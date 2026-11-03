"""Shared command transmission, learning, and remote state updates."""

import asyncio
from collections.abc import Callable
from time import monotonic
from typing import Any

from homeassistant.components import radio_frequency as rf
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .commands import PolygroupCommand, decode_frames
from .const import (
    COMMANDS,
    CONF_BRIGHTNESS_LEVELS,
    CONF_CODES,
    CONF_RECEIVER,
    CONF_TRANSMITTER,
    FREQUENCY,
)
from .state import BurstFilter, TreeState


class TreeController:
    """One state source for all entities and all command origins."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.options = dict(entry.options)
        self.codes: dict[str, int] = dict(entry.data.get(CONF_CODES, {}))
        self.levels: list[int] = entry.options.get(CONF_BRIGHTNESS_LEVELS, [])
        self.state = TreeState()
        self.bursts = BurstFilter()
        self.lock = asyncio.Lock()
        self.listeners: set[Callable[[], None]] = set()
        self.event_callback: Callable[[str, int], None] | None = None
        self.learning: str | None = None
        self.learning_until = 0.0
        self.cancel_learning = None
        self.unsubscribe_receiver = None

    @callback
    def start_receiving(self) -> None:
        """Track RF reception independently of whether any entity is enabled."""
        self.entry.async_on_unload(
            async_track_state_change_event(
                self.hass,
                [self.entry.data[CONF_RECEIVER]],
                self.receiver_changed,
            )
        )
        self.entry.async_on_unload(self.stop_receiving)
        self.receiver_changed(None)

    @callback
    def stop_receiving(self) -> None:
        if self.unsubscribe_receiver is not None:
            self.unsubscribe_receiver()
            self.unsubscribe_receiver = None

    @callback
    def receiver_changed(self, _event) -> None:
        state = self.hass.states.get(self.entry.data[CONF_RECEIVER])
        available = state is not None and state.state != "unavailable"
        if not available:
            self.stop_receiving()
            self.state.power = None
            self.state.effect = None
            self.state.brightness_index = None
        elif self.unsubscribe_receiver is None:
            self.unsubscribe_receiver = rf.async_subscribe_receiver(
                self.hass,
                self.entry.data[CONF_RECEIVER],
                self.receive,
            )
        self.notify()

    @callback
    def notify(self) -> None:
        """Notify all stateful controls."""
        for listener in tuple(self.listeners):
            listener()

    @callback
    def receive(self, signal: Any) -> None:
        """Decode only matching frequency/modulation and complete frames."""
        if (
            signal.frequency not in (None, FREQUENCY)
            or signal.modulation != rf.ModulationType.OOK
        ):
            return
        for code in decode_frames(signal.timings):
            now = monotonic()
            if not self.bursts.accept(code, now):
                continue
            if self.learning is not None and now < self.learning_until:
                command = self.learning
                if any(
                    value == code and key != command
                    for key, value in self.codes.items()
                ):
                    # Never create ambiguous bindings from an accidental press.
                    continue
                self.codes[command] = code
                self.learning = None
                if self.cancel_learning:
                    self.cancel_learning()
                    self.cancel_learning = None
                self.hass.config_entries.async_update_entry(
                    self.entry, data={**self.entry.data, CONF_CODES: self.codes.copy()}
                )
            else:
                self.learning = None
                command = next(
                    (key for key, value in self.codes.items() if value == code), None
                )
            if command is not None:
                self.state.apply(command, self.levels)
                self.notify()
            if self.event_callback is not None:
                self.event_callback(command or "unlearned", code)

    def learn(self, command: str) -> None:
        """Arm learning for 30 seconds without blocking a service call."""
        if command not in COMMANDS:
            raise HomeAssistantError("Unknown remote button")
        self.learning = command
        self.learning_until = monotonic() + 30
        if self.cancel_learning:
            self.cancel_learning()
        self.cancel_learning = async_call_later(self.hass, 30, self.finish_learning)
        self.entry.async_on_unload(self.cancel_learning)
        self.notify()

    @callback
    def finish_learning(self, _now) -> None:
        """Clear the learning indicator when no button was captured."""
        self.learning = None
        if self.cancel_learning:
            self.cancel_learning()
        self.cancel_learning = None
        self.notify()

    async def send(self, command: str, context: Any = None) -> None:
        """Send under the caller's lock; commit state only after success."""
        if command not in self.codes:
            raise HomeAssistantError(
                f"Learn the {command} button first using polygroup_lights.learn_command"
            )
        code = self.codes[command]
        self.bursts.echo_code = code
        self.bursts.echo_until = monotonic() + 2
        try:
            await rf.async_send_command(
                self.hass,
                self.entry.data[CONF_TRANSMITTER],
                PolygroupCommand(code),
                context=context,
            )
        except Exception:
            self.bursts.echo_until = float("-inf")
            raise
        self.bursts.echo_until = monotonic() + 0.3
        self.state.apply(command, self.levels)
        self.notify()
