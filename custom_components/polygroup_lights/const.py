"""Polygroup PDT-015-14 constants."""

DOMAIN = "polygroup_lights"
FREQUENCY = 433_895_000
CONF_TRANSMITTER = "transmitter"
CONF_RECEIVER = "receiver"
CONF_CODES = "codes"
CONF_BRIGHTNESS_LEVELS = "brightness_levels"

# Labels transcribed from the PDT-015-14 (053/056) remote.
EFFECTS = {
    "combo": "Combo",
    "clear_steady": "Clear Steady",
    "clear_fade": "Clear Fade",
    "clear_twinkle": "Clear Twinkle",
    "color_steady": "Color Steady",
    "color_fade": "Color Fade",
    "color_twinkle": "Color Twinkle",
    "clear_color_alt": "Clear/Color Alt",
    "clear_color_fade": "Clear/Color Fade",
    "clear_color_fast_blink": "Clear/Color Fast Blink",
    "clear_color_slow_blink": "Clear/Color Slow Blink",
}
COMMANDS = (*EFFECTS, "power", "brightness")
DIMMABLE_EFFECTS = {"clear_steady", "color_steady", "clear_color_alt"}
