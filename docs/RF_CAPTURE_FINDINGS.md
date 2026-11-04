# Polygroup RF evidence and hardware validation

## Confirmed inputs

User photos identify a PDR-053-29V wired controller and Polygroup PDT-015-14 (053/056) remote, FCC ID 2A62O-PDT015TS. The remote has 11 effect buttons, On/Off, Timer, and Brightness. The wired controller has brightness minus/plus and an unlabeled central button. Timer is excluded at the user's request. The remote's printed bracket connects Brightness to Clear Steady, Color Steady, and Clear/Color Alt.

The supplied handoff records successful reception using a Waveshare ESP32-C6-Zero and CC1101 at 433.895 MHz ASK/OOK over OpenThread. It contains one On/Off capture; all other codes, independent-press stability, transmission, and native proxy operation remain unverified. Its proposed firmware is not a validated installed configuration.

Live inspection on November 2, 2026 confirmed Home Assistant 2026.10.4 and ESPHome 2026.10.1. The installed tree firmware advertises two RadioFrequencyInfo objects: transmitter key 495550377 and receiver key 3655256847, both on device 0, with a fixed 433895000 Hz range and OOK modulation bit set. These keys are observations, not hardcoded bindings. That Home Assistant release filters out receiver-only ESPHome entities. The integration currently transmits only and does not access ESPHome internals, subscribe to receive events, or use firmware event forwarding. No firmware or Home Assistant runtime configuration was changed during these checks.

## Frame representation

The complete captured On/Off frame decodes MSB first as `807FFF00`, using a roughly 9000/-5350 microsecond header, 900 microsecond marks, -540 zero spaces, -1600 one spaces, and a trailing 900/-9000 mark/gap. `tests/test_commands.py` preserves the measured timings independently of the encoder. This is a raw pulse-distance representation, not evidence of NEC compatibility. Unknown pre-header 1000/-1000 activity was omitted from the candidate waveform and may matter if transmission fails.

No code is installed as a default. Capture and verify the model's codes during development, then add them to `commands.VERIFIED_CODES` so installations do not need to learn or enter codes. Existing saved bindings remain readable for compatibility. The retained decoder accepts complete 32-bit frames with timing tolerance and ignores unrelated timings. The retained burst filter uses a 200ms gap to separate same-code bursts; very rapid independent presses or unusual long holds need hardware testing when reception is added. Neither utility subscribes to live reception. Transmission uses three repeats after the initial frame. Capturing packets does not establish that the controller accepts that replay.

## Required checks on hardware

1. Inspect the actual ESPHome configuration and installed Home Assistant/ESPHome versions. Preserve Thread and secret references; do not reuse the copied bathroom IR proxy address or credentials. No USB serial proxy was present during development.
2. Verify that Home Assistant exposes a compatible RF transmitter and select it during setup. No receiver API or entity is required. Tests exercise the native transmit helper, assumed-state updates, and preservation of existing bindings and obsolete receiver settings.
3. Verify replay of the captured On/Off candidate during development and confirm one toggle per action before bundling it as a supported code. If replay fails, compare the whole recorded waveform, including possible wake-up preamble and repetition behavior.
4. Capture each of the 11 effect buttons and Brightness separately, checking multiple independent presses for stable codes and whether different remotes share the same codes. Verify transmission, then bundle the model's command set. Physical remote presses currently require manual state synchronization and do not generate an integration event.
5. Synchronize observed power and effect, then compare HA and remote actions. Selecting an effect records that effect without assuming it powers on an off tree. Verify whether effect or power changes reset brightness before enabling calibrated brightness.
6. Count brightness levels in each of the three bracketed modes, verify cycle direction and wraparound, and enter measured percentages in options. Synchronize the current index; compare remote and slider updates. Wired controller presses require manual resynchronization unless RF reception from that controller is separately demonstrated.

The timer function is intentionally absent. Automatic changes by an enabled hardware timer cannot be inferred from remote RF commands; disable that timer for Home Assistant scheduling.

## Adding official reception later

The core receiver API was merged in [PR #186720](https://github.com/home-assistant/core/pull/186720), and the ESPHome adapter in [PR #189484](https://github.com/home-assistant/core/pull/189484). Reception should use those official interfaces once a supported release includes both.

Keep subscriptions and receiver lifecycle in a separate adapter. Decode frames with `decode_frames`, resolve codes using the existing command bindings, and suppress packet repeats and local transmission echoes before calling `TreeController.apply_command`. That method updates the shared `TreeState` and entity listeners without transmitting. `send` calls the same method only after the official transmit helper succeeds. Existing decoder and burst-filter tests preserve the protocol evidence; the state-transition hook has a regression test proving that it does not transmit. Receiver-based learning and command events can be added alongside the official adapter without changing light or brightness command semantics.
