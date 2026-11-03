# TODO: this should be part of https://github.com/home-assistant-libs/infrared-protocols

"""TOTO Washlet infrared commands."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import override

from infrared_protocols.commands import Command as InfraredCommand

PREAMBLE_HIGH = 6200
PREAMBLE_LOW = 2800
BIT_HIGH = 550
BIT_ONE_LOW = 1700
BIT_ZERO_LOW = 550
FRAME_GAP = 36000
MODULATION = 38000
TOTO_HEADER = 0x2008
TOTO_HEADER_BITS = 15
TOTO_PAYLOAD_BITS = 24
TOLERANCE = 0.35


@dataclass(frozen=True)
class TotoData:
    """TOTO infrared command data."""

    command: int
    rc_code_1: int = 0
    rc_code_2: int = 0

    @property
    def payload(self) -> int:
        """Return the 24-bit TOTO payload."""
        payload = self.rc_code_1 << 20
        payload |= self.rc_code_2 << 16
        payload |= self.command << 8
        payload |= ((payload & 0xFF0000) >> 16) ^ ((payload & 0x00FF00) >> 8)
        return payload


class TotoWashletCode(Enum):
    """TOTO Washlet IR command codes."""

    STOP = (TotoData(0xDA, 0xA, 0xA), TotoData(0x00))
    REAR = (TotoData(0x80, 0x2, 0xC),)
    SOFT_REAR = (TotoData(0xA8, 0x2, 0xC),)
    FRONT = (TotoData(0x40, 0x2, 0xC),)
    SOFT_FRONT = (TotoData(0x91, 0x2, 0xC),)
    USER_PROFILE_1 = (
        TotoData(0xD5),
        TotoData(0x95, 0x2, 0x8),
        TotoData(0x55, 0xD),
    )
    USER_PROFILE_2 = (
        TotoData(0xD5, 0x4),
        TotoData(0x95, 0x4, 0xC),
        TotoData(0x55, 0xD),
    )
    USER_PROFILE_3 = (
        TotoData(0xD5, 0xC),
        TotoData(0x95, 0x2, 0xC),
        TotoData(0x55, 0x1),
    )
    USER_PROFILE_4 = (
        TotoData(0xD5, 0x2),
        TotoData(0x95, 0x2, 0xC),
        TotoData(0x55, 0x1),
    )
    OSCILLATE = (TotoData(0x60), TotoData(0x10))
    PULSATE = (TotoData(0xE0),)
    LID_OPEN_CLOSE = (TotoData(0x0E),)
    SEAT_OPEN_CLOSE = (TotoData(0xF6),)
    FULL_FLUSH = (TotoData(0xB0),)
    LIGHT_FLUSH = (TotoData(0x88),)
    ECO_FLUSH = (TotoData(0xB6),)
    BOWL_LIGHT_ON = (TotoData(0x39, 0x4),)
    BOWL_LIGHT_OFF = (TotoData(0x39, 0x8),)
    BEEP_SOUND_ON = (TotoData(0xCC, 0x4),)
    BEEP_SOUND_OFF = (TotoData(0xCC, 0x8),)
    DRYER = (TotoData(0xC0),)
    POWER_DEODORIZER = (TotoData(0x7C),)
    WAND_CLEAN = (TotoData(0x11),)
    MANUAL_NOZZLE_CLEANING = (TotoData(0x74),)
    MANUAL_PREMIST = (TotoData(0x59),)
    LOWER_WATER = (TotoData(0x12),)
    NOZZLE_POSITION_1 = (TotoData(0xA0, 0x0, 0x8),)
    NOZZLE_POSITION_2 = (TotoData(0xA0, 0x0, 0x4),)
    NOZZLE_POSITION_3 = (TotoData(0xA0, 0x0, 0xC),)
    NOZZLE_POSITION_4 = (TotoData(0xA0, 0x0, 0x2),)
    NOZZLE_POSITION_5 = (TotoData(0xA0, 0x0, 0xA),)
    PRESSURE_LEVEL_1 = (TotoData(0x20, 0x4),)
    PRESSURE_LEVEL_2 = (TotoData(0x20, 0xC),)
    PRESSURE_LEVEL_3 = (TotoData(0x20, 0x2),)
    PRESSURE_LEVEL_4 = (TotoData(0x20, 0xA),)
    PRESSURE_LEVEL_5 = (TotoData(0x20, 0x6),)
    TEMPERATURE_OFF = (TotoData(0xEC),)
    WATER_TEMPERATURE_1 = (TotoData(0xEC, 0x8),)
    WATER_TEMPERATURE_2 = (TotoData(0xEC, 0xA),)
    WATER_TEMPERATURE_3 = (TotoData(0xEC, 0x1),)
    WATER_TEMPERATURE_4 = (TotoData(0xEC, 0x9),)
    WATER_TEMPERATURE_5 = (TotoData(0xEC, 0xD),)
    DRYER_AIR_TEMPERATURE_1 = (TotoData(0x1C, 0x8),)
    DRYER_AIR_TEMPERATURE_2 = (TotoData(0x1C, 0x4),)
    DRYER_AIR_TEMPERATURE_3 = (TotoData(0x1C, 0xC),)
    DRYER_AIR_TEMPERATURE_4 = (TotoData(0x1C, 0x2),)
    DRYER_AIR_TEMPERATURE_5 = (TotoData(0x1C, 0xA),)
    SEAT_TEMPERATURE_1 = (TotoData(0xEC, 0x0, 0x8),)
    SEAT_TEMPERATURE_2 = (TotoData(0xEC, 0x0, 0xA),)
    SEAT_TEMPERATURE_3 = (TotoData(0xEC, 0x0, 0x1),)
    SEAT_TEMPERATURE_4 = (TotoData(0xEC, 0x0, 0x9),)
    SEAT_TEMPERATURE_5 = (TotoData(0xEC, 0x0, 0xD),)
    AUTO_ENERGY_SAVER = (TotoData(0x34),)
    AUTO_ENERGY_SAVER_PLUS = (TotoData(0x2A),)
    AUTO_ENERGY_SAVER_OFF = (TotoData(0xB4),)
    TIMER_ENERGY_SAVER_6 = (TotoData(0x68, 0x6),)
    TIMER_ENERGY_SAVER_OFF = (TotoData(0x68),)
    AUTO_LID_OPEN_OFF = (TotoData(0x5C),)
    AUTO_LID_OPEN_ON = (TotoData(0x9C),)
    AUTO_FLUSH_OFF = (TotoData(0x3C),)
    AUTO_FLUSH_ON = (TotoData(0xDC),)
    CLOSE_LID_BEFORE_FLUSHING_ON = (TotoData(0x66, 0x4),)
    CLOSE_LID_BEFORE_FLUSHING_OFF = (TotoData(0x66, 0x8),)
    MYSTERY = (TotoData(0x3D),)

    def to_command(self) -> TotoCommand:
        """Build a TOTO command for this Washlet code."""
        return TotoCommand(self.value)

    @classmethod
    def from_raw_timings(cls, timings: list[int]) -> TotoWashletCode | None:
        """Decode raw IR timings into a known TOTO Washlet code."""
        frames = decode_toto_frames(timings)
        if not frames:
            return None

        return cls.from_frames(frames)

    @classmethod
    def from_frames(cls, frames: Iterable[TotoData]) -> TotoWashletCode | None:
        """Return the known TOTO Washlet code matching decoded frames."""
        frames = tuple(frames)
        for code in cls:
            if frames == code.value:
                return code

        if len(frames) == 1:
            for code in cls:
                if frames[0] == code.value[0] and len(code.value) == 1:
                    return code

            command_matches = [
                code
                for code in cls
                if len(code.value) == 1 and frames[0].command == code.value[0].command
            ]
            if len(command_matches) == 1:
                return command_matches[0]

            matches = [
                code
                for code in cls
                if len(code.value) > 1 and frames[0] == code.value[0]
            ]
            if len(matches) == 1:
                return matches[0]

        return None


class TotoCommand(InfraredCommand):
    """TOTO infrared command."""

    def __init__(
        self,
        frames: Iterable[TotoData],
        *,
        modulation: int = MODULATION,
        repeat_count: int = 2,
    ) -> None:
        """Initialize the TOTO IR command."""
        super().__init__(modulation=modulation, repeat_count=repeat_count)
        self.frames = tuple(frames)

    @override
    def get_raw_timings(self) -> list[int]:
        """Get raw timings for the TOTO command."""
        timings: list[int] = []
        for frame_index, frame in enumerate(self.frames):
            if frame_index:
                timings.append(-FRAME_GAP)
            for repeat_index in range(self.repeat_count + 1):
                if repeat_index:
                    timings.append(-FRAME_GAP)
                timings.extend(_encode_frame(frame))
        return timings


def _encode_frame(frame: TotoData) -> list[int]:
    """Encode one TOTO frame."""
    timings = [PREAMBLE_HIGH, -PREAMBLE_LOW]
    _append_bits(timings, TOTO_HEADER, TOTO_HEADER_BITS)
    _append_bits(timings, frame.payload, TOTO_PAYLOAD_BITS)
    timings.append(BIT_HIGH)
    return timings


def _append_bits(timings: list[int], value: int, bit_count: int) -> None:
    """Append MSB-first TOTO bits to timings."""
    for bit in range(bit_count - 1, -1, -1):
        timings.append(BIT_HIGH)
        timings.append(-BIT_ONE_LOW if value & (1 << bit) else -BIT_ZERO_LOW)


def decode_toto_frames(timings: list[int]) -> list[TotoData] | None:
    """Decode raw timings into de-duplicated TOTO frames."""
    frames: list[TotoData] = []
    index = 0
    while index < len(timings):
        frame = _decode_frame_at(timings, index)
        if frame is None:
            index += 1
            continue

        if not frames or frames[-1] != frame:
            frames.append(frame)
        index += _encoded_frame_length()

    return frames or None


def format_toto_frames(frames: Iterable[TotoData]) -> str:
    """Format TOTO frames for diagnostic logs."""
    return ", ".join(
        f"0x{frame.rc_code_1:X} / 0x{frame.rc_code_2:X} / 0x{frame.command:02X}"
        for frame in frames
    )


def _decode_frame_at(timings: list[int], index: int) -> TotoData | None:
    """Decode a single TOTO frame starting at an index."""
    if index + _encoded_frame_length() > len(timings):
        return None

    if not _matches_mark(timings[index], PREAMBLE_HIGH) or not _matches_space(
        timings[index + 1], PREAMBLE_LOW
    ):
        return None

    index += 2
    header = _decode_bits(timings, index, TOTO_HEADER_BITS)
    if header != TOTO_HEADER:
        return None

    index += TOTO_HEADER_BITS * 2
    payload = _decode_bits(timings, index, TOTO_PAYLOAD_BITS)
    if payload is None:
        return None

    checksum = payload & 0xFF
    expected_checksum = ((payload & 0xFF0000) >> 16) ^ ((payload & 0x00FF00) >> 8)
    if checksum != expected_checksum:
        return None

    return TotoData(
        command=(payload >> 8) & 0xFF,
        rc_code_1=(payload >> 20) & 0xF,
        rc_code_2=(payload >> 16) & 0xF,
    )


def _decode_bits(timings: list[int], index: int, bit_count: int) -> int | None:
    """Decode MSB-first TOTO bits."""
    value = 0
    for _ in range(bit_count):
        if not _matches_mark(timings[index], BIT_HIGH):
            return None

        space = timings[index + 1]
        if _matches_space(space, BIT_ONE_LOW):
            value = (value << 1) | 1
        elif _matches_space(space, BIT_ZERO_LOW):
            value <<= 1
        else:
            return None

        index += 2

    return value


def _matches_mark(value: int, expected: int) -> bool:
    """Return whether a timing matches an IR mark."""
    return value > 0 and _matches_duration(value, expected)


def _matches_space(value: int, expected: int) -> bool:
    """Return whether a timing matches an IR space."""
    return value < 0 and _matches_duration(abs(value), expected)


def _matches_duration(value: int, expected: int) -> bool:
    """Return whether a timing is within protocol tolerance."""
    return abs(value - expected) <= expected * TOLERANCE


def _encoded_frame_length() -> int:
    """Return the number of timings in one encoded TOTO frame."""
    return 2 + (TOTO_HEADER_BITS + TOTO_PAYLOAD_BITS) * 2 + 1
