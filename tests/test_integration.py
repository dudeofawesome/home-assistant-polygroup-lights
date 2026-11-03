"""Exercise HA services, shared remote state, learning, and restart behavior.

The pinned HA test release predates native RF receivers. Tests install the
documented receiver helper contract on that release; TX uses HA's real helper.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components import radio_frequency as rf
from homeassistant.core import Context
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.polygroup_lights.commands import encode_frame
from custom_components.polygroup_lights.config_flow import parse_levels
from custom_components.polygroup_lights.const import DOMAIN, EFFECTS
from custom_components.polygroup_lights.coordinator import TreeController

TX = "radio_frequency.tree_transmitter"
RX = "radio_frequency.tree_receiver"


def signal(code, frequency=433_895_000):
    return SimpleNamespace(
        timings=encode_frame(code),
        frequency=frequency,
        modulation=rf.ModulationType.OOK,
    )


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Christmas tree",
        data={
            "transmitter": TX,
            "receiver": RX,
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


async def test_shared_state_learning_echo_and_failed_tx(hass, entry):
    controller = TreeController(hass, entry)
    controller.state.power = False
    events = []
    controller.event_callback = lambda command, code: events.append((command, code))
    with patch(
        "custom_components.polygroup_lights.coordinator.monotonic", return_value=1
    ):
        controller.receive(signal(0x807FFF00))
        controller.receive(signal(0x807FFF00))
    assert controller.state.power is True
    assert len(events) == 1
    controller.receive(signal(2, frequency=123))
    assert controller.state.effect is None
    controller.receive(signal(2))
    assert controller.state.effect == "clear_steady"
    with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
        await controller.send("power", Context())
        assert controller.state.power is False
        controller.receive(signal(0x807FFF00))
        assert controller.state.power is False
        assert send.call_args.args[2].get_raw_timings() == encode_frame(0x807FFF00)
    with (
        patch.object(
            rf, "async_send_command", side_effect=HomeAssistantError("offline")
        ),
        pytest.raises(HomeAssistantError),
    ):
        await controller.send("power")
    assert controller.state.power is False
    controller.learn("color_steady")
    controller.receive(signal(5))
    assert entry.data["codes"]["color_steady"] == 5
    assert controller.state.effect == "color_steady"
    assert controller.learning is None
    controller.learn("combo")
    controller.receive(signal(2))  # Already bound: don't corrupt the mapping.
    assert "combo" not in controller.codes
    controller.finish_learning(None)


async def test_entities_and_remote_updates(hass, entry):
    hass.states.async_set(TX, "unknown")
    hass.states.async_set(RX, "unknown")
    with patch.object(
        rf, "async_subscribe_receiver", create=True, return_value=lambda: None
    ) as subscribe:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        receive = subscribe.call_args.args[2]
        light_id = "light.christmas_tree"
        assert hass.states.get(light_id).state == "unknown"
        with pytest.raises(HomeAssistantError, match="Synchronize"):
            await hass.services.async_call(
                "light", "turn_off", {"entity_id": light_id}, blocking=True
            )
        await hass.services.async_call(
            DOMAIN,
            "synchronize_state",
            {
                "entity_id": light_id,
                "power": True,
                "effect": "clear_steady",
                "brightness_index": 0,
            },
            blocking=True,
        )
        assert hass.states.get(light_id).state == "on"
        receive(signal(4))
        await hass.async_block_till_done()
        assert hass.states.get(light_id).attributes["brightness"] == 128
        with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
            await hass.services.async_call(
                "light",
                "turn_on",
                {
                    "entity_id": light_id,
                    "brightness": 64,
                },
                blocking=True,
            )
            assert send.call_count == 1
            assert hass.states.get(light_id).attributes["brightness"] == 64
            await hass.services.async_call(
                "light",
                "turn_on",
                {
                    "entity_id": light_id,
                    "brightness": 64,
                },
                blocking=True,
            )
            assert send.call_count == 1
            with pytest.raises(HomeAssistantError, match="Learn the combo"):
                await hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": light_id,
                        "effect": "Combo",
                    },
                    blocking=True,
                )
            assert send.call_count == 1
        receive(signal(3))
        await hass.async_block_till_done()
        assert hass.states.get(light_id).attributes["effect_key"] == "color_fade"
        with patch.object(rf, "async_send_command", new_callable=AsyncMock) as send:
            await hass.services.async_call(
                "light", "turn_off", {"entity_id": light_id}, blocking=True
            )
            assert hass.states.get(light_id).state == "off"
            await hass.services.async_call(
                "light", "turn_off", {"entity_id": light_id}, blocking=True
            )
            assert send.call_count == 1
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get(light_id).state == "off"
        assert hass.states.get(light_id).attributes["effect_key"] == "color_fade"
        hass.states.async_set(RX, "unavailable")
        await hass.async_block_till_done()
        assert hass.states.get(light_id).state == "unavailable"
        hass.states.async_set(RX, "unknown")
        await hass.async_block_till_done()
        assert hass.states.get(light_id).state == "unknown"
        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_native_transmit_helper(hass, entry):
    """Exercise HA's real RF routing and the raw waveform passed to hardware."""

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
    assert transmitter.sent.frequency == 433_895_000
    assert transmitter.sent.get_raw_timings() == encode_frame(0x807FFF00)
    assert hass.states.get(TX).state not in ("unknown", "unavailable")


async def test_remote_tracking_with_event_entity_disabled(hass, entry):
    er.async_get(hass).async_get_or_create(
        "event",
        DOMAIN,
        f"{entry.entry_id}_remote_command",
        config_entry=entry,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    hass.states.async_set(TX, "unknown")
    hass.states.async_set(RX, "unknown")
    with patch.object(
        rf, "async_subscribe_receiver", create=True, return_value=lambda: None
    ) as subscribe:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.runtime_data.event_callback is None
        subscribe.call_args.args[2](signal(2))
        await hass.async_block_till_done()
        assert (
            hass.states.get("light.christmas_tree").attributes["effect_key"]
            == "clear_steady"
        )
        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_config_requires_receivers(hass, monkeypatch):
    assert await async_setup_component(hass, "radio_frequency", {})
    monkeypatch.delattr(rf, "async_get_receivers", raising=False)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["reason"] == "receiver_support_required"


async def test_config_filters_adapters(hass):
    with (
        patch.object(rf, "async_get_transmitters", return_value=[TX]),
        patch.object(rf, "async_get_receivers", create=True, return_value=[RX]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == "form"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "transmitter": TX,
                "receiver": RX,
            },
        )
        assert result["type"] == "create_entry"
        await hass.async_block_till_done()


def test_remote_buttons_and_brightness_configuration():
    assert len(EFFECTS) == 11
    assert parse_levels("") == []
    assert parse_levels("100, 50,25") == [100, 50, 25]
    for invalid in ("a", "100", "100,100", "0,50", "101,50"):
        with pytest.raises(ValueError):
            parse_levels(invalid)
