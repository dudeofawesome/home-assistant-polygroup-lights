"""Uncalibrated brightness can still be cycled like the remote."""

from homeassistant.components.button import ButtonEntity

from .entity import PolygroupEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([PolygroupBrightnessButton(entry)])


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
