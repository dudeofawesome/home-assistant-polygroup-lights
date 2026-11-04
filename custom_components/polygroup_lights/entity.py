"""Shared device identity and state notifications."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN


class PolygroupEntity(Entity):
    """An entity belonging to a Polygroup tree controller."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        self.controller = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Polygroup",
            model="PDR-053-29V / PDT-015-14 (053/056)",
        )

    @property
    def available(self) -> bool:
        return all(
            (state := self.hass.states.get(adapter)) is not None
            and state.state != "unavailable"
            for adapter in self.controller.adapter_entities
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.controller.listeners.add(self.async_write_ha_state)
        self.async_on_remove(
            lambda: self.controller.listeners.discard(self.async_write_ha_state)
        )
        if adapters := getattr(self, "adapters", None):
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    adapters,
                    self.adapter_changed,
                )
            )

    @callback
    def adapter_changed(self, event):
        """Refresh availability from the HA event loop."""
        self.async_write_ha_state()
