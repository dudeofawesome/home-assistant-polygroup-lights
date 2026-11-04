"""Raw waveform encoding; deliberately does not assume NEC compatibility."""

from collections.abc import Sequence

from rf_protocols import ModulationType, RadioFrequencyCommand

from .const import FREQUENCY

# Populate only with hardware-verified codes for the supported controller/model.
# The handoff's On/Off candidate has not been verified for transmission.
VERIFIED_CODES: dict[str, int] = {}

# Captured from physical remote presses; tree acceptance of replay is unverified.
CAPTURED_CODES: dict[str, int] = {
    "combo": 0x807F7788,
    "clear_steady": 0x807F6699,
    "color_steady": 0x807F55AA,
    "clear_twinkle": 0x807FEE11,
    "brightness": 0x807F11EE,
    "power": 0x807FFF00,
}


def encode_frame(code: int) -> list[int]:
    """Encode the measured 32-bit pulse-distance frame, MSB first."""
    if not 0 <= code <= 0xFFFFFFFF:
        raise ValueError("Expected a 32-bit code")
    timings = [9000, -5350]
    for shift in range(31, -1, -1):
        timings.extend((900, -1600 if code & (1 << shift) else -540))
    return [*timings, 900, -9000]


def decode_frames(timings: Sequence[int]) -> list[int]:
    """Find complete frames amid noise, preambles, and concatenated repeats."""

    def near(value: int, expected: int) -> bool:
        return abs(value - expected) <= abs(expected) * 0.25

    frames = []
    index = 0
    while index + 66 < len(timings):
        if not (near(timings[index], 9000) and near(timings[index + 1], -5350)):
            index += 1
            continue
        code = 0
        for bit in range(32):
            mark, space = timings[index + 2 + bit * 2 : index + 4 + bit * 2]
            if not near(mark, 900):
                break
            if near(space, -540):
                value = 0
            elif near(space, -1600):
                value = 1
            else:
                break
            code = (code << 1) | value
        else:
            if near(timings[index + 66], 900):
                frames.append(code)
                index += 67
                continue
        index += 1
    return frames


class PolygroupCommand(RadioFrequencyCommand):
    """Send one captured Polygroup code using its measured timings."""

    def __init__(self, code: int) -> None:
        super().__init__(
            frequency=FREQUENCY, modulation=ModulationType.OOK, repeat_count=3
        )
        self.code = code

    def get_raw_timings(self) -> list[int]:
        """Return a frame including the gap between repeats."""
        return encode_frame(self.code)
