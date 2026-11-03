# Polygroup Lights for Home Assistant

Control a Polygroup Christmas tree with a PDR-053-29V controller and PDT-015-14 (053/056) RF remote through an ESPHome/CC1101 RF proxy at 433.895 MHz OOK.

The integration provides a stateful light with power and 11 effects: Combo; Clear Steady, Fade, and Twinkle; Color Steady, Fade, and Twinkle; and Clear/Color Alt, Fade, Fast Blink, and Slow Blink. It also provides a Cycle brightness button and a Remote command event. Timer control is intentionally omitted.

## Requirements and installation

Home Assistant must expose native RF transmitters **and receivers**, including `radio_frequency.async_get_receivers` and `async_subscribe_receiver`. RF transmitter support alone is insufficient; setup reports an explicit error on older versions. See the [Home Assistant RF consumer API](https://contributors.home-assistant.io/core/entities/radio-frequency/). Configure the proxy to expose both RF entities at 433.895 MHz OOK. Keep the receiver enabled so physical remote presses can update Home Assistant.

Add `https://github.com/dudeofawesome/home-assistant-polygroup-lights` as an Integration custom repository in HACS and install Polygroup Lights. For manual installation, copy `custom_components/polygroup_lights` into Home Assistant's `config/custom_components/`. Restart Home Assistant, then add **Polygroup Lights** under Settings → Devices & services and select the tree's RF transmitter and receiver.

## Learn the remote

In Developer tools → Actions, call `polygroup_lights.learn_command` targeting the tree's light, then press the corresponding remote button within 30 seconds. Repeat for each button. Learned codes are saved in the integration's config entry; no firmware rebuild is required. The light's `learned_commands` and `learning_command` attributes show progress. The Remote command event shows the received hexadecimal code, including unlearned frames. A code already assigned to another button is rejected during learning.

```yaml
action: polygroup_lights.learn_command
target:
  entity_id: light.christmas_tree
data:
  command: clear_steady
```

Supported command names are `power`, `brightness`, `combo`, `clear_steady`, `clear_fade`, `clear_twinkle`, `color_steady`, `color_fade`, `color_twinkle`, `clear_color_alt`, `clear_color_fade`, `clear_color_fast_blink`, and `clear_color_slow_blink`. Do not press Timer while learning another button. Unlearned controls report an error rather than sending guessed codes.

## Stateful operation

Both successful Home Assistant transmissions and learned physical remote presses update the same state. Repeated RF frames and local transmission echoes are suppressed to avoid toggling the displayed state multiple times. Mode presses update the selected effect; they do not assume that an off tree powers on. Power changes only when the desired state differs from the current state, preventing repeated `light.turn_on` calls from toggling the tree off.

The tree supplies no acknowledgement or state readback. Power begins unknown because On/Off is a toggle. Observe the tree and record its current state with `polygroup_lights.synchronize_state`; this action sends nothing. Synchronize after learning, controller button presses, power loss, missed RF signals, or restarting Home Assistant while someone has used the remote. State is restored across restarts as an assumption; a detected receiver disconnection clears it because remote presses could have been missed.

```yaml
action: polygroup_lights.synchronize_state
target:
  entity_id: light.christmas_tree
data:
  power: true
  effect: clear_steady
```

The buttons on the wired controller cannot be observed through RF unless the controller itself transmits a signal. Timer-driven changes also cannot be tracked; leave the tree's timer disabled when using Home Assistant for power scheduling. The integration's state remains an estimate even with reliable remote reception.

## Brightness

Until calibrated, use Cycle brightness; the integration does not invent percentages or a level count. The bracket on the remote associates brightness with Clear Steady, Color Steady, and Clear/Color Alt. Other effects do not advance the inferred brightness cycle.

To enable a brightness slider, first measure the distinct brightness levels and their order under successive remote presses. In the integration's options, enter those percentages in cycle order. Then synchronize `brightness_index` to the observed level using the same action above (zero means the first configured percentage). Subsequent remote Brightness presses advance that index, and Home Assistant brightness changes send the required number of cycle commands. Recalibrate if the tree resets brightness when switching effects or power; that behavior must be verified on the controller.

## Development

Run checks in the project environment:

```sh
devenv shell --quiet -- pytest tests
devenv shell --quiet -- ruff check custom_components/polygroup_lights tests
devenv shell --quiet -- ruff format --check custom_components/polygroup_lights tests
```

Protocol evidence and remaining hardware checks are in [docs/RF_CAPTURE_FINDINGS.md](docs/RF_CAPTURE_FINDINGS.md).
