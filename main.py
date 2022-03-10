import asyncio
import time
import json
import paho.mqtt.client as mqtt

from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.client import OverkizClient
from pyoverkiz.models import Device, Command

from const import *

devices: list[Device]
updateAll = False
command_queue = []
mqclient = mqtt.Client()
somfyClient: OverkizClient


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQ_MAIN_TOPIC)

    somfy_include_all()

    global updateAll
    updateAll = True


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

    if msg.topic == MQ_MAIN_TOPIC:
        global updateAll
        updateAll = True
    else:
        exterior_screen_count = 0
        for device in devices:
            if device.ui_class == "ExteriorScreen":
                exterior_screen_count = exterior_screen_count + 1
                command_topic = f"pt:j1/mt:cmd/rt:dev/rn:somfy/ad:1/sv:out_lvl_switch/ad:e{exterior_screen_count}_0"
                if msg.topic == command_topic:
                    payload = json.loads(msg.payload)
                    closure_state = 100 - int(payload["val"])
                    command_queue.append((device.device_url, Command("setPosition", [closure_state])))


async def main() -> None:
    await somfy_init()
    await mq_init()
    await somfy_listen()


async def mq_init() -> None:
    mqclient.on_connect = on_connect
    mqclient.on_message = on_message

    mqclient.loop_start()
    mqclient.username_pw_set(MQ_USERNAME, MQ_PASSWORD)
    mqclient.connect(MQ_ADDRESS, MQ_PORT, 60)


async def somfy_init() -> None:
    global somfyClient
    somfyClient = OverkizClient(SOMFY_USERNAME, SOMFY_PASSWORD, server=SUPPORTED_SERVERS["somfy_europe"])
    await somfyClient.login()

    global devices
    devices = await somfyClient.get_devices()


def somfy_include_all() -> None:
    topic = "pt:j1/mt:evt/rt:ad/rn:somfy/ad:1"
    exterior_screen_count = 0
    light_sensor_count = 0

    for device in devices:
        print(f"{device.label} ({device.id}) - {device.controllable_name}")
        print(f"{device.widget} - {device.ui_class}")

        if device.ui_class == "ExteriorScreen":
            exterior_screen_count = exterior_screen_count + 1
            event_topic = f"/rt:dev/rn:somfy/ad:1/sv:out_lvl_switch/ad:e{exterior_screen_count}_0"
            mqclient.subscribe("pt:j1/mt:cmd"+event_topic)

            mqclient.publish(topic, payload=json.dumps({
                  "serv": "somfy",
                  "type": "evt.thing.inclusion_report",
                  "val_t": "object",
                  "val": {
                    "address": f"e{exterior_screen_count}",
                    "product_hash": device.controllable_name,
                    "comm_tech": "somfy",
                    "product_name": device.label,
                    "manufacturer_id": "Somfy",
                    "hw_ver": "1",
                    "is_sensor": "0",
                    "power_source": "ac",
                    "services": [
                      {
                        "name": "out_lvl_switch",
                        "alias": "Light control",
                        "address": event_topic,
                        "enabled": True,
                        "groups": [
                          "ch_0"
                        ],
                        "props": {
                          "max_lvl": 100,
                          "min_lvl": 0
                        },
                        "interfaces": [
                          {
                            "intf_t": "in",
                            "msg_t": "cmd.binary.set",
                            "val_t": "bool",
                            "ver": "1"
                          },
                          {
                            "intf_t": "in",
                            "msg_t": "cmd.lvl.set",
                            "val_t": "int",
                            "ver": "1"
                          },
                          {
                            "intf_t": "in",
                            "msg_t": "cmd.lvl.start",
                            "val_t": "string",
                            "ver": "1"
                          },
                          {
                            "intf_t": "in",
                            "msg_t": "cmd.lvl.stop",
                            "val_t": "null",
                            "ver": "1"
                          },
                          {
                            "intf_t": "out",
                            "msg_t": "evt.lvl.report",
                            "val_t": "int",
                            "ver": "1"
                          },
                          {
                            "intf_t": "out",
                            "msg_t": "evt.binary.report",
                            "val_t": "bool",
                            "ver": "1"
                          }
                        ]
                      }
                    ]
                  },
                  "src": "fh-somfy",
                  "ver": "1",
                  "uid": device.id,
                  "topic": "pt:j1/mt:evt/rt:ad/rn:somfy/ad:1"
            }))
        elif device.ui_class == "LightSensor":
            light_sensor_count = light_sensor_count + 1
            event_topic = f"/rt:dev/rn:somfy/ad:1/sv:sensor_lumin/ad:s{light_sensor_count}_0"

            mqclient.publish(topic, payload=json.dumps({
                "serv": "somfy",
                "type": "evt.thing.inclusion_report",
                "val_t": "object",
                "val": {
                    "address": f"s{light_sensor_count}",
                    "product_hash": device.controllable_name,
                    "comm_tech": "somfy",
                    "product_name": device.label,
                    "manufacturer_id": "Somfy",
                    "hw_ver": "1",
                    "is_sensor": "0",
                    "power_source": "battery",
                    "services": [
                        {
                            "name": "sensor_lumin",
                            "address": event_topic,
                            "interfaces": [
                                {"intf_t": "out", "msg_t": "evt.sensor.report", "ver": "1", "val_t": "float"},
                                {"intf_t": "in", "msg_t": "cmd.sensor.get", "ver": "1", "val_t": "null"}
                            ],
                            "groups": ["ch1"]
                        }
                    ]
                },
                "src": "fh-somfy",
                "ver": "1",
                "uid": device.id,
                "topic": "pt:j1/mt:evt/rt:ad/rn:somfy/ad:1"
            }))


async def somfy_update_all() -> None:
    global updateAll
    updateAll = False

    exterior_screen_count = 0
    light_sensor_count = 0

    for device in devices:
        print(f"{device.label} ({device.id}) - {device.controllable_name}")
        print(f"{device.widget} - {device.ui_class}")

        if device.ui_class == "ExteriorScreen":
            exterior_screen_count = exterior_screen_count + 1
            states = await somfyClient.get_state(device.device_url)
            closure_state = next(filter(lambda s: s.name == "core:ClosureState", states))
            print(closure_state.value)
            topic = f"pt:j1/mt:evt/rt:dev/rn:somfy/ad:1/sv:out_lvl_switch/ad:e{exterior_screen_count}_0"

            mqclient.publish(topic, payload=json.dumps({
                "type": "cmd.lvl.report",
                "serv": "out_lvl_switch",
                "val_t": "int",
                "val": 100 - closure_state.value,
                "props": {},
                "ver": "1",
                "src": "fh_somfy",
            }))
        elif device.ui_class == "LightSensor":
            light_sensor_count = light_sensor_count + 1
            states = await somfyClient.get_state(device.device_url)
            luminance_state = next(filter(lambda s: s.name == "core:LuminanceState", states))
            topic = f"pt:j1/mt:evt/rt:dev/rn:somfy/ad:1/sv:sensor_lumin/ad:s{light_sensor_count}_0"

            mqclient.publish(topic, payload=json.dumps({
                "type": "evt.sensor.report",
                "serv": "sensor_lumin",
                "val_t": "float",
                "val": luminance_state.value,
                "props": {
                    "unit": "Lux"
                },
                "ver": "1"
            }))


async def somfy_listen() -> None:
    async with somfyClient as client:
        while True:
            if updateAll:
                await somfy_update_all()
            for command in list(command_queue):
                command_queue.remove(command)
                await somfyClient.execute_command(command[0], command[1])
            events = await client.fetch_events()
            print(events)
            for event in events:
                print(event.name)
                if event.name == "DeviceStateChangedEvent":
                    print(event.device_url)
                    await somfy_update_all()
            time.sleep(2)

asyncio.run(main())
