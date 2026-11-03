"""Common entity for TOTO Washlet integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class TotoWashletEntity(Entity):
    """TOTO Washlet base entity."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, unique_id_suffix: str) -> None:
        """Initialize TOTO Washlet entity."""
        self._attr_unique_id = f"{entry.entry_id}_{unique_id_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TOTO Washlet",
            manufacturer="TOTO",
        )
