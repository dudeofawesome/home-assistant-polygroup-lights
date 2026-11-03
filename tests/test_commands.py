"""Exercise real captured timings, malformed frames, and repeated packets."""

import pytest

from custom_components.polygroup_lights.commands import (
    PolygroupCommand,
    decode_frames,
    encode_frame,
)

CAPTURE = [
    8984,
    -5345,
    908,
    -1590,
    914,
    -523,
    923,
    -517,
    925,
    -514,
    908,
    -535,
    915,
    -545,
    894,
    -534,
    910,
    -544,
    892,
    -545,
    893,
    -1615,
    890,
    -1616,
    891,
    -1592,
    912,
    -1592,
    890,
    -1618,
    910,
    -1597,
    891,
    -1601,
    919,
    -1591,
    910,
    -1599,
    901,
    -1592,
    892,
    -1600,
    920,
    -1597,
    897,
    -1609,
    881,
    -1607,
    906,
    -1625,
    877,
    -545,
    911,
    -525,
    915,
    -536,
    884,
    -542,
    911,
    -541,
    892,
    -546,
    898,
    -546,
    908,
    -519,
    913,
    -8988,
]


def test_capture_and_noisy_bursts():
    assert decode_frames(CAPTURE) == [0x807FFF00]
    assert decode_frames([1000, -1000, *CAPTURE, *CAPTURE]) == [0x807FFF00] * 2
    assert decode_frames(CAPTURE[:-2]) == []
    damaged = CAPTURE.copy()
    damaged[8] = 100
    assert decode_frames([*damaged, *CAPTURE]) == [0x807FFF00]
    assert decode_frames([-value for value in CAPTURE]) == []


@pytest.mark.parametrize("code", [0, 0xFFFFFFFF, 0x807FFF00, 0x12345678])
def test_raw_encoding(code):
    command = PolygroupCommand(code)
    assert command.frequency == 433_895_000
    assert command.repeat_count == 3
    assert decode_frames(command.get_raw_timings()) == [code]


def test_invalid_code():
    with pytest.raises(ValueError):
        encode_frame(1 << 32)
