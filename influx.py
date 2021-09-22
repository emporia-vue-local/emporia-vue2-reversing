from datetime import datetime
from zoneinfo import ZoneInfo
import json

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate a Token from the "Tokens Tab" in the UI
token = "<snip>"
org = "home"
bucket = "home_automation"

client = InfluxDBClient(url="http://localhost:8086", token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)

batch = []

try:
    for i, line in enumerate(open('logs.json')):
        data = json.loads(line)
        timestamp = int(datetime.fromisoformat(data["time"]).replace(tzinfo=ZoneInfo("America/New_York")).timestamp()) * 1000000000
        for phase in data['phases']:
            batch.append(f"home_power,phase={phase['phase']} current={phase['current']},power={phase['power']},voltage={phase['voltage']},frequency={phase['frequency']} {timestamp}")
        for circuit in data['circuits']:
            batch.append(f"home_power,circuit={circuit['channel'] - 3} current={circuit['current']},power={circuit['power']} {timestamp}")

        if len(batch) > 2000:
            write_api.write(bucket, org, batch)
            batch = []
        print(i)
finally:
    write_api.write(bucket, org, batch)
