"""Config flow for TOTO Washlet integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.infrared import (
    DOMAIN as INFRARED_DOMAIN,
    async_get_emitters,
    async_get_receivers,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    CONF_INFRARED_ENTITY_ID,
    CONF_INFRARED_RECEIVER_ENTITY_ID,
    DOMAIN,
)


class TotoWashletConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for TOTO Washlet."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return TotoWashletOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        emitter_entity_ids = async_get_emitters(self.hass)
        if not emitter_entity_ids:
            return self.async_abort(reason="no_emitters")

        receiver_entity_ids = async_get_receivers(self.hass)

        if user_input is not None:
            entity_id = user_input[CONF_INFRARED_ENTITY_ID]

            await self.async_set_unique_id(f"toto_washlet_{entity_id}")
            self._abort_if_unique_id_configured()

            ent_reg = er.async_get(self.hass)
            entry = ent_reg.async_get(entity_id)
            entity_name = (
                entry.name or entry.original_name or entity_id if entry else entity_id
            )
            title = f"TOTO Washlet via {entity_name}"

            return self.async_create_entry(title=title, data=user_input)

        schema = {
            vol.Required(CONF_INFRARED_ENTITY_ID): EntitySelector(
                EntitySelectorConfig(
                    domain=INFRARED_DOMAIN,
                    include_entities=emitter_entity_ids,
                )
            ),
        }
        if receiver_entity_ids:
            schema[vol.Optional(CONF_INFRARED_RECEIVER_ENTITY_ID)] = EntitySelector(
                EntitySelectorConfig(
                    domain=INFRARED_DOMAIN,
                    include_entities=receiver_entity_ids,
                )
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
        )


class TotoWashletOptionsFlow(OptionsFlow):
    """Handle options for TOTO Washlet."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options step."""
        receiver_entity_ids = async_get_receivers(self.hass)
        if not receiver_entity_ids:
            return self.async_abort(reason="no_receivers")

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_receiver = self._config_entry.options.get(
            CONF_INFRARED_RECEIVER_ENTITY_ID,
            self._config_entry.data.get(CONF_INFRARED_RECEIVER_ENTITY_ID),
        )
        receiver_field = vol.Optional(CONF_INFRARED_RECEIVER_ENTITY_ID)
        if current_receiver in receiver_entity_ids:
            receiver_field = vol.Optional(
                CONF_INFRARED_RECEIVER_ENTITY_ID,
                default=current_receiver,
            )

        schema = {
            receiver_field: EntitySelector(
                EntitySelectorConfig(
                    domain=INFRARED_DOMAIN,
                    include_entities=receiver_entity_ids,
                )
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
