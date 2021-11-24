The sensor data coming over the I2C connection includes all of the information to measure the amount of power the individual circuits are comsuming. It consists of a short header, power and current information for all nineteen sensors, and AC voltage/frequency information.

## Overview

The information is encoded little-endian, and is a total of 284 bytes. The diagram below is a to-scale overview of a message received from the sensor.

```
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0000 | Header        | Power data                                    |
       +-+-+-+-+-+-+-+-+                                               +
0x0010 |                                                               |
       +                                                               +
0x0020 |                                                               |
       +                                                               +
0x0030 |                                                               |
       +                                                               +
0x0040 |                                                               |
       +                                                               +
0x0050 |                                                               |
       +                                                               +
0x0060 |                                                               |
       +                                                               +
0x0070 |                                                               |
       +                                                               +
0x0080 |                                                               |
       +                                                               +
0x0090 |                                                               |
       +                                                               +
0x00A0 |                                                               |
       +                                                               +
0x00B0 |                                                               |
       +                                                               +
0x00C0 |                                                               |
       +                                                               +
0x00D0 |                                                               |
       +                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00E0 |                               | AC data                       |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00F0 |AC data (cont.)| Current data                                  |
       +-+-+-+-+-+-+-+-+                                               +
0x0100 |                                                               |
       +                                       +-+-+-+-+-+-+-+-+-+-+-+-+
0x0110 |                                       | End   |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field        | Size      | Description                                   |
| ------------ | --------- | --------------------------------------------- |
| Header       | 4 bytes   | Metadata about the message                    |
| Power data   | 228 bytes | Calculated power draw for each of the sensors |
| AC data      | 12 bytes  | Measured AC voltage, frequency and period     |
| Current data | 38 bytes  | Measured current data from CT sensors         |
| End          | 2 bytes   | Marks the end of the message                  |

## Header

The message header contains a version, and some other information that doesn't seem relevant to sensor data. It's a total of 4 bytes.

```
       +-+-+-+-+-+-+-+-+
0x0000 |Ver|Sum|Unk|Cnt|
       +-+-+-+-+-+-+-+-+
```

| Field    | Size   | Type     | Description                          |
| -------- | ------ | -------- | ------------------------------------ |
| Version  | 1 byte | `uint8`  | Version of the message (always 3)    |
| Checksum | 1 byte | `binary` | Checksum of the message (unverified) |
| Unknown  | 1 byte |          | Has an unknown meaning (always 82)   |
| Counter  | 1 byte | `uint8`  | An unknown incrementing counter      |

## Power data

The power data includes power information, watts, for each of the CT clamp sensors and for each of the three phases. Presumably, it is calculated using the AC data and the current data. There are 19 sensors, with 12 bytes used for each sensor for a total size of 228 bytes.

```
                       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                0x0004 | Input 1 Power                                 |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0010 | Input 2 Power                                 | Input 3 Power |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0020 | Input 3 Power (cont.)         | Input 4 Power                 |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0030 |Input 4 (cont.)| Input 5 Power                                 |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0040 | Input 6 Power                                 | Input 7 Power |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0050 | Input 7 Power (cont.)         | Input 8 Power                 |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0060 |Input 8 (cont.)| Input 9 Power                                 |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0070 | Input 10 Power                                |Input 11 Power |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0080 | Input 11 Power (cont.)        | Input 12 Power                |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0090 |Input 12(cont.)| Input 13 Power                                |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00A0 | Input 14 Power                                |Input 15 Power |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00B0 | Input 15 Power (cont.)        | Input 16 Power                |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00C0 |Input 16(cont.)| Input 17 Power                                |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00D0 | Input 18 Power                                |Input 19 Power |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00E0 | Input 19 Power (cont.)        |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

The power data for each sensor consists of three values, a watt calculation for each phase of the AC power.

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Power (phase 1)|Power (phase 2)|Power (phase 3)|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field           | Size    | Type    | Description                  |
| --------------- | ------- | ------- | ---------------------------- |
| Power (phase 1) | 4 bytes | `int32` | Power calculated for phase 1 |
| Power (phase 2) | 4 bytes | `int32` | Power calculated for phase 2 |
| Power (phase 3) | 4 bytes | `int32` | Power calculated for phase 3 |

## AC data

The AC data includes voltage and phase information for the AC electricity, which is needed to calculate power usage.

```
                                       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                0x00E8 | Ph1 V | Ph2 V | Ph3 V | Freq. |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x00F0 |Ph2 deg|Ph3 deg|
       +-+-+-+-+-+-+-+-+
```

| Field           | Size    | Type     | Description                        |
| --------------- | ------- | -------- | ---------------------------------- |
| Phase 1 Voltage | 2 bytes | `uint16` | AC voltage measured for phase 1    |
| Phase 2 Voltage | 2 bytes | `uint16` | AC voltage measured for phase 2    |
| Phase 3 Voltage | 2 bytes | `uint16` | AC voltage measured for phase 3    |
| Freqency (Hz)   | 2 bytes | `uint16` | AC frequency measured (all phases) |
| Phase 2 degrees | 2 bytes | `uint16` | Degrees from phase 1 of phase 2    |
| Phase 3 degrees | 2 bytes | `uint16` | Degrees from phase 1 of phase 3    |

## Current data

The current data contains the measured current (A) through each of the 19 sensors.

```
                       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                0x00F4 | In1 I | In2 I | In3 I | In4 I | In5 I | In6 I |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0100 | In7 I | In8 I | In9 I |In10 I |In11 I |In12 I |In13 I |In14 I |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
0x0110 |In15 I |In16 I |In17 I |In18 I |In19 I |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

The current data for each sensor consists of a single value, the meaured current.

| Field   | Size    | Type     | Description                    |
| ------- | ------- | -------- | ------------------------------ |
| Current | 2 bytes | `uint16` | Current measured for the input |
