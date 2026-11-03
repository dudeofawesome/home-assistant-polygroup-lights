"""Uncalibrated brightness can still be cycled like the remote."""

from homeassistant.components.button import ButtonEntity

from .const import CONF_RECEIVER, CONF_TRANSMITTER
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
        self.adapters = [entry.data[CONF_TRANSMITTER], entry.data[CONF_RECEIVER]]

    @property
    def available(self):
        return all(
            (state := self.hass.states.get(adapter)) is not None
            and state.state != "unavailable"
            for adapter in self.adapters
        )

    async def async_press(self):
        async with self.controller.lock:
            await self.controller.send("brightness", self._context)
