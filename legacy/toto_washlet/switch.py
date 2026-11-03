"""Switch platform for the TOTO Washlet integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .commands import TotoWashletCode
from .const import CONF_INFRARED_ENTITY_ID, received_command_signal
from .entity import TotoWashletEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class TotoWashletSwitchEntityDescription(SwitchEntityDescription):
    """Describes TOTO Washlet switch entity."""

    turn_on_command_code: TotoWashletCode
    turn_off_command_code: TotoWashletCode


SWITCH_DESCRIPTIONS: tuple[TotoWashletSwitchEntityDescription, ...] = (
    TotoWashletSwitchEntityDescription(
        key="auto_flush",
        translation_key="auto_flush",
        icon="mdi:water-sync",
        turn_on_command_code=TotoWashletCode.AUTO_FLUSH_ON,
        turn_off_command_code=TotoWashletCode.AUTO_FLUSH_OFF,
    ),
    TotoWashletSwitchEntityDescription(
        key="auto_lid_open",
        translation_key="auto_lid_open",
        icon="mdi:toilet",
        turn_on_command_code=TotoWashletCode.AUTO_LID_OPEN_ON,
        turn_off_command_code=TotoWashletCode.AUTO_LID_OPEN_OFF,
    ),
    TotoWashletSwitchEntityDescription(
        key="close_lid_before_flushing",
        translation_key="close_lid_before_flushing",
        icon="mdi:toilet",
        turn_on_command_code=TotoWashletCode.CLOSE_LID_BEFORE_FLUSHING_ON,
        turn_off_command_code=TotoWashletCode.CLOSE_LID_BEFORE_FLUSHING_OFF,
    ),
    TotoWashletSwitchEntityDescription(
        key="bowl_light",
        translation_key="bowl_light",
        icon="mdi:lightbulb",
        turn_on_command_code=TotoWashletCode.BOWL_LIGHT_ON,
        turn_off_command_code=TotoWashletCode.BOWL_LIGHT_OFF,
    ),
    TotoWashletSwitchEntityDescription(
        key="beep_sound",
        translation_key="beep_sound",
        icon="mdi:volume-high",
        turn_on_command_code=TotoWashletCode.BEEP_SOUND_ON,
        turn_off_command_code=TotoWashletCode.BEEP_SOUND_OFF,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TOTO Washlet switches from config entry."""
    infrared_entity_id = entry.data[CONF_INFRARED_ENTITY_ID]
    async_add_entities(
        TotoWashletSwitch(entry, infrared_entity_id, description)
        for description in SWITCH_DESCRIPTIONS
    )


class TotoWashletSwitch(
    TotoWashletEntity, InfraredEmitterConsumerEntity, RestoreEntity, SwitchEntity
):
    """TOTO Washlet switch entity."""

    entity_description: TotoWashletSwitchEntityDescription

    def __init__(
        self,
        entry: ConfigEntry,
        infrared_entity_id: str,
        description: TotoWashletSwitchEntityDescription,
    ) -> None:
        """Initialize TOTO Washlet switch."""
        super().__init__(entry, unique_id_suffix=description.key)
        self._entry_id = entry.entry_id
        self._attr_is_on: bool | None = None
        self._infrared_emitter_entity_id = infrared_entity_id
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        """Track emitter availability and restore the last assumed state."""
        await super().async_added_to_hass()

        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                received_command_signal(self._entry_id),
                self._handle_received_command,
            )
        )

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn on the Washlet setting."""
        await self._send_command(
            self.entity_description.turn_on_command_code.to_command()
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn off the Washlet setting."""
        await self._send_command(
            self.entity_description.turn_off_command_code.to_command()
        )
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def _handle_received_command(self, command_code: TotoWashletCode) -> None:
        """Update the switch state from a received remote command."""
        if command_code == self.entity_description.turn_on_command_code:
            is_on = True
        elif command_code == self.entity_description.turn_off_command_code:
            is_on = False
        else:
            return

        if is_on == self._attr_is_on:
            return

        self._attr_is_on = is_on
        self.async_write_ha_state()
