"""Polygroup Christmas tree RF control."""

from homeassistant.components import radio_frequency as rf
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .coordinator import TreeController

PLATFORMS = [Platform.LIGHT, Platform.BUTTON, Platform.EVENT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one shared receiver and state model for this tree."""
    if not hasattr(rf, "async_subscribe_receiver"):
        raise ConfigEntryError(
            "This Home Assistant version lacks native RF receiver support"
        )
    entry.runtime_data = TreeController(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.runtime_data.start_receiving()
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload configuration changes, but keep learning updates in memory."""
    if entry.runtime_data.options != dict(entry.options):
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload platforms and their receiver subscriptions."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
