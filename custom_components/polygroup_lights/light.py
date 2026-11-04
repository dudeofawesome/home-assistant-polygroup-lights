"""Stateful light effects and optional calibrated brightness."""

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DIMMABLE_EFFECTS, EFFECTS
from .entity import PolygroupEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([PolygroupLight(entry)])
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "synchronize_state",
        {
            vol.Required("power"): bool,
            vol.Optional("effect"): vol.In(EFFECTS),
            vol.Optional("brightness_index"): vol.All(
                vol.Coerce(int), vol.Range(min=0)
            ),
        },
        "async_synchronize_state",
    )


class PolygroupLight(PolygroupEntity, RestoreEntity, LightEntity):
    """Restore assumed state and update it after successful transmissions."""

    _attr_name = None
    _attr_icon = "mdi:pine-tree"
    _attr_assumed_state = True
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(EFFECTS.values())

    def __init__(self, entry):
        super().__init__(entry, "light")
        self.adapters = self.controller.adapter_entities
        mode = ColorMode.BRIGHTNESS if self.controller.levels else ColorMode.ONOFF
        self._attr_color_mode = mode
        self._attr_supported_color_modes = {mode}

    @property
    def is_on(self):
        return self.controller.state.power

    @property
    def effect(self):
        return EFFECTS.get(self.controller.state.effect)

    @property
    def brightness(self):
        index = self.controller.state.brightness_index
        if index is None or not self.controller.levels:
            return None
        return round(self.controller.levels[index] * 255 / 100)

    @property
    def extra_state_attributes(self):
        c = self.controller
        return {
            "last_command": c.state.last_command,
            "effect_key": c.state.effect,
            "brightness_index": c.state.brightness_index,
            "brightness_levels": c.levels,
            "available_commands": sorted(c.codes),
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            state = self.controller.state
            if state.power is None and last.state in (STATE_ON, STATE_OFF):
                state.power = last.state == STATE_ON
            if state.effect is None:
                effect_key = last.attributes.get("effect_key")
                if effect_key in EFFECTS:
                    state.effect = effect_key
                else:
                    state.effect = next(
                        (
                            key
                            for key, value in EFFECTS.items()
                            if value == last.attributes.get(ATTR_EFFECT)
                        ),
                        None,
                    )
            state.last_command = last.attributes.get("last_command")
            index = last.attributes.get("brightness_index")
            if (
                last.attributes.get("brightness_levels") == self.controller.levels
                and isinstance(index, int)
                and 0 <= index < len(self.controller.levels)
            ):
                state.brightness_index = index

    async def async_turn_on(self, **kwargs: Any):
        c = self.controller
        async with c.lock:
            effect = next(
                (
                    key
                    for key, label in EFFECTS.items()
                    if label == kwargs.get(ATTR_EFFECT)
                ),
                None,
            )
            if ATTR_EFFECT in kwargs and effect is None:
                raise HomeAssistantError("Unknown lighting effect")
            if c.state.power is None:
                raise HomeAssistantError(
                    "Synchronize the tree's current power state first"
                )
            needed = (["power"] if not c.state.power else []) + (
                [effect] if effect else []
            )
            target_index = None
            if ATTR_BRIGHTNESS in kwargs:
                if not c.levels or c.state.brightness_index is None:
                    raise HomeAssistantError(
                        "Calibrate and synchronize brightness first"
                    )
                if (effect or c.state.effect) not in DIMMABLE_EFFECTS:
                    raise HomeAssistantError(
                        "Brightness is supported for Clear Steady, Color Steady, and Clear/Color Alt"
                    )
                target_index = min(
                    range(len(c.levels)),
                    key=lambda i: abs(
                        c.levels[i] * 255 / 100 - kwargs[ATTR_BRIGHTNESS]
                    ),
                )
                if target_index != c.state.brightness_index:
                    needed.append("brightness")
            for command in needed:
                if command not in c.codes:
                    raise HomeAssistantError(
                        f"No verified RF code is available for {command}"
                    )
            if not c.state.power:
                await c.send("power", self._context)
            if effect:
                await c.send(effect, self._context)
            if target_index is not None:
                if c.state.brightness_index is None or not c.state.power:
                    raise HomeAssistantError(
                        "State changed during transmission; synchronize brightness again"
                    )
                steps = (target_index - c.state.brightness_index) % len(c.levels)
                for step in range(steps):
                    if not c.state.power or c.state.effect not in DIMMABLE_EFFECTS:
                        raise HomeAssistantError(
                            "State changed during brightness adjustment"
                        )
                    if step:
                        await asyncio.sleep(0.25)
                    await c.send("brightness", self._context)

    async def async_turn_off(self, **kwargs: Any):
        c = self.controller
        async with c.lock:
            if c.state.power is None:
                raise HomeAssistantError(
                    "Synchronize the tree's current power state first"
                )
            if c.state.power:
                await c.send("power", self._context)

    async def async_synchronize_state(
        self, power: bool, effect=None, brightness_index=None
    ):
        """Record observed state without transmitting anything."""
        c = self.controller
        async with c.lock:
            if brightness_index is not None and brightness_index >= len(c.levels):
                raise HomeAssistantError(
                    "Brightness index is outside the configured cycle"
                )
            c.state.power = power
            if effect is not None:
                c.state.effect = effect
            if brightness_index is not None:
                c.state.brightness_index = brightness_index
            c.notify()
