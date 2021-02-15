from mqtt_as import MQTTClient, config
import uasyncio as asyncio
from config import *

# Subscription callback
def sub_cb(topic, msg, retained):
    print((topic, msg, retained))

async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe('foo_topic', 1)

async def main(client):
    while not client.isconnected():
        try:
            await client.connect()
        except OSError as e:
            print('Connection failed.')
            print(e)
            print('retrying in 10 sec')
            await asyncio.sleep(10)
    n = 0
    while True:
        await asyncio.sleep(5)
        print('publish', n)
        # If WiFi is down the following will pause for the duration.
        await client.publish('result', '{}'.format(n))
        n += 1

# Define configuration
config['subs_cb'] = sub_cb
config['wifi_coro'] = wifi_han
config['connect_coro'] = conn_han
config['clean'] = True

# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
