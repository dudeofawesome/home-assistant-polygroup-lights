"""Transmitter-only setup, persistent bindings, and assumed-state controls."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.components import radio_frequency as rf
from homeassistant.core import Context, State
from homeassistant.data_entry_flow import InvalidData
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

from custom_components.polygroup_lights.commands import encode_frame
from custom_components.polygroup_lights.config_flow import parse_levels
from custom_components.polygroup_lights.const import DOMAIN, EFFECTS
from custom_components.polygroup_lights.coordinator import TreeController

TX = "radio_frequency.tree_transmitter"
LIGHT = "light.christmas_tree"
EFFECT_SELECT = "select.christmas_tree_effect"


@pytest.mark.parametrize(
    ("command", "code"),
    [
        ("brightness", 0x807F11EE),
        ("power", 0x807FFF00),
    ],
)
async def test_verified_buttons_enabled_by_default_and_use_native_transport(
    hass, entry, command, code
):
    hass.states.async_set(TX, "unknown")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "button", DOMAIN, f"{entry.entry_id}_test_captured_{command}"
    )
    assert registry.async_get(entity_id).disabled_by is None
    assert registry.async_get(entity_id).entity_category is None
    assert hass.states.get(entity_id) is not None
    controller = entry.runtime_data
    controller.state.power = False
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        await hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True
        )
        send.assert_awaited_once()
        assert send.call_args.args[1] == TX
        assert send.call_args.args[2].get_raw_timings() == encode_frame(code)
    assert controller.state.last_command == command
    if command == "power":
        assert controller.state.power is True
    assert controller.state.brightness_index is None
    with (
        patch.object(
            rf, "async_send_command", side_effect=HomeAssistantError("offline")
        ),
        pytest.raises(HomeAssistantError),
    ):
        controller.state.last_command = None
        await hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True
        )
    assert controller.state.last_command is None
    hass.states.async_set(TX, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "unavailable"
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(
    ("command", "code"),
    [
        ("combo", 0x807F7788),
        ("clear_steady", 0x807F6699),
        ("clear_twinkle", 0x807FEE11),
        ("color_steady", 0x807F55AA),
    ],
)
async def test_effect_dropdown_sends_verified_commands(hass, entry, command, code):
    hass.states.async_set(TX, "unknown")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(EFFECT_SELECT).state == "unknown"
    assert hass.states.get(EFFECT_SELECT).attributes["options"] == [
        "Combo",
        "Clear Steady",
        "Clear Twinkle",
        "Color Steady",
    ]
    registry = er.async_get(hass)
    for effect in ("combo", "clear_steady", "clear_twinkle", "color_steady"):
        assert (
            registry.async_get_entity_id(
                "button", DOMAIN, f"{entry.entry_id}_test_captured_{effect}"
            )
            is None
        )
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        context = Context()
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": EFFECT_SELECT, "option": EFFECTS[command]},
            blocking=True,
            context=context,
        )
        send.assert_awaited_once()
        assert send.call_args.args[1] == TX
        assert send.call_args.args[2].get_raw_timings() == encode_frame(code)
        assert send.call_args.kwargs["context"] is context
    assert hass.states.get(EFFECT_SELECT).state == EFFECTS[command]
    assert hass.states.get(LIGHT).attributes["effect_key"] == command
    assert entry.runtime_data.state.power is None
    with (
        patch.object(
            rf, "async_send_command", side_effect=HomeAssistantError("offline")
        ),
        pytest.raises(HomeAssistantError),
    ):
        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": EFFECT_SELECT,
                "option": "Color Steady" if command == "combo" else "Combo",
            },
            blocking=True,
        )
    assert hass.states.get(EFFECT_SELECT).state == EFFECTS[command]
    assert entry.runtime_data.state.effect == command
    hass.states.async_set(TX, "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(EFFECT_SELECT).state == "unavailable"
    hass.states.async_set(TX, "unknown")
    await hass.async_block_till_done()
    assert hass.states.get(EFFECT_SELECT).state == EFFECTS[command]
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(EFFECT_SELECT).state == EFFECTS[command]
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_effect_dropdown_replaces_registered_effect_buttons(hass, entry):
    registry = er.async_get(hass)
    for command in ("combo", "clear_steady", "clear_twinkle", "color_steady"):
        registry.async_get_or_create(
            "button",
            DOMAIN,
            f"{entry.entry_id}_test_captured_{command}",
            config_entry=entry,
        )
    hass.states.async_set(TX, "unknown")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(EFFECT_SELECT) is not None
    assert not any(
        entity.unique_id == f"{entry.entry_id}_test_captured_{command}"
        for entity in registry.entities.values()
        for command in ("combo", "clear_steady", "clear_twinkle", "color_steady")
    )
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(("power", "state"), [(True, "on"), (False, "off")])
async def test_record_power_buttons_without_rf_and_restore(hass, entry, power, state):
    hass.states.async_set(TX, "unavailable")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "button", DOMAIN, f"{entry.entry_id}_record_power_{state}"
    )
    button = registry.async_get(entity_id)
    assert button.disabled_by is None
    assert button.entity_category == "config"
    assert hass.states.get(entity_id).name == f"Christmas tree Record tree as {state}"
    assert hass.states.get(entity_id).state != "unavailable"
    assert hass.states.get(LIGHT).state == "unavailable"
    controller = entry.runtime_data
    assert controller.state.power is None
    controller.state.effect = "clear_steady"
    controller.state.brightness_index = 1
    controller.state.last_command = "brightness"
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        for _ in range(2):
            await hass.services.async_call(
                "button", "press", {"entity_id": entity_id}, blocking=True
            )
        assert controller.state.power is power
        assert controller.state.effect == "clear_steady"
        assert controller.state.brightness_index == 1
        assert controller.state.last_command == "brightness"
        send.assert_not_called()
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(LIGHT).state == "unavailable"
        assert entry.runtime_data.state.power is power
        assert entry.runtime_data.state.effect == "clear_steady"
        assert entry.runtime_data.state.brightness_index == 1
        assert entry.runtime_data.state.last_command == "brightness"
        hass.states.async_set(TX, "unknown")
        await hass.async_block_till_done()
        assert hass.states.get(LIGHT).state == state
        assert not hass.states.get(LIGHT).attributes.get("assumed_state", False)
        for _ in range(2):
            await hass.services.async_call(
                "light", f"turn_{state}", {"entity_id": LIGHT}, blocking=True
            )
        send.assert_not_called()
        other_state = "off" if power else "on"
        for _ in range(2):
            await hass.services.async_call(
                "light", f"turn_{other_state}", {"entity_id": LIGHT}, blocking=True
            )
        send.assert_awaited_once()
        assert send.call_args.args[2].get_raw_timings() == encode_frame(0x807FFF00)
        assert hass.states.get(LIGHT).state == other_state
        await hass.services.async_call(
            "light", "toggle", {"entity_id": LIGHT}, blocking=True
        )
        assert send.await_count == 2
        assert hass.states.get(LIGHT).state == state
        assert not hass.states.get(LIGHT).attributes.get("assumed_state", False)
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(("power", "state"), [(True, "on"), (False, "off")])
async def test_restore_light_state_saved_without_extra_data(hass, entry, power, state):
    mock_restore_cache(
        hass,
        [
            State(
                LIGHT,
                state,
                {
                    "effect_key": "clear_steady",
                    "brightness_index": 1,
                    "brightness_levels": [100, 50, 25],
                    "last_command": "brightness",
                },
            )
        ],
    )
    hass.states.async_set(TX, "unknown")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == state
    assert entry.runtime_data.state.power is power
    assert entry.runtime_data.state.effect == "clear_steady"
    assert entry.runtime_data.state.brightness_index == 1
    assert entry.runtime_data.state.last_command == "brightness"
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Christmas tree",
        data={
            "transmitter": TX,
            "codes": {
                "power": 0x807FFF00,
                "clear_steady": 0x807F6699,
                "color_fade": 3,
                "brightness": 0x807F11EE,
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
        await controller.send("clear_fade")


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
    assert hass.states.get(LIGHT).attributes["assumed_state"] is True
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
    assert hass.states.get(EFFECT_SELECT).state == "Clear Steady"
    assert not hass.states.get(LIGHT).attributes.get("assumed_state", False)
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
        assert hass.states.get(EFFECT_SELECT).state == "Clear Steady"
        assert send.call_count == 1
        with pytest.raises(HomeAssistantError, match="No verified RF code.*clear_fade"):
            await hass.services.async_call(
                "light",
                "turn_on",
                {
                    "entity_id": LIGHT,
                    "effect": "Clear Fade",
                },
                blocking=True,
            )
        assert send.call_count == 1
        await hass.services.async_call(
            "light",
            "turn_on",
            {"entity_id": LIGHT, "effect": "Color Steady"},
            blocking=True,
        )
        assert hass.states.get(EFFECT_SELECT).state == "Color Steady"
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": LIGHT,
                "effect": "Color Fade",
            },
            blocking=True,
        )
        assert hass.states.get(EFFECT_SELECT).state == "unknown"
        await hass.services.async_call(
            "light", "turn_off", {"entity_id": LIGHT}, blocking=True
        )
        assert hass.states.get(LIGHT).state == "off"
        assert send.call_count == 4
        await hass.services.async_call(
            "light", "turn_off", {"entity_id": LIGHT}, blocking=True
        )
        assert send.call_count == 4
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == "off"
    assert hass.states.get(LIGHT).attributes["effect_key"] == "color_fade"
    assert not hass.states.get(LIGHT).attributes.get("assumed_state", False)
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


@pytest.mark.parametrize(
    ("command", "code"),
    [
        ("combo", 0x807F7788),
        ("clear_steady", 0x807F6699),
        ("color_steady", 0x807F55AA),
        ("clear_twinkle", 0x807FEE11),
        ("brightness", 0x807F11EE),
        ("power", 0x807FFF00),
    ],
)
async def test_fresh_install_sends_verified_defaults(hass, command, code):
    entry = MockConfigEntry(domain=DOMAIN, data={"transmitter": TX})
    controller = TreeController(hass, entry)
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        await controller.send(command)
    assert send.call_args.args[2].get_raw_timings() == encode_frame(code)
    assert controller.state.last_command == command


async def test_fresh_install_rejects_uncaptured_commands(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"transmitter": TX})
    controller = TreeController(hass, entry)
    with (
        patch.object(rf, "async_send_command", new_callable=AsyncMock) as send,
        pytest.raises(HomeAssistantError, match="No verified RF code.*clear_fade"),
    ):
        await controller.send("clear_fade")
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
