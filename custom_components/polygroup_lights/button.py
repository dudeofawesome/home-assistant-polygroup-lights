"""Brightness cycling and replay tests for captured remote buttons."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .commands import CAPTURED_CODES
from .const import EFFECTS
from .entity import PolygroupEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [PolygroupBrightnessButton(entry)]
        + [PolygroupCaptureTestButton(entry, command) for command in CAPTURED_CODES]
    )


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


class PolygroupCaptureTestButton(PolygroupEntity, ButtonEntity):
    """Test a captured code before it becomes a verified default."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:remote"

    def __init__(self, entry, command):
        super().__init__(entry, f"test_captured_{command}")
        self.command = command
        label = {**EFFECTS, "brightness": "Brightness", "power": "On/Off"}[command]
        self._attr_name = f"Test captured {label}"
        self.adapters = self.controller.adapter_entities

    async def async_press(self):
        async with self.controller.lock:
            await self.controller.send_captured(self.command, self._context)
