"""Optional remote command events; reception belongs to the controller."""

from homeassistant.components.event import EventEntity
from homeassistant.core import callback

from .const import COMMANDS, CONF_RECEIVER
from .entity import PolygroupEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([PolygroupRemoteEvent(entry)])


class PolygroupRemoteEvent(PolygroupEntity, EventEntity):
    """Receive native RF frames and publish one event per button burst."""

    _attr_name = "Remote command"
    _attr_event_types = [*COMMANDS, "unlearned"]

    def __init__(self, entry):
        super().__init__(entry, "remote_command")
        self.receiver = entry.data[CONF_RECEIVER]

    @property
    def available(self):
        state = self.hass.states.get(self.receiver)
        return state is not None and state.state != "unavailable"

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.controller.event_callback = self.received
        self.async_on_remove(self.cleanup)

    @callback
    def cleanup(self):
        self.controller.event_callback = None

    @callback
    def received(self, command, code):
        self._trigger_event(command, {"code": f"{code:08X}"})
        self.async_write_ha_state()
