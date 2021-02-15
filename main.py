from mqtt_as import MQTTClient, config
import uasyncio as asyncio
from config import *
import json
import ubinascii
from controll import get_state, init, command

# Subscription callback
def sub_cb(topic, msg, retained):
    print((topic, msg, retained))
    if topic == b"homeassistant/climate/{}/command".format(mac):
        command(msg.decode())
        loop.create_task(publish_status())

async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe("homeassistant/climate/{}/command".format(mac), 1)

async def mqtt():
    while not client.isconnected():
        try:
            await client.connect()
        except OSError as e:
            print('Connection failed.')
            print(e)
            print('retrying in 10 sec')
            await asyncio.sleep(10)
            
    while True:
        await asyncio.sleep(5)
        await client.publish('homeassistant/climate/{}/config'.format(mac), json.dumps({
            "~": "homeassistant/climate/{}".format(mac),
            "name": "Winefridge Upper Compartment",
            "min_temp": 5,
            "max_temp": 20,
            "temp_step": 0.5,
            "temp_unit": "C",
            "modes":["off", "cool"],
            
            "mode_cmd_t": "~/command",
            "mode_cmd_tpl": "mode:{{ value }}",
            
            "mode_stat_t": "~/state",
            "mode_stat_tpl": "{{ value_json.mode }}",
            
            "temp_cmd_t": "~/command",
            "temp_cmd_tpl": "target:{{ value }}",
            
            "temp_stat_t": "~/state",
            "temp_stat_tpl": "{{ value_json.target_temp }}",
            
            "curr_temp_t": "~/state",
            "curr_temp_tpl": "{{ value_json.current_temp }}",
        }))
        await publish_status()

async def publish_status():
    await client.publish('homeassistant/climate/{}/state'.format(mac), json.dumps(get_state()))

# Define configuration
config['subs_cb'] = sub_cb
config['wifi_coro'] = wifi_han
config['connect_coro'] = conn_han
config['clean'] = True

# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)
mac = ubinascii.hexlify(client._sta_if.config('mac')).decode()

init()
try:
    asyncio.run(mqtt())
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
