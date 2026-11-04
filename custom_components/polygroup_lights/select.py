"""Select a verified lighting effect using the shared assumed state."""

from homeassistant.components.select import SelectEntity

from .commands import VERIFIED_CODES
from .const import EFFECTS
from .entity import PolygroupEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([PolygroupEffectSelect(entry)])


class PolygroupEffectSelect(PolygroupEntity, SelectEntity):
    """Send an effect command without changing assumed power."""

    _attr_name = "Effect"
    _attr_icon = "mdi:pine-tree"
    _attr_assumed_state = True

    def __init__(self, entry):
        super().__init__(entry, "effect")
        self.adapters = self.controller.adapter_entities
        self.commands = {
            label: command
            for command, label in EFFECTS.items()
            if command in VERIFIED_CODES
        }
        self._attr_options = list(self.commands)

    @property
    def current_option(self) -> str | None:
        effect = EFFECTS.get(self.controller.state.effect)
        return effect if effect in self.commands else None

    async def async_select_option(self, option: str) -> None:
        async with self.controller.lock:
            await self.controller.send(self.commands[option], self._context)
