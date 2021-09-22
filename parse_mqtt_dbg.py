#!/usr/bin/env python3
import base64
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


@dataclass
class MessageVoltageReading:
    phase: int
    voltage: float
    frequency_hz: float
    offset_degrees: float

    unknown_1: int
    unknown_2: float


@dataclass
class MessageCurrentReading:
    channel: int
    current_amps: float
    power_watts: [float, float, float]


@dataclass
class Vue2Message:
    sensor_id: str
    # time the measurement was taken
    time: datetime

    # the i2c data data packet received from the mcu
    raw_data: bytes

    voltage_readings: list[MessageVoltageReading]
    current_readings: list[MessageCurrentReading]


example_message = """\
id: A2035A04B4B8F009841CC8, t: 1627512531
039952C23E580000ABC5FFFF30F9FFFF
19C4FFFFE3E100002FFDFFFFC5080300
F345FEFFDC9BFFFF52070000EAECFFFF
D6FFFFFF97FCFFFF24060000F5FFFFFF
1B040000DDFFFFFFFAFFFFFFB9E90000
DC53FFFF63ECFFFF4109000084F8FFFF
41FFFFFF830300007705000076FFFFFF
4705000018F9FFFF45FFFFFF6A100000
816000007EFCFFFF4DF402002639FEFF
51A9FFFF833BFFFF85D6020064F8FFFF
09000000AFFDFFFFD0FFFFFF931F0000
53FBFFFF34FEFFFFE3710000E5B6FFFF
07F9FFFF6603000052F3FFFF7FFFFFFF
430D0000E103000041FFFFFF7C220000
A9E1FFFF2BFDFFFF7A14DE158201A701
8E000000FD0093000050500044005100
14016700630058007200035099013200
2D004E003B00450046000000
V1: 120.2, 61.4 Hz, 5242, 0.0229308
V2: 121.8, 120 degrees, 5598, 0.0217630
V3:   8.5, 0 degrees, 386, 0.0220000
I01:    4.6, P[V1]:    94.2, P[V2]:   -59.1, P[V3]:    -7.0
I02:    2.7, P[V1]:   -63.9, P[V2]:   228.8, P[V3]:    -2.9
I03:  372.4, P[V1]:   829.1, P[V2]:  -447.8, P[V3]:  -102.5
I04:    0.4, P[V1]:     2.0, P[V2]:    -4.8, P[V3]:    -0.0
I05:    0.3, P[V1]:    -0.9, P[V2]:     1.6, P[V3]:    -0.0
I06:    0.4, P[V1]:     1.1, P[V2]:    -0.0, P[V3]:    -0.0
I07:    1.3, P[V1]:    62.4, P[V2]:   -43.6, P[V3]:    -5.0
I08:    0.5, P[V1]:     2.5, P[V2]:    -1.9, P[V3]:    -0.2
I09:    0.5, P[V1]:     0.9, P[V2]:     1.4, P[V3]:    -0.1
I10:    0.4, P[V1]:     1.4, P[V2]:    -1.7, P[V3]:    -0.2
I11:    0.5, P[V1]:     4.4, P[V2]:    24.4, P[V3]:    -0.9
I12:   93.1, P[V1]:   201.8, P[V2]:  -115.2, P[V3]:   -22.2
I13:    1.9, P[V1]:   -52.4, P[V2]:   184.0, P[V3]:    -1.9
I14:    0.2, P[V1]:     0.0, P[V2]:    -0.6, P[V3]:    -0.0
I15:    0.2, P[V1]:     8.4, P[V2]:    -1.2, P[V3]:    -0.5
I16:    0.4, P[V1]:    30.4, P[V2]:   -18.5, P[V3]:    -1.8
I17:    0.3, P[V1]:     0.9, P[V2]:    -3.2, P[V3]:    -0.1
I18:    0.3, P[V1]:     3.5, P[V2]:     1.0, P[V3]:    -0.2
I19:    0.3, P[V1]:     9.2, P[V2]:    -7.7, P[V3]:    -0.7
"""

ID_TIME_REGEX = re.compile(r"id: (?P<id>[A-F0-9]+), t: (?P<time>\d+)",
                           flags=re.MULTILINE)
RAW_BYTES_REGEX = re.compile(r"^[A-F0-9]{16,}$", flags=re.MULTILINE)
PHASE_1_VOLTS_REGEX = re.compile(
    r"V(?P<phase>\d):\s*(?P<voltage>\d+\.\d+), (?P<frequency>\d+\.\d+) Hz, (?P<unk1>\d+), (?P<unk2>\d+\.\d+)",
    flags=re.MULTILINE)
PHASES_VOLTS_REGEX = re.compile(
    r"V(?P<phase>\d):\s*(?P<voltage>\d+\.\d+), (?P<offset>\d+) degrees, (?P<unk1>\d+), (?P<unk2>\d+\.\d+)",
    flags=re.MULTILINE)
CURRENT_REGEX = re.compile(
    r"I(?P<ch>\d+):\s*(?P<current>-?\d+\.\d+), P\[V1\]:\s*(?P<pwr1>-?\d+\.\d+), P\[V2\]:\s*(?P<pwr2>-?\d+\.\d+), P\[V3\]:\s*(?P<pwr3>-?\d+\.\d+)",
    flags=re.MULTILINE)


def parse_message(msg):
    id_and_time = ID_TIME_REGEX.search(msg)

    if not id_and_time:
        raise ValueError("message missing id and measurement time")

    id_ = id_and_time["id"]
    time = datetime.fromtimestamp(int(id_and_time["time"]))

    raw_data = bytes.fromhex("".join(RAW_BYTES_REGEX.findall(msg)))

    voltage_readings = []

    for match in PHASE_1_VOLTS_REGEX.finditer(msg):
        frequency = float(match["frequency"])
        voltage_readings.append(MessageVoltageReading(
            phase=int(match["phase"]),
            voltage=float(match["voltage"]),
            frequency_hz=frequency,
            offset_degrees=0.0,
            unknown_1=int(match["unk1"]),
            unknown_2=float(match["unk2"]),
        ))
        break
    else:
        raise ValueError("message missing V1 line")

    for match in PHASES_VOLTS_REGEX.finditer(msg):
        voltage_readings.append(MessageVoltageReading(
            phase=int(match["phase"]),
            voltage=float(match["voltage"]),
            frequency_hz=frequency,
            offset_degrees=float(match["offset"]),
            unknown_1=int(match["unk1"]),
            unknown_2=float(match["unk2"]),
        ))

    current_readings = [MessageCurrentReading(
        channel=int(match["ch"]),
        current_amps=float(match["current"]),
        power_watts=[float(match["pwr1"]), float(match["pwr2"]), float(match["pwr3"])],
    ) for match in CURRENT_REGEX.finditer(msg)]

    return Vue2Message(
        id_, time, raw_data, voltage_readings, current_readings
    )


@dataclass
class PhaseReading:
    phase: int  # 1, 2, 3

    voltage: float
    current: float
    power: float

    frequency: float
    offset: float


@dataclass
class CircuitReading:
    channel: int

    power: float
    current: float


@dataclass
class Vue2Reading:
    sensor_id: str
    # time the measurement was taken
    time: datetime

    phases: [PhaseReading, Optional[PhaseReading], Optional[PhaseReading]]
    circuits: list[CircuitReading]


@dataclass
class ChannelConfiguration:
    channel: int
    phase: int
    multiplier: float


@dataclass
class Configuration:
    enabled_phases: list[int]
    channel_config: list[ChannelConfiguration]


def process_message(msg: Vue2Message, conf: Configuration) -> Vue2Reading:
    if not conf.enabled_phases:
        raise ValueError("Must have at least one phase enabled")

    phases = []

    for reading in msg.voltage_readings:
        if reading.phase not in conf.enabled_phases:
            continue

        phase_current = next(
            filter(lambda v: v.channel == reading.phase, msg.current_readings))
        phases.append(PhaseReading(
            phase=reading.phase,
            voltage=reading.voltage,
            frequency=reading.frequency_hz,
            offset=reading.offset_degrees,
            current=phase_current.current_amps,
            power=phase_current.power_watts[reading.phase - 1]
        ))

    circuits = []
    for reading in msg.current_readings:
        if reading.channel in {1, 2, 3}:
            # this is one of the phase current readings
            continue

        channel_conf = next(
            filter(lambda cc: cc.channel == (reading.channel - 3), conf.channel_config))

        if not channel_conf:
            # this channel isn't in the config, ignore
            continue

        phase_info = phases[channel_conf.phase - 1]
        circuits.append(CircuitReading(
            channel=reading.channel - 3,
            power=reading.power_watts[phase_info.phase - 1] * channel_conf.multiplier,
            current=reading.current_amps * channel_conf.multiplier,
        ))

    return Vue2Reading(
        sensor_id=msg.sensor_id,
        time=msg.time,
        phases=phases,
        circuits=circuits
    )


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode('ascii')
    return obj.__dict__


def main(args):
    if len(args) < 2:
        print(f"{args[0]} <mqtt_input> <json_output>")
        print("")
        print(f"  mqtt_input: source of mqtt messages. may be /dev/stdin")
        print(f"      tip, try mosquitto_sub -h ... -t prod/minions/emporia/ct/v1/.../debug/v2")
        return 1

    token = "<snip>"
    org = "home"
    bucket = "home_automation"

    client = InfluxDBClient(url="http://localhost:8086", token=token)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    with open(args[1], 'r') as inf:
        message = ''

        for line in inf:
            message += line
            if line == '\n':
                parsed_message = parse_message(message)
                line = json.dumps(process_message(parsed_message, Configuration(
                    enabled_phases=[1, 2],
                    channel_config=[
                        ChannelConfiguration(channel=1, phase=1, multiplier=1),
                        ChannelConfiguration(channel=2, phase=2, multiplier=1),
                        ChannelConfiguration(channel=3, phase=1, multiplier=1),
                        ChannelConfiguration(channel=4, phase=1, multiplier=1),
                        ChannelConfiguration(channel=5, phase=1, multiplier=2),
                        ChannelConfiguration(channel=6, phase=1, multiplier=2),
                        ChannelConfiguration(channel=7, phase=1, multiplier=2),
                        ChannelConfiguration(channel=8, phase=2, multiplier=1),
                        ChannelConfiguration(channel=9, phase=2, multiplier=1),
                        ChannelConfiguration(channel=10, phase=2, multiplier=1),
                        ChannelConfiguration(channel=11, phase=1, multiplier=2),
                        ChannelConfiguration(channel=12, phase=1, multiplier=2),
                        ChannelConfiguration(channel=13, phase=1, multiplier=1),
                        ChannelConfiguration(channel=14, phase=1, multiplier=1),
                        ChannelConfiguration(channel=15, phase=2, multiplier=1),
                        ChannelConfiguration(channel=16, phase=1, multiplier=1),
                    ]
                )), default=json_serializer)
                message = ''

                batch = []
                data = json.loads(line)
                timestamp = int(datetime.fromisoformat(data["time"]).replace(tzinfo=ZoneInfo("America/New_York")).timestamp()) * 1000000000
                for phase in data['phases']:
                    batch.append(f"home_power,phase={phase['phase']} current={phase['current']},power={phase['power']},voltage={phase['voltage']},frequency={phase['frequency']} {timestamp}")
                for circuit in data['circuits']:
                    batch.append(f"home_power,circuit={circuit['channel']} current={circuit['current']},power={circuit['power']} {timestamp}")

                write_api.write(bucket, org, batch)
                print("\n".join(batch))



if __name__ == '__main__':
    sys.exit(main(sys.argv))

# https://discord.com/channels/330944238910963714/554842238073700352/870152674660737035;
