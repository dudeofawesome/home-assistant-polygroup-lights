"""Event platform for the TOTO Washlet integration."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.event import EventEntity
from homeassistant.components.infrared import (
    InfraredReceivedSignal,
    InfraredReceiverConsumerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .commands import (
    TotoData,
    TotoWashletCode,
    decode_toto_frames,
    format_toto_frames,
)
from .const import CONF_INFRARED_RECEIVER_ENTITY_ID, received_command_signal
from .entity import TotoWashletEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0
_COMMAND_BURST_SETTLE_DELAY = 0.15

_COMMAND_CODE_TO_EVENT_TYPE: dict[TotoWashletCode, str] = {
    code: code.name.lower() for code in TotoWashletCode
}
_EVENT_TYPE_UNKNOWN = "unknown"
_EVENT_TYPES = [*_COMMAND_CODE_TO_EVENT_TYPE.values(), _EVENT_TYPE_UNKNOWN]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TOTO Washlet event entity from a config entry."""
    if not (
        receiver_entity_id := entry.options.get(
            CONF_INFRARED_RECEIVER_ENTITY_ID,
            entry.data.get(CONF_INFRARED_RECEIVER_ENTITY_ID),
        )
    ):
        return

    async_add_entities([TotoWashletReceivedCommandEvent(entry, receiver_entity_id)])


class TotoWashletReceivedCommandEvent(
    TotoWashletEntity, InfraredReceiverConsumerEntity, EventEntity
):
    """Event entity that fires when a TOTO Washlet IR command is received."""

    _attr_translation_key = "received_command"
    _attr_event_types = _EVENT_TYPES

    def __init__(self, entry: ConfigEntry, receiver_entity_id: str) -> None:
        """Initialize the event entity."""
        super().__init__(entry, unique_id_suffix="received_command")
        self._entry_id = entry.entry_id
        self._infrared_receiver_entity_id = receiver_entity_id
        self._pending_frames: list[TotoData] = []
        self._pending_signal_count = 0
        self._pending_timing_count = 0
        self._cancel_pending_event: CALLBACK_TYPE | None = None

    async def async_will_remove_from_hass(self) -> None:
        """Cancel a pending command event when the entity is removed."""
        if self._cancel_pending_event is not None:
            self._cancel_pending_event()
            self._cancel_pending_event = None
        await super().async_will_remove_from_hass()

    @callback
    def _handle_signal(self, signal: InfraredReceivedSignal) -> None:
        """Handle a received IR signal."""
        frames = decode_toto_frames(signal.timings)
        self._pending_signal_count += 1
        self._pending_timing_count += len(signal.timings)
        if frames:
            for frame in frames:
                if not self._pending_frames or self._pending_frames[-1] != frame:
                    self._pending_frames.append(frame)

        if self._cancel_pending_event is not None:
            self._cancel_pending_event()
        self._cancel_pending_event = async_call_later(
            self.hass,
            _COMMAND_BURST_SETTLE_DELAY,
            self._flush_pending_event,
        )

    @callback
    def _flush_pending_event(self, _now: datetime) -> None:
        """Fire one event after all repeated frames for a command arrive."""
        self._cancel_pending_event = None
        frames = self._pending_frames
        signal_count = self._pending_signal_count
        timing_count = self._pending_timing_count
        self._pending_frames = []
        self._pending_signal_count = 0
        self._pending_timing_count = 0

        command_code = TotoWashletCode.from_frames(frames) if frames else None
        if command_code is None:
            event_type = _EVENT_TYPE_UNKNOWN
        else:
            event_type = _COMMAND_CODE_TO_EVENT_TYPE[command_code]
            async_dispatcher_send(
                self.hass,
                received_command_signal(self._entry_id),
                command_code,
            )

        if frames:
            _LOGGER.debug(
                "Received TOTO Washlet IR command: event_type=%s, "
                "signal_count=%s, frames=%s",
                event_type,
                signal_count,
                format_toto_frames(frames),
            )
        else:
            _LOGGER.debug(
                "Received undecodable TOTO Washlet IR signal: timing_count=%s, "
                "signal_count=%s",
                timing_count,
                signal_count,
            )
        self._trigger_event(event_type)
        self.async_write_ha_state()
