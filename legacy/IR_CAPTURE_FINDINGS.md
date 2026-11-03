# TOTO Washlet IR Capture Findings

These findings came from a live ESPHome IR receiver capture against the Washlet
remote. Codes are written as:

```text
rc_code_1 / rc_code_2 / command
```

## Confirmed Controls

| Control                | Captured code sequence                      | Notes                                                   |
| ---------------------- | ------------------------------------------- | ------------------------------------------------------- |
| Stop                   | `0xA / 0xA / 0xDA`, then `0x0 / 0x0 / 0x00` | Stop consistently sent the `0xDA` prefix before `0x00`. |
| Rear wash              | `0x2 / 0xC / 0x80`                          | Previously stored value was wrong.                      |
| Rear wash soft         | `0x2 / 0xC / 0xA8`                          | Previously stored value was wrong.                      |
| Front wash             | `0x2 / 0xC / 0x40`                          | Previously stored value was wrong.                      |
| Front wash soft        | `0x2 / 0xC / 0x91`                          | Missing from the integration before capture.            |
| Dryer                  | `0x0 / 0x0 / 0xC0`                          | Matches stored value.                                   |
| Deodorize              | `0x0 / 0x0 / 0x7C`                          | Matches stored `POWER_DEODORIZER`.                      |
| Wand clean             | `0x0 / 0x0 / 0x11`                          | Missing from the integration before capture.            |
| Manual nozzle cleaning | `0x0 / 0x0 / 0x74`                          | Missing from the integration before capture.            |
| Manual premist         | `0x0 / 0x0 / 0x59`                          | Missing from the integration before capture.            |
| Lower water            | `0x0 / 0x0 / 0x12`                          | Missing from the integration before capture.            |
| Nozzle up              | `0x0 / 0x2 / 0xA0`                          | Missing from the integration before capture.            |
| Nozzle down            | `0x0 / 0xC / 0xA0`                          | Missing from the integration before capture.            |
| Pulsate                | `0x0 / 0x0 / 0xE0`                          | Matches stored value.                                   |
| Oscillate              | `0x0 / 0x0 / 0x60`, then `0x0 / 0x0 / 0x10` | Stored value only had the first frame.                  |
| Large flush            | `0x0 / 0x0 / 0xB0`                          | Matches stored `FULL_FLUSH`.                            |
| Small flush            | `0x0 / 0x0 / 0x88`                          | Matches stored `LIGHT_FLUSH`.                           |
| Toggle seat            | `0x0 / 0x0 / 0xF6`                          | Matches stored `SEAT_OPEN_CLOSE`.                       |
| Toggle lid             | `0x0 / 0x0 / 0x0E`                          | Matches stored `LID_OPEN_CLOSE`.                        |

## User Profiles

The remote has four user profiles, but selecting later profiles requires stepping
through earlier profiles. These captures should be treated as sequences rather
than independent single commands.

| Profile action | Captured code sequence                                                       | Notes                                      |
| -------------- | ---------------------------------------------------------------------------- | ------------------------------------------ |
| User profile 1 | `0x0 / 0x0 / 0xD5`, then `0x2 / 0x8 / 0x95`, then `0xD / 0x0 / 0x55`         | Confirmed in a full 1 -> 2 -> 3 -> 4 cycle. |
| User profile 2 | `0x4 / 0x0 / 0xD5`, then `0x4 / 0xC / 0x95`, then `0xD / 0x0 / 0x55`         | Confirmed in two full cycles.              |
| User profile 3 | `0xC / 0x0 / 0xD5`, then `0x2 / 0xC / 0x95`, then `0x1 / 0x0 / 0x55`         | Confirmed in two full cycles.              |
| User profile 4 | `0x2 / 0x0 / 0xD5`, then `0x2 / 0xC / 0x95`, then `0x1 / 0x0 / 0x55`         | Confirmed in two full cycles.              |

## Stateful Controls

These controls appear to encode the resulting state or level in `rc_code_1` or
`rc_code_2`. The captures below should not be modeled as simple increase/decrease
buttons without more mapping.

| Control                 | Captured values                                                                                                        | Notes                                                                                         |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Pressure decrease       | `0xC / 0x0 / 0x20`, then `0x4 / 0x0 / 0x20`                                                                            | Pressed twice.                                                                                |
| Pressure increase       | `0xC / 0x0 / 0x20`                                                                                                     | Pressed once.                                                                                 |
| Water temperature       | `0x0 / 0x0 / 0xEC`, `0x8 / 0x0 / 0xEC`, `0xA / 0x0 / 0xEC`, `0x1 / 0x0 / 0xEC`, `0x9 / 0x0 / 0xEC`, `0xD / 0x0 / 0xEC` | Confirmed as off, then levels `1/5` through `5/5`, in both ascending and descending sweeps.     |
| Dryer air temperature   | `0x2 / 0x0 / 0x1C`                                                                                                     | User identified this as level `4/5`.                                                          |
| Seat temperature        | `0x0 / 0x0 / 0xEC`, `0x0 / 0x8 / 0xEC`, `0x0 / 0xA / 0xEC`, `0x0 / 0x1 / 0xEC`, `0x0 / 0x9 / 0xEC`, `0x0 / 0xD / 0xEC` | Confirmed as off, then levels `1/5` through `5/5`, in both ascending and descending sweeps.     |

## Settings And Automation Controls

| Control                | Captured code        | Notes                                                                                                                                             |
| ---------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Auto energy saver      | `0x0 / 0x0 / 0x34`   | Confirmed.                                                                                                                                        |
| Auto energy saver+     | `0x0 / 0x0 / 0x2A`   | Confirmed.                                                                                                                                        |
| Auto energy saver off  | `0x0 / 0x0 / 0xB4`   | Label was tentative during capture, but it did transmit.                                                                                          |
| Timer energy saver 6   | `0x6 / 0x0 / 0x68`   | Confirmed.                                                                                                                                        |
| Timer energy saver 9   | `0x9 / 0x0 / 0x68`   | Confirmed after cycling through off and 6 hours first.                                                                                             |
| Timer energy saver off | `0x0 / 0x0 / 0x68`   | Confirmed.                                                                                                                                        |
| Auto lid open off      | `0x0 / 0x0 / 0x5C`   | Confirmed.                                                                                                                                        |
| Auto lid open on       | `0x0 / 0x0 / 0x9C`   | Confirmed.                                                                                                                                        |
| Auto flush off         | `0x0 / 0x0 / 0x3C`   | Confirmed.                                                                                                                                        |
| Auto flush on          | `0x0 / 0x0 / 0xDC`   | Confirmed.                                                                                                                                        |
| Close lid before flushing on  | `0x4 / 0x0 / 0x66` | Confirmed on S7A. The manual calls the same model-dependent setting "Auto flush lid relation" on S7. |
| Close lid before flushing off | `0x8 / 0x0 / 0x66` | Confirmed on S7A. The manual calls the same model-dependent setting "Auto flush lid relation" on S7. |
| Mystery button         | `0x0 / 0x0 / 0x3D`   | Function unknown.                                                                                                                                 |

## Buttons With No IR Decode

These buttons produced no `remote.toto` decode during the capture attempts:

- Power
- Settings

## Follow-Up Capture Targets

- Map all dryer air temperature levels.
