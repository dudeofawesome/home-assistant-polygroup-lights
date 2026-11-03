"""Tests for TOTO Washlet command matching."""

from __future__ import annotations

import pytest

from custom_components.toto_washlet.commands import TotoData, TotoWashletCode


def test_matches_exact_frame() -> None:
    """An exact frame matches its command."""
    assert (
        TotoWashletCode.from_frames(TotoWashletCode.REAR.value) is TotoWashletCode.REAR
    )


@pytest.mark.parametrize(
    ("frame", "payload", "expected_code"),
    [
        (TotoData(0x39, 0x4), 0x403979, TotoWashletCode.BOWL_LIGHT_ON),
        (TotoData(0x39, 0x8), 0x8039B9, TotoWashletCode.BOWL_LIGHT_OFF),
        (TotoData(0xCC, 0x4), 0x40CC8C, TotoWashletCode.BEEP_SOUND_ON),
        (TotoData(0xCC, 0x8), 0x80CC4C, TotoWashletCode.BEEP_SOUND_OFF),
        (
            TotoData(0x66, 0x4),
            0x406626,
            TotoWashletCode.CLOSE_LID_BEFORE_FLUSHING_ON,
        ),
        (
            TotoData(0x66, 0x8),
            0x8066E6,
            TotoWashletCode.CLOSE_LID_BEFORE_FLUSHING_OFF,
        ),
    ],
)
def test_captured_stateful_frames(
    frame: TotoData,
    payload: int,
    expected_code: TotoWashletCode,
) -> None:
    """Captured stateful frames match and encode their checksums."""
    assert frame.payload == payload
    assert TotoWashletCode.from_frames([frame]) is expected_code


@pytest.mark.parametrize(
    ("frame", "expected_code"),
    [
        (TotoData(0x80, 0x2, 0x4), TotoWashletCode.REAR),
        (TotoData(0xA8, 0x2, 0x4), TotoWashletCode.SOFT_REAR),
        (TotoData(0x40, 0x2, 0x4), TotoWashletCode.FRONT),
        (TotoData(0x91, 0x2, 0x4), TotoWashletCode.SOFT_FRONT),
    ],
)
def test_matches_unique_single_frame_command_with_different_rc_code(
    frame: TotoData,
    expected_code: TotoWashletCode,
) -> None:
    """A unique command byte matches even when its RC fields differ."""
    assert TotoWashletCode.from_frames([frame]) is expected_code


def test_does_not_match_ambiguous_command_byte() -> None:
    """An RC mismatch does not match a shared stateful command byte."""
    assert TotoWashletCode.from_frames([TotoData(0xEC, 0x4, 0x4)]) is None


def test_does_not_match_multiframe_command_by_command_byte() -> None:
    """Command-byte fallback does not apply to multi-frame commands."""
    assert TotoWashletCode.from_frames([TotoData(0xDA, 0x0, 0x0)]) is None
