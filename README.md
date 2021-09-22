This is a companion repo to my post, ["Reverse-engineering the Emporia Vue
2"][post]. If you haven't already seen that, it may provide useful background.

It contains no flash dumps, ELF files, or any other copyrighted material.

Any code written by myself is licensed under the MIT license.

[post]: https://flaviutamas.com/2021/reversing-emporia-vue-2

## Index

- `example_messages.txt`: a dump of messages sent over MQTT. Contains the raw
  I2C payload and the processed data
- `gen_esp32part.py`: tool downloaded [from Espressif][gen_esp32part]
- `i2c data dump.bin`, `i2c dump.bin`: raw I2C captures using a logic analyzer
- `parse_mqtt_dbg.py`: converts MQTT messages into JSON, and then converts them
  into InfluxDB commands and sends them.
- `nvs.json`: a dump of a clean NVS json
- `nvs_new.json`: a modified NVS json
- `nvs_partition_gen.py`: [partition generator tool][nvs_partition_gen] from
  the vendor
- `seriallog.log`: an example dump of the serial output

[gen_esp32part]: https://raw.githubusercontent.com/espressif/esp-idf/master/components/partition_table/gen_esp32part.py
[nvs_partition_gen]: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/nvs_partition_gen.html
