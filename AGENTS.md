This is a custom Home Assistant integration for Polygroup Christmas tree lights, targeting the PDR-053-29V controller and PDT-015-14 (053/056) RF remote.

The remote uses 433.895 MHz OOK RF through an ESPHome CC1101 proxy. The integration currently transmits only; do not add workarounds for missing receive APIs or firmware event forwarding. Remote reception and in-app learning are deferred until the official Home Assistant RF receiver API and ESPHome adapter are available. Do not invent unverified codes, brightness levels, or feedback from the tree. Timer control is out of scope.

See `docs/RF_CAPTURE_FINDINGS.md` for capture evidence and remaining hardware verification. The `legacy/` directory preserves the copied Washlet integration for reference and is not installed or tested as the active integration.

Use the native Home Assistant RF transmit API. Keep command bindings, RF transport, and state transitions separate. Successful transmissions call `TreeController.apply_command`; future official reception should decode and deduplicate frames, then call the same hook without retransmitting. Keep the raw decoder and burst filter independent of Home Assistant receiver APIs. Existing saved command bindings must survive removal of receiver settings.

Supported model codes belong in `commands.VERIFIED_CODES` after hardware verification. Do not require users to learn or manually enter RF codes. Preserve existing saved bindings for compatibility, but expose no manual code-setting action.

Run non-basic commands from inside the devenv (`devenv shell --quiet -- {command}`), which will not work in Codex's sandbox.
