# Polygroup RF evidence and hardware validation

## Confirmed inputs

User photos identify a PDR-053-29V wired controller and Polygroup PDT-015-14 (053/056) remote, FCC ID 2A62O-PDT015TS. The remote has 11 effect buttons, On/Off, Timer, and Brightness. The wired controller has brightness minus/plus and an unlabeled central button. Timer is excluded at the user's request. The remote's printed bracket connects Brightness to Clear Steady, Color Steady, and Clear/Color Alt.

The supplied handoff records successful reception using a Waveshare ESP32-C6-Zero and CC1101 at 433.895 MHz ASK/OOK over OpenThread. It contains one On/Off capture. Subsequent live captures are recorded below; transmission remains unverified. Its proposed firmware is not a validated installed configuration.

Live inspection on November 2, 2026 confirmed Home Assistant 2026.10.4 and ESPHome 2026.10.1. The installed tree firmware advertises two RadioFrequencyInfo objects: transmitter key 495550377 and receiver key 3655256847, both on device 0, with a fixed 433895000 Hz range and OOK modulation bit set. These keys are observations, not hardcoded bindings. That Home Assistant release filters out receiver-only ESPHome entities. The integration currently transmits only and does not access ESPHome internals, subscribe to receive events, or use firmware event forwarding. No firmware or Home Assistant runtime configuration was changed during these checks.

## Frame representation

The complete captured On/Off frame decodes MSB first as `807FFF00`, using a roughly 9000/-5350 microsecond header, 900 microsecond marks, -540 zero spaces, -1600 one spaces, and a trailing 900/-9000 mark/gap. `tests/test_commands.py` preserves the measured timings independently of the encoder. This is a raw pulse-distance representation, not evidence of NEC compatibility. Unknown pre-header 1000/-1000 activity was omitted from the candidate waveform and may matter if transmission fails.

No code is installed as a default. Capture and verify the model's codes during development, then add them to `commands.VERIFIED_CODES` so installations do not need to learn or enter codes. Existing saved bindings remain readable for compatibility. The retained decoder accepts complete 32-bit frames with timing tolerance and ignores unrelated timings. The retained burst filter uses a 200ms gap to separate same-code bursts; very rapid independent presses or unusual long holds need hardware testing when reception is added. Neither utility subscribes to live reception. Transmission uses three repeats after the initial frame. Capturing packets does not establish that the controller accepts that replay.

## November 3, 2026 capture session

Logs were captured through Kubernetes MCP by running `esphome logs /config/christmas-tree.yaml` in the current pod in namespace `esphome`, connected to `christmas-tree-rf.local`. The CLI was ESPHome 2026.10.2 and device firmware 2026.10.1. Read-only configuration inspection confirmed DEBUG logging, raw and rc_switch dumps, a 100us receive filter, 10ms idle threshold, and CC1101 ASK/OOK at 433.895MHz. Raw captures were decoded with the existing `commands.decode_frames` function in `devenv`.

| Button | Captured code | Complete decoded frames | Raw evidence |
| --- | --- | --- | --- |
| Combo | `807F7788` | Three independent presses, five identical frames each | [Clean attempt](rf-captures/2026-11-03-combo-attempt-2.log) |
| Clear Steady | `807F6699` | Three independent presses, five identical frames each | [Capture](rf-captures/2026-11-03-clear-steady.log) |
| Color Steady | `807F55AA` | Three independent presses, five identical frames each | [Capture](rf-captures/2026-11-03-color-steady.log) |
| Clear Twinkle | `807FEE11` | Three press windows with five, five, and two matching complete frames; third press partly fragmented | [Capture](rf-captures/2026-11-03-clear-twinkle.log) |
| Brightness | `807F11EE` | Three independent presses, five identical frames each | [Capture](rf-captures/2026-11-03-brightness.log) |
| On/Off | `807FFF00` | Two separated bursts, five and two frames; intervening signals fragmented | [Capture](rf-captures/2026-11-03-on-off-attempt-1.log) |

Moving the remote to about one metre from the RF proxy resolved the fragmented [first Combo attempt](rf-captures/2026-11-03-combo-attempt-1.log). The clean Combo and Brightness bursts begin with approximately three 1000/-1000 mark/space pairs followed by 1000/-2000, before five full frames. The current encoder omits that preamble and transmits four frames total; whether those differences affect tree acceptance remains unverified.

The Color Steady capture window also contains an earlier burst at 03:40:00.745 with four decoded `807F6699` frames matching Clear Steady. This burst is retained as unlabeled extra activity and excluded from Color Steady's three-press result, which starts at 03:40:05.719.

On/Off matches the handoff candidate, but its clean three-press consistency check remains outstanding. Brightness reception establishes a stable button code, not brightness levels or cycle behavior. Timer was skipped at the user's request. Seven effect buttons remain uncaptured. The initial capture was stopped at the user's request, then resumed to capture Clear Steady, Color Steady, and Clear Twinkle. That second session was stopped after all three requested buttons were captured. Their raw logs are preserved above. No replay, firmware update, or Home Assistant runtime configuration change was performed.

All six codes are retained in `commands.CAPTURED_CODES`, exposed only through enabled-by-default **Test captured Combo**, **Test captured Clear Steady**, **Test captured Color Steady**, **Test captured Clear Twinkle**, **Test captured Brightness**, and **Test captured On/Off** diagnostic buttons. These use native RF transport and call `TreeController.apply_command` after successful transmission, preserving assumed-state semantics. They do not populate normal command bindings or `VERIFIED_CODES`. Press a test button on the device page to verify physical response; promote codes to verified defaults only after replay is checked. Existing saved bindings retain precedence for normal controls.

## Required checks on hardware

1. Inspect the actual ESPHome configuration and installed Home Assistant/ESPHome versions. Preserve Thread and secret references; do not reuse the copied bathroom IR proxy address or credentials. No USB serial proxy was present during development.
2. Verify that Home Assistant exposes a compatible RF transmitter and select it during setup. No receiver API or entity is required. Tests exercise the native transmit helper, assumed-state updates, and preservation of existing bindings and obsolete receiver settings.
3. Verify replay of the captured On/Off candidate during development and confirm one toggle per action before bundling it as a supported code. If replay fails, compare the whole recorded waveform, including possible wake-up preamble and repetition behavior.
4. Capture the seven remaining effect buttons and repeat clean On/Off and Clear Twinkle captures where frames were fragmented. Check whether different remotes share the same codes. Verify transmission of Combo, Clear Steady, Color Steady, Clear Twinkle, Brightness, On/Off, and subsequent captures before bundling the model's command set. Physical remote presses currently require manual state synchronization and do not generate an integration event.
5. Synchronize observed power and effect, then compare HA and remote actions. Selecting an effect records that effect without assuming it powers on an off tree. Verify whether effect or power changes reset brightness before enabling calibrated brightness.
6. Count brightness levels in each of the three bracketed modes, verify cycle direction and wraparound, and enter measured percentages in options. Synchronize the current index; compare remote and slider updates. Wired controller presses require manual resynchronization unless RF reception from that controller is separately demonstrated.

The timer function is intentionally absent. Automatic changes by an enabled hardware timer cannot be inferred from remote RF commands; disable that timer for Home Assistant scheduling.

## Adding official reception later

The core receiver API was merged in [PR #186720](https://github.com/home-assistant/core/pull/186720), and the ESPHome adapter in [PR #189484](https://github.com/home-assistant/core/pull/189484). Reception should use those official interfaces once a supported release includes both.

Keep subscriptions and receiver lifecycle in a separate adapter. Decode frames with `decode_frames`, resolve codes using the existing command bindings, and suppress packet repeats and local transmission echoes before calling `TreeController.apply_command`. That method updates the shared `TreeState` and entity listeners without transmitting. `send` calls the same method only after the official transmit helper succeeds. Existing decoder and burst-filter tests preserve the protocol evidence; the state-transition hook has a regression test proving that it does not transmit. Receiver-based learning and command events can be added alongside the official adapter without changing light or brightness command semantics.
