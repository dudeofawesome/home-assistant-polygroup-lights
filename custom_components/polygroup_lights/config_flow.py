"""Configure an RF transmitter and brightness calibration."""

import voluptuous as vol
from homeassistant.components import radio_frequency as rf
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
)

from .const import (
    CONF_BRIGHTNESS_LEVELS,
    CONF_TRANSMITTER,
    DOMAIN,
    FREQUENCY,
)


def parse_levels(value: str) -> list[int]:
    """Percentages in the physical button's cycle order, empty until measured."""
    levels = [int(part.strip()) for part in value.split(",")] if value.strip() else []
    if (
        (levels and len(levels) < 2)
        or len(set(levels)) != len(levels)
        or any(not 1 <= level <= 100 for level in levels)
    ):
        raise ValueError("Use two or more distinct percentages from 1 to 100")
    return levels


class PolygroupConfigFlow(ConfigFlow, domain=DOMAIN):
    """Select a transmitter compatible with the tree's RF frequency."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PolygroupOptionsFlow()

    async def async_step_user(self, user_input=None):
        try:
            transmitters = rf.async_get_transmitters(
                self.hass, FREQUENCY, rf.ModulationType.OOK
            )
        except HomeAssistantError:
            return self.async_abort(reason="no_adapters")
        if not transmitters:
            return self.async_abort(reason="no_adapters")
        errors = {}
        if user_input is not None:
            if user_input[CONF_TRANSMITTER] not in transmitters:
                errors["base"] = "invalid_adapter"
            else:
                await self.async_set_unique_id(user_input[CONF_TRANSMITTER])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Christmas tree", data=user_input)
        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TRANSMITTER): EntitySelector(
                        EntitySelectorConfig(
                            domain="radio_frequency", include_entities=transmitters
                        )
                    ),
                }
            ),
        )


class PolygroupOptionsFlow(OptionsFlow):
    """Calibrate brightness only after measuring the physical cycle."""

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                levels = parse_levels(user_input[CONF_BRIGHTNESS_LEVELS])
            except ValueError:
                errors["base"] = "invalid_levels"
            else:
                return self.async_create_entry(
                    title="", data={CONF_BRIGHTNESS_LEVELS: levels}
                )
        current = self.config_entry.options.get(CONF_BRIGHTNESS_LEVELS, [])
        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BRIGHTNESS_LEVELS, default=",".join(map(str, current))
                    ): TextSelector(),
                }
            ),
        )
