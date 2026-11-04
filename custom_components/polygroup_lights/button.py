"""Remote button controls and manual power-state synchronization."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .commands import VERIFIED_CODES
from .const import EFFECTS
from .entity import PolygroupEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [PolygroupBrightnessButton(entry)]
        + [PolygroupCommandButton(entry, command) for command in VERIFIED_CODES]
        + [PolygroupPowerStateButton(entry, power) for power in (True, False)]
    )


class PolygroupPowerStateButton(PolygroupEntity, ButtonEntity):
    """Record the tree's observed power state without sending a command."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, power: bool):
        state = "on" if power else "off"
        super().__init__(entry, f"record_power_{state}")
        self.power = power
        self._attr_name = f"Record tree as {state}"
        self._attr_icon = f"mdi:lightbulb-{state}-outline"

    @property
    def available(self) -> bool:
        """Recording an observation does not require an RF transmitter."""
        return True

    async def async_press(self):
        await self.controller.async_synchronize_state(self.power)


class PolygroupBrightnessButton(PolygroupEntity, ButtonEntity):
    """Cycle brightness without inventing a percentage."""

    _attr_name = "Cycle brightness"
    _attr_icon = "mdi:brightness-6"

    def __init__(self, entry):
        super().__init__(entry, "cycle_brightness")
        self.adapters = self.controller.adapter_entities

    async def async_press(self):
        async with self.controller.lock:
            await self.controller.send("brightness", self._context)


class PolygroupCommandButton(PolygroupEntity, ButtonEntity):
    """Send one verified remote button command."""

    _attr_icon = "mdi:remote"

    def __init__(self, entry, command):
        # Keep the original unique ID so existing entity references survive.
        super().__init__(entry, f"test_captured_{command}")
        self.command = command
        label = {**EFFECTS, "brightness": "Brightness", "power": "On/Off"}[command]
        self._attr_name = label
        self.adapters = self.controller.adapter_entities

    async def async_press(self):
        async with self.controller.lock:
            await self.controller.send(self.command, self._context)
