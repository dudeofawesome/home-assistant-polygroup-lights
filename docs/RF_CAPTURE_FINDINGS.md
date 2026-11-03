# Polygroup RF evidence and hardware validation

## Confirmed inputs

User photos identify a PDR-053-29V wired controller and Polygroup PDT-015-14 (053/056) remote, FCC ID 2A62O-PDT015TS. The remote has 11 effect buttons, On/Off, Timer, and Brightness. The wired controller has brightness minus/plus and an unlabeled central button. Timer is excluded at the user's request. The remote's printed bracket connects Brightness to Clear Steady, Color Steady, and Clear/Color Alt.

The supplied handoff records successful reception using a Waveshare ESP32-C6-Zero and CC1101 at 433.895 MHz ASK/OOK over OpenThread. It contains one On/Off capture; all other codes, independent-press stability, transmission, and native proxy operation remain unverified. Its proposed firmware is not a validated installed configuration.

## Frame representation

The complete captured On/Off frame decodes MSB first as `807FFF00`, using a roughly 9000/-5350 microsecond header, 900 microsecond marks, -540 zero spaces, -1600 one spaces, and a trailing 900/-9000 mark/gap. `tests/test_commands.py` preserves the measured timings independently of the encoder. This is a raw pulse-distance representation, not evidence of NEC compatibility. Unknown pre-header 1000/-1000 activity was omitted from the candidate waveform and may matter if transmission fails.

No code is installed as a default: learning captures each remote's actual code. The decoder accepts complete 32-bit frames with timing tolerance and ignores unrelated timings. It can extract repeated frames from one signal or separate callbacks. A 200ms gap separates same-code bursts; very rapid independent presses or unusual long holds need hardware testing. Transmission uses three repeats after the initial frame. Capturing packets does not establish that the controller accepts that replay.

## Required checks on hardware

1. Inspect the actual ESPHome configuration and installed Home Assistant/ESPHome versions. Preserve Thread and secret references; do not reuse the copied bathroom IR proxy address or credentials. No USB serial proxy was present during development.
2. Verify that Home Assistant exposes an RF transmitter and receiver and the native subscription API. The current pinned test release supports RF transmission only. The integration aborts cleanly on that release; tests inject the documented receive callback contract, not real receiver hardware.
3. Learn On/Off with `polygroup_lights.learn_command`, replay it, and confirm one toggle per action. If replay fails, compare the whole recorded waveform, including possible wake-up preamble and repetition behavior.
4. Learn each of the 11 effect buttons and Brightness, checking multiple independent presses for stable codes. Pressing a learned physical button must update the light once and fire one Remote command event for a burst. Verify receive coverage, local echoes, long holds, and rapid presses.
5. Synchronize observed power and effect, then compare HA and remote actions. Selecting an effect records that effect without assuming it powers on an off tree. Verify whether effect or power changes reset brightness before enabling calibrated brightness.
6. Count brightness levels in each of the three bracketed modes, verify cycle direction and wraparound, and enter measured percentages in options. Synchronize the current index; compare remote and slider updates. Wired controller presses require manual resynchronization unless RF reception from that controller is separately demonstrated.

The timer function is intentionally absent. Automatic changes by an enabled hardware timer cannot be inferred from remote RF commands; disable that timer for Home Assistant scheduling.
