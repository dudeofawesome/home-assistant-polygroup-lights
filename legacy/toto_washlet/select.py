"""Select platform for the TOTO Washlet integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .commands import TotoWashletCode
from .const import CONF_INFRARED_ENTITY_ID, received_command_signal
from .entity import TotoWashletEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class TotoWashletSelectOption:
    """Describes a TOTO Washlet select option."""

    option: str
    command_code: TotoWashletCode


@dataclass(frozen=True, kw_only=True)
class TotoWashletSelectEntityDescription(SelectEntityDescription):
    """Describes TOTO Washlet select entity."""

    washlet_options: tuple[TotoWashletSelectOption, ...]


SELECT_DESCRIPTIONS: tuple[TotoWashletSelectEntityDescription, ...] = (
    TotoWashletSelectEntityDescription(
        key="water_temperature",
        translation_key="water_temperature",
        icon="mdi:thermometer-water",
        washlet_options=(
            TotoWashletSelectOption(
                option="off",
                command_code=TotoWashletCode.TEMPERATURE_OFF,
            ),
            TotoWashletSelectOption(
                option="1",
                command_code=TotoWashletCode.WATER_TEMPERATURE_1,
            ),
            TotoWashletSelectOption(
                option="2",
                command_code=TotoWashletCode.WATER_TEMPERATURE_2,
            ),
            TotoWashletSelectOption(
                option="3",
                command_code=TotoWashletCode.WATER_TEMPERATURE_3,
            ),
            TotoWashletSelectOption(
                option="4",
                command_code=TotoWashletCode.WATER_TEMPERATURE_4,
            ),
            TotoWashletSelectOption(
                option="5",
                command_code=TotoWashletCode.WATER_TEMPERATURE_5,
            ),
        ),
    ),
    TotoWashletSelectEntityDescription(
        key="dryer_air_temperature",
        translation_key="dryer_air_temperature",
        icon="mdi:thermometer",
        washlet_options=(
            TotoWashletSelectOption(
                option="1",
                command_code=TotoWashletCode.DRYER_AIR_TEMPERATURE_1,
            ),
            TotoWashletSelectOption(
                option="2",
                command_code=TotoWashletCode.DRYER_AIR_TEMPERATURE_2,
            ),
            TotoWashletSelectOption(
                option="3",
                command_code=TotoWashletCode.DRYER_AIR_TEMPERATURE_3,
            ),
            TotoWashletSelectOption(
                option="4",
                command_code=TotoWashletCode.DRYER_AIR_TEMPERATURE_4,
            ),
            TotoWashletSelectOption(
                option="5",
                command_code=TotoWashletCode.DRYER_AIR_TEMPERATURE_5,
            ),
        ),
    ),
    TotoWashletSelectEntityDescription(
        key="seat_temperature",
        translation_key="seat_temperature",
        icon="mdi:car-seat-heater",
        washlet_options=(
            TotoWashletSelectOption(
                option="off",
                command_code=TotoWashletCode.TEMPERATURE_OFF,
            ),
            TotoWashletSelectOption(
                option="1",
                command_code=TotoWashletCode.SEAT_TEMPERATURE_1,
            ),
            TotoWashletSelectOption(
                option="2",
                command_code=TotoWashletCode.SEAT_TEMPERATURE_2,
            ),
            TotoWashletSelectOption(
                option="3",
                command_code=TotoWashletCode.SEAT_TEMPERATURE_3,
            ),
            TotoWashletSelectOption(
                option="4",
                command_code=TotoWashletCode.SEAT_TEMPERATURE_4,
            ),
            TotoWashletSelectOption(
                option="5",
                command_code=TotoWashletCode.SEAT_TEMPERATURE_5,
            ),
        ),
    ),
    TotoWashletSelectEntityDescription(
        key="nozzle_position",
        translation_key="nozzle_position",
        icon="mdi:arrow-up-down",
        washlet_options=(
            TotoWashletSelectOption(
                option="1",
                command_code=TotoWashletCode.NOZZLE_POSITION_1,
            ),
            TotoWashletSelectOption(
                option="2",
                command_code=TotoWashletCode.NOZZLE_POSITION_2,
            ),
            TotoWashletSelectOption(
                option="3",
                command_code=TotoWashletCode.NOZZLE_POSITION_3,
            ),
            TotoWashletSelectOption(
                option="4",
                command_code=TotoWashletCode.NOZZLE_POSITION_4,
            ),
            TotoWashletSelectOption(
                option="5",
                command_code=TotoWashletCode.NOZZLE_POSITION_5,
            ),
        ),
    ),
    TotoWashletSelectEntityDescription(
        key="pressure_level",
        translation_key="pressure_level",
        icon="mdi:water",
        washlet_options=(
            TotoWashletSelectOption(
                option="1",
                command_code=TotoWashletCode.PRESSURE_LEVEL_1,
            ),
            TotoWashletSelectOption(
                option="2",
                command_code=TotoWashletCode.PRESSURE_LEVEL_2,
            ),
            TotoWashletSelectOption(
                option="3",
                command_code=TotoWashletCode.PRESSURE_LEVEL_3,
            ),
            TotoWashletSelectOption(
                option="4",
                command_code=TotoWashletCode.PRESSURE_LEVEL_4,
            ),
            TotoWashletSelectOption(
                option="5",
                command_code=TotoWashletCode.PRESSURE_LEVEL_5,
            ),
        ),
    ),
    TotoWashletSelectEntityDescription(
        key="user_profile",
        translation_key="user_profile",
        icon="mdi:account",
        washlet_options=(
            TotoWashletSelectOption(
                option="1",
                command_code=TotoWashletCode.USER_PROFILE_1,
            ),
            TotoWashletSelectOption(
                option="2",
                command_code=TotoWashletCode.USER_PROFILE_2,
            ),
            TotoWashletSelectOption(
                option="3",
                command_code=TotoWashletCode.USER_PROFILE_3,
            ),
            TotoWashletSelectOption(
                option="4",
                command_code=TotoWashletCode.USER_PROFILE_4,
            ),
        ),
    ),
    TotoWashletSelectEntityDescription(
        key="energy_saver",
        translation_key="energy_saver",
        icon="mdi:leaf",
        washlet_options=(
            TotoWashletSelectOption(
                option="off",
                command_code=TotoWashletCode.AUTO_ENERGY_SAVER_OFF,
            ),
            TotoWashletSelectOption(
                option="auto",
                command_code=TotoWashletCode.AUTO_ENERGY_SAVER,
            ),
            TotoWashletSelectOption(
                option="auto_plus",
                command_code=TotoWashletCode.AUTO_ENERGY_SAVER_PLUS,
            ),
        ),
    ),
    TotoWashletSelectEntityDescription(
        key="timer_energy_saver",
        translation_key="timer_energy_saver",
        icon="mdi:timer-cog",
        washlet_options=(
            TotoWashletSelectOption(
                option="off",
                command_code=TotoWashletCode.TIMER_ENERGY_SAVER_OFF,
            ),
            TotoWashletSelectOption(
                option="6",
                command_code=TotoWashletCode.TIMER_ENERGY_SAVER_6,
            ),
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TOTO Washlet selects from config entry."""
    infrared_entity_id = entry.data[CONF_INFRARED_ENTITY_ID]
    async_add_entities(
        TotoWashletSelect(entry, infrared_entity_id, description)
        for description in SELECT_DESCRIPTIONS
    )


class TotoWashletSelect(
    TotoWashletEntity, InfraredEmitterConsumerEntity, RestoreEntity, SelectEntity
):
    """TOTO Washlet select entity."""

    entity_description: TotoWashletSelectEntityDescription

    def __init__(
        self,
        entry: ConfigEntry,
        infrared_entity_id: str,
        description: TotoWashletSelectEntityDescription,
    ) -> None:
        """Initialize TOTO Washlet select."""
        super().__init__(entry, unique_id_suffix=description.key)
        self._entry_id = entry.entry_id
        self._attr_options = [
            option.option for option in description.washlet_options
        ]
        self._attr_current_option: str | None = None
        self._infrared_emitter_entity_id = infrared_entity_id
        self.entity_description = description
        self._command_code_to_option = {
            option.command_code: option.option
            for option in description.washlet_options
        }

    async def async_added_to_hass(self) -> None:
        """Track emitter availability and restore the last assumed option."""
        await super().async_added_to_hass()

        if (
            (last_state := await self.async_get_last_state()) is not None
            and last_state.state in self.options
        ):
            self._attr_current_option = last_state.state

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                received_command_signal(self._entry_id),
                self._handle_received_command,
            )
        )

    async def async_select_option(self, option: str) -> None:
        """Select a Washlet setting option."""
        command_code = next(
            washlet_option.command_code
            for washlet_option in self.entity_description.washlet_options
            if washlet_option.option == option
        )
        await self._send_command(command_code.to_command())
        self._attr_current_option = option
        self.async_write_ha_state()

    @callback
    def _handle_received_command(self, command_code: TotoWashletCode) -> None:
        """Update the selected option from a received remote command."""
        if (option := self._command_code_to_option.get(command_code)) is None:
            return

        if option == self._attr_current_option:
            return

        self._attr_current_option = option
        self.async_write_ha_state()
