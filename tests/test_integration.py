"""Transmitter-only setup, persistent bindings, and assumed-state controls."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.components import radio_frequency as rf
from homeassistant.core import Context
from homeassistant.data_entry_flow import InvalidData
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.polygroup_lights.commands import encode_frame
from custom_components.polygroup_lights.config_flow import parse_levels
from custom_components.polygroup_lights.const import DOMAIN, EFFECTS
from custom_components.polygroup_lights.coordinator import TreeController

TX = "radio_frequency.tree_transmitter"
LIGHT = "light.christmas_tree"


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Christmas tree",
        data={
            "transmitter": TX,
            "codes": {
                "power": 0x807FFF00,
                "clear_steady": 2,
                "color_fade": 3,
                "brightness": 4,
            },
        },
        options={"brightness_levels": [100, 50, 25]},
    )
    entry.add_to_hass(hass)
    return entry


async def test_successful_send_commits_state_and_failure_does_not(hass, entry):
    controller = TreeController(hass, entry)
    controller.state.power = False
    listener = Mock()
    controller.listeners.add(listener)
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        context = Context()
        await controller.send("power", context)
        assert controller.state.power is True
        assert send.call_args.kwargs["context"] is context
        assert send.call_args.args[2].get_raw_timings() == encode_frame(0x807FFF00)
    listener.assert_called_once()
    with (
        patch.object(
            rf, "async_send_command", side_effect=HomeAssistantError("offline")
        ),
        pytest.raises(HomeAssistantError),
    ):
        await controller.send("power")
    assert controller.state.power is True
    listener.assert_called_once()
    with pytest.raises(HomeAssistantError, match="No verified RF code"):
        await controller.send("combo")


async def test_state_transition_hook_never_transmits(hass, entry):
    """The same hook can accept deduplicated commands from an official receiver later."""
    controller = TreeController(hass, entry)
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        controller.apply_command("color_fade")
        assert controller.state.effect == "color_fade"
        send.assert_not_called()


async def test_entities_services_and_restore(hass, entry):
    hass.states.async_set(TX, "unknown")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == "unknown"
    assert not hass.services.has_service(DOMAIN, "learn_command")
    assert not hass.services.has_service(DOMAIN, "set_command_code")
    assert not hass.states.async_entity_ids("event")
    with pytest.raises(HomeAssistantError, match="Synchronize"):
        await hass.services.async_call(
            "light", "turn_off", {"entity_id": LIGHT}, blocking=True
        )
    await hass.services.async_call(
        DOMAIN,
        "synchronize_state",
        {
            "entity_id": LIGHT,
            "power": True,
            "effect": "clear_steady",
            "brightness_index": 0,
        },
        blocking=True,
    )
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": LIGHT,
                "brightness": 128,
            },
            blocking=True,
        )
        assert send.call_count == 1
        assert hass.states.get(LIGHT).attributes["brightness"] == 128
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": LIGHT,
                "brightness": 128,
            },
            blocking=True,
        )
        assert send.call_count == 1
        with pytest.raises(HomeAssistantError, match="No verified RF code.*combo"):
            await hass.services.async_call(
                "light",
                "turn_on",
                {
                    "entity_id": LIGHT,
                    "effect": "Combo",
                },
                blocking=True,
            )
        assert send.call_count == 1
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": LIGHT,
                "effect": "Color Fade",
            },
            blocking=True,
        )
        await hass.services.async_call(
            "light", "turn_off", {"entity_id": LIGHT}, blocking=True
        )
        assert hass.states.get(LIGHT).state == "off"
        assert send.call_count == 3
        await hass.services.async_call(
            "light", "turn_off", {"entity_id": LIGHT}, blocking=True
        )
        assert send.call_count == 3
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == "off"
    assert hass.states.get(LIGHT).attributes["effect_key"] == "color_fade"
    hass.states.async_set(TX, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == "unavailable"
    assert (
        hass.states.get("button.christmas_tree_cycle_brightness").state == "unavailable"
    )
    hass.states.async_set(TX, "unknown")
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == "off"
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_saved_bindings_survive_reload(hass, entry):
    hass.states.async_set(TX, "unknown")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.codes["power"] == 0x807FFF00
    assert "power" in hass.states.get(LIGHT).attributes["available_commands"]
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.runtime_data.codes["power"] == 0x807FFF00
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_bundled_codes_and_saved_binding_precedence(hass, entry):
    with patch.dict(
        "custom_components.polygroup_lights.coordinator.VERIFIED_CODES",
        {
            "combo": 0x12345678,
            "power": 0x87654321,
        },
    ):
        controller = TreeController(hass, entry)
    assert controller.codes["combo"] == 0x12345678
    assert controller.codes["power"] == 0x807FFF00


async def test_fresh_install_does_not_send_unverified_candidate(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"transmitter": TX})
    controller = TreeController(hass, entry)
    assert controller.codes == {}
    with (
        patch.object(rf, "async_send_command", new_callable=AsyncMock) as send,
        pytest.raises(HomeAssistantError, match="No verified RF code.*power"),
    ):
        await controller.send("power")
    send.assert_not_called()


@pytest.mark.parametrize(
    "receiver", ["radio_frequency.old_receiver", "esphome:missing:0:123"]
)
async def test_legacy_receiver_setting_is_ignored(hass, entry, receiver):
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, "receiver": receiver}
    )
    hass.states.async_set(TX, "unknown")
    # No ESPHome entry, receiver entity, or receive helper is needed.
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == "unknown"
    assert entry.runtime_data.codes["power"] == 0x807FFF00
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_native_transmit_helper(hass, entry):
    class Transmitter(rf.RadioFrequencyTransmitterEntity):
        _attr_name = "Tree transmitter"

        @property
        def supported_frequency_ranges(self):
            return [(433_895_000, 433_895_000)]

        async def async_send_command(self, command):
            self.sent = command

    assert await async_setup_component(hass, "radio_frequency", {})
    transmitter = Transmitter()
    transmitter.entity_id = TX
    await hass.data[rf.DATA_COMPONENT].async_add_entities([transmitter])
    controller = TreeController(hass, entry)
    controller.state.power = False
    await controller.send("power", Context())
    assert controller.state.power is True
    assert transmitter.sent.get_raw_timings() == encode_frame(0x807FFF00)


async def test_config_requires_only_transmitter(hass):
    with patch.object(rf, "async_get_transmitters", return_value=[TX]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == "form"
        assert {str(key) for key in result["data_schema"].schema} == {"transmitter"}
        with pytest.raises(InvalidData):
            await hass.config_entries.flow.async_configure(
                result["flow_id"], {"transmitter": "radio_frequency.wrong"}
            )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"transmitter": TX}
        )
        assert result["type"] == "create_entry"
        assert result["data"] == {"transmitter": TX}
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(result["result"].entry_id)


async def test_config_without_transmitter(hass):
    with patch.object(rf, "async_get_transmitters", return_value=[]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
    assert result["reason"] == "no_adapters"


def test_remote_buttons_and_brightness_configuration():
    assert len(EFFECTS) == 11
    assert parse_levels("") == []
    assert parse_levels("100, 50,25") == [100, 50, 25]
    for invalid in ("a", "100", "100,100", "0,50", "101,50"):
        with pytest.raises(ValueError):
            parse_levels(invalid)
