from mqtt_as import MQTTClient, config
import uasyncio as asyncio
from config import *
import json
import ubinascii
import network
from controll import get_state, init, command

# Subscription callback
def sub_cb(topic, msg, retained):
    print((topic, msg, retained))
    if topic == b"micropython/{}/command".format(mac):
        command(msg.decode())
        asyncio.create_task(publish_status())

async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await publish_status()

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe("micropython/{}/command".format(mac), 1)

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
        await client.publish('homeassistant/climate/{}/config'.format(mac), json.dumps({
            "~": "micropython/{}".format(mac),
            "name": "Winefridge Upper Compartment",
            "min_temp": 5,
            "max_temp": 20,
            "temp_step": 0.5,
            "temp_unit": "C",
            "modes":["off", "cool"],
            
            "avty_t": "~/availability",
            
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
        await asyncio.sleep(5)


async def publish_status():
    await client.publish('micropython/{}/availability'.format(mac), 'online')
    await client.publish('micropython/{}/state'.format(mac), json.dumps(get_state()))

# mac adress
mac = ubinascii.hexlify(network.WLAN().config('mac')).decode()

# Define configuration
config['subs_cb'] = sub_cb
config['wifi_coro'] = wifi_han
config['connect_coro'] = conn_han
config['clean'] = True
config['will'] = ('micropython/{}/availability'.format(mac), "offline", True, 1)

# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)

init()
try:
    asyncio.run(mqtt())
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
