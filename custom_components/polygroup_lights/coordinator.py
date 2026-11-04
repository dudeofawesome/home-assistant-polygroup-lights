"""Command transport and shared assumed state, independent of RF reception."""

import asyncio
from collections.abc import Callable
from typing import Any

from homeassistant.components import radio_frequency as rf
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .commands import VERIFIED_CODES, PolygroupCommand
from .const import COMMANDS, CONF_BRIGHTNESS_LEVELS, CONF_CODES, CONF_TRANSMITTER
from .state import TreeState


class TreeController:
    """Keep transport, command bindings, and state transitions separate.

    Future official RF reception can decode and deduplicate signals, then call
    apply_command(). It must not call send(), which would retransmit a press.
    No receiver subscription or hardware-specific API belongs in this class.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.options = dict(entry.options)
        self.codes: dict[str, int] = {
            **VERIFIED_CODES,
            **entry.data.get(CONF_CODES, {}),
        }
        self.levels: list[int] = entry.options.get(CONF_BRIGHTNESS_LEVELS, [])
        self.state = TreeState()
        self.lock = asyncio.Lock()
        self.listeners: set[Callable[[], None]] = set()

    @property
    def adapter_entities(self) -> list[str]:
        return [self.entry.data[CONF_TRANSMITTER]]

    @callback
    def notify(self) -> None:
        for listener in tuple(self.listeners):
            listener()

    @callback
    def apply_command(self, command: str) -> None:
        """Commit one logical command without transmitting any RF signal."""
        if command not in COMMANDS:
            raise HomeAssistantError("Unknown remote button")
        self.state.apply(command, self.levels)
        self.notify()

    async def send(self, command: str, context: Any = None) -> None:
        """Send under the caller's lock; commit state only after success."""
        if command not in self.codes:
            raise HomeAssistantError(f"No verified RF code is available for {command}")
        await rf.async_send_command(
            self.hass,
            self.entry.data[CONF_TRANSMITTER],
            PolygroupCommand(self.codes[command]),
            context=context,
        )
        self.apply_command(command)
