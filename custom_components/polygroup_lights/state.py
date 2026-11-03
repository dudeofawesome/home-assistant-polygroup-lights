"""State inferred from commands, shared by HA actions and RF reception."""

from dataclasses import dataclass

from .const import DIMMABLE_EFFECTS, EFFECTS


@dataclass
class TreeState:
    """Unknown values stay unknown until explicitly synchronized."""

    power: bool | None = None
    effect: str | None = None
    brightness_index: int | None = None
    last_command: str | None = None

    def apply(self, command: str, brightness_levels: list[int]) -> None:
        """Apply a single button press, never individual repeated frames."""
        self.last_command = command
        if command == "power":
            if self.power is not None:
                self.power = not self.power
        elif command in EFFECTS:
            # Whether selecting an effect powers up an off tree is unverified.
            self.effect = command
        elif (
            command == "brightness"
            and self.effect in DIMMABLE_EFFECTS
            and self.power is True
            and self.brightness_index is not None
            and brightness_levels
        ):
            self.brightness_index = (self.brightness_index + 1) % len(brightness_levels)
        elif command == "brightness" and self.effect is None:
            self.brightness_index = None


class BurstFilter:
    """Suppress repeated packets and our own TX echo, using monotonic time."""

    def __init__(self) -> None:
        self.last_code: int | None = None
        self.last_received = float("-inf")
        self.echo_code: int | None = None
        self.echo_until = float("-inf")

    def accept(self, code: int, now: float) -> bool:
        """Group a continuous burst until 200ms of silence for that code."""
        duplicate = code == self.last_code and now - self.last_received < 0.2
        self.last_code, self.last_received = code, now
        return not duplicate and not (code == self.echo_code and now < self.echo_until)
