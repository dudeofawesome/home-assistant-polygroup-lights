---
name: rf-capture
description: Use when capturing live RF codes, especially to add new buttons, enum values, or received-command events
---

Captures live RF codes from an ESPHome RF device.

## Process

1. check if usbserial device available ie: /dev/cu.usbserial-0001
   - if available use `pio device monitor -p /dev/cu.usbserial-0001 -b 115200` (needs interactive terminal)
   - otherwise try connecting remotely
     1. create minimal config: `./scripts/gen-minimal-config.sh /tmp/washlet-proxy-config.yaml`
     2. watch the logs: `esphome logs --device 10.0.16.10 /tmp/washlet-proxy-config.yaml`
2. consider filtering logs with something like `grep -iE 'remote|ir|receiver'`
   - custom_components/toto_washlet/commands.py contains codes that are already known
3. Remove temporary capture logs, scratch files
