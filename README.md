# Polygroup Lights for Home Assistant

Control a Polygroup Christmas tree with a PDR-053-29V controller and PDT-015-14 (053/056) RF remote through an ESPHome/CC1101 RF proxy at 433.895 MHz OOK.

The integration provides a light with assumed power state and 11 effects: Combo; Clear Steady, Fade, and Twinkle; Color Steady, Fade, and Twinkle; and Clear/Color Alt, Fade, Fast Blink, and Slow Blink. It also provides a Cycle brightness button. Physical remote reception, in-app RF learning, and timer control are currently unsupported.

## Requirements and installation

Home Assistant must expose a `radio_frequency` transmitter supporting 433.895 MHz OOK. Configure the ESPHome/CC1101 proxy's transmitter at that frequency. No receiver entity, RF receive API, or firmware event forwarding is required.

Add `https://github.com/dudeofawesome/home-assistant-polygroup-lights` as an Integration custom repository in HACS and install Polygroup Lights. For manual installation, copy `custom_components/polygroup_lights` into Home Assistant's `config/custom_components/`. Restart Home Assistant, then add **Polygroup Lights** under Settings → Devices & services and select the tree's RF transmitter.

## Hardware support status

Verified RF codes are bundled for Combo, Clear Steady, Color Steady, Clear Twinkle, Brightness, and On/Off. These commands work through the light and enabled-by-default remote buttons without learning or entering codes. The remaining seven effects are not yet supported and report an error if requested. The light's `available_commands` attribute lists commands with an available code, including compatible saved bindings.

The remote buttons send one command per press; On/Off toggles power even when its current state is unknown. The light's on/off controls require synchronized power state to avoid unwanted toggles. Brightness and Cycle brightness both send the physical remote's brightness command without assuming a percentage.

## Stateful operation

Successful Home Assistant transmissions update the assumed state once per action; failed sends leave it unchanged. Power changes only when the desired state differs from the current state, preventing repeated `light.turn_on` calls from toggling the tree off. Effects update after their command is sent. Physical remote and wired controller presses do not update Home Assistant.

The tree supplies no acknowledgement or state readback. Power begins unknown because On/Off is a toggle. Observe the tree, then press **Record tree as on** or **Record tree as off** under Configuration on its device page. These buttons update Home Assistant's power estimate without sending RF and remain available when the transmitter is offline. After recording the state, use the light's normal on/off controls. Synchronize again after physical remote or wired controller use, power loss, or any other change made outside Home Assistant. State is restored across restarts as an assumption. Availability of the light and remote command buttons follows the transmitter alone.

Use `polygroup_lights.synchronize_state` to record power together with an observed effect or calibrated brightness index; this action also sends nothing.

```yaml
action: polygroup_lights.synchronize_state
target:
  entity_id: light.christmas_tree
data:
  power: true
  effect: clear_steady
```

Timer-driven changes cannot be tracked; leave the tree's timer disabled when using Home Assistant for power scheduling. The integration's state remains an estimate even after a successful transmission.

## Brightness

Until calibrated, use Cycle brightness; the integration does not invent percentages or a level count. The bracket on the remote associates brightness with Clear Steady, Color Steady, and Clear/Color Alt. Other effects do not advance the inferred brightness cycle.

To enable a brightness slider, first measure the distinct brightness levels and their order under successive remote presses. In the integration's options, enter those percentages in cycle order. Then synchronize `brightness_index` to the observed level using the same action above (zero means the first configured percentage). Home Assistant brightness changes send the required number of cycle commands and advance the assumed index. Physical Brightness presses require manual resynchronization. Recalibrate if the tree resets brightness when switching effects or power; that behavior must be verified on the controller.

## Development

Run checks in the project environment:

```sh
devenv shell --quiet -- pytest tests
devenv shell --quiet -- ruff check custom_components/polygroup_lights tests
devenv shell --quiet -- ruff format --check custom_components/polygroup_lights tests
```

Protocol evidence and remaining hardware checks are in [docs/RF_CAPTURE_FINDINGS.md](docs/RF_CAPTURE_FINDINGS.md).

State transitions are isolated in `TreeState.apply`, with `TreeController.apply_command` committing a logical command without transmitting. Future official RF receiver support can decode and deduplicate incoming signals, then call that same method. Raw frame decoding and burst filtering remain transport-independent utilities; no receiver subscription is currently installed.
