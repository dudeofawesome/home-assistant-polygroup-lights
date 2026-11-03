"""State must never count repeated frames as extra physical presses."""

from custom_components.polygroup_lights.state import BurstFilter, TreeState


def test_repeat_and_echo_filter():
    burst = BurstFilter()
    assert burst.accept(1, 0)
    assert not burst.accept(1, 0.1)
    assert not burst.accept(1, 0.25)
    assert burst.accept(1, 0.5)
    assert burst.accept(2, 0.51)
    burst.echo_code, burst.echo_until = 3, 2
    assert not burst.accept(3, 1)
    assert burst.accept(2, 1.01)
    assert burst.accept(3, 2.1)


def test_unknown_power_requires_sync():
    state = TreeState()
    state.apply("power", [])
    assert state.power is None
    state.power = True
    state.apply("power", [])
    assert state.power is False
    state.apply("clear_steady", [])
    assert state.effect == "clear_steady"
    assert state.power is False


def test_calibrated_brightness_and_restricted_modes():
    state = TreeState(power=True, effect="clear_steady", brightness_index=0)
    for index in (1, 2, 0):
        state.apply("brightness", [100, 50, 25])
        assert state.brightness_index == index
    state.apply("clear_fade", [100, 50, 25])
    state.apply("brightness", [100, 50, 25])
    assert state.brightness_index == 0
    state.effect = None
    state.apply("brightness", [100, 50, 25])
    assert state.brightness_index is None
