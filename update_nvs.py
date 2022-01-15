import base64
import json
import subprocess
import sys
import tempfile

import nvsjson2csv

ESPTOOL_PARAMS = ["esptool.py", "--port", "/dev/ttyUSB1", "--chip", "esp32", "-b",
                  "921600"]


def main(args):
    dump_nvs = subprocess.run([
        "python3", "esp32_image_parser/esp32_image_parser.py", "dump_nvs",
        args[1],
        "-partition", "nvs",
        "-nvs_output_type", "json"
    ], capture_output=True, text=True)

    nvs_pages = nvsjson2csv.load_nvsjson(json.loads(dump_nvs.stdout))
    nvs_entries = nvsjson2csv.get_entries(nvs_pages)
    nvs_entries = nvsjson2csv.set_entry(nvsjson2csv.Entry(
        ns_name="storage",
        key="ssid",
        typ="BLOB_DATA",
        data=base64.b64encode(b'NEW_SSID').decode(),
    ), nvs_entries)
    nvs_entries = nvsjson2csv.set_entry(nvsjson2csv.Entry(
        ns_name="storage",
        key="password",
        typ="BLOB_DATA",
        data=base64.b64encode(b'NEW_PASSWORD').decode(),
    ), nvs_entries)
    with tempfile.NamedTemporaryFile(mode='wt') as csv_file, \
            tempfile.NamedTemporaryFile(mode='wb', suffix='.bin') as bin_file:
        nvsjson2csv.nvsjson_to_csv(nvs_entries, csv_file)
        csv_file.flush()

        subprocess.run([
            "python3", "nvs_partition_gen.py", "generate",
            csv_file.name, bin_file.name,
            str(327680),
        ])

        subprocess.run(ESPTOOL_PARAMS + [
            "erase_region", str(0x9000), str(327680),
        ])

        input("Reset ESP32 & press Enter to continue...")

        subprocess.run(ESPTOOL_PARAMS + [
            "write_flash", str(0x9000), bin_file.name,
        ])


if __name__ == '__main__':
    main(sys.argv)
