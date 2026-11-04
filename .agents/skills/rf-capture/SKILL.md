---
name: rf-capture
description: Use when capturing live RF codes, especially to add new buttons, enum values, or received-command events
---

1. Use Kubernetes MCP to find the current ESPHome pod in namespace `esphome`.
2. Use `pods_exec` to run `esphome logs /config/christmas-tree.yaml` while the user presses remote buttons.

Preserve raw RF captures and remove temporary scratch files.
