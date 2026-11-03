This is a custom Home Assistant integration for Polygroup Christmas tree lights, targeting the PDR-053-29V controller and PDT-015-14 (053/056) RF remote.

The remote uses 433.895 MHz OOK RF through an ESPHome CC1101 proxy. Require both a transmitter and receiver; received remote commands must update the same state used by Home Assistant actions. Suppress RF burst repeats and transmission echoes before applying toggle commands. Do not invent unverified codes, brightness levels, or feedback from the tree. Timer control is out of scope.

See `docs/RF_CAPTURE_FINDINGS.md` for capture evidence and remaining hardware verification. The `legacy/` directory preserves the copied Washlet integration for reference and is not installed or tested as the active integration.

Use the [native Home Assistant RF API](https://contributors.home-assistant.io/core/entities/radio-frequency/). The pinned development HA release lacks RF receive helpers; integration tests inject their documented callback contract. Verify against a receiver-capable runtime before deployment.

Run non-basic commands from inside the devenv (`devenv shell --quiet -- {command}`), which will not work in Codex's sandbox.
