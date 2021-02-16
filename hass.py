import binascii
import json

import network
import uasyncio as asyncio

import mqtt_as
from config import make_config


class HassIntegration:
    def __init__(self, state_cb, command_cb):
        self.state_cb = state_cb
        self.command_cb = command_cb
        self.mac = binascii.hexlify(network.WLAN().config('mac')).decode()
        self.client = None

    def run(self):
        # Define configuration
        config = mqtt_as.config.copy()
        config['subs_cb'] = self.sub_cb
        config['wifi_coro'] = self.wifi_han
        config['connect_coro'] = self.conn_han
        config['clean'] = True
        config['will'] = ('micropython/{}/availability'.format(self.mac), "offline", True, 1)
        make_config(config)

        # Set up client
        mqtt_as.MQTTClient.DEBUG = True  # Optional
        self.client = mqtt_as.MQTTClient(config)

        try:
            asyncio.run(self.mqtt())
        finally:
            self.client.close()  # Prevent LmacRxBlk:1 errors

    def sub_cb(self, topic, msg, retained):
        print((topic, msg, retained))
        if topic == b"micropython/{}/command".format(self.mac):
            self.command_cb(msg.decode())
            asyncio.create_task(self.publish_status())

    async def wifi_han(self, state):
        print('Wifi is ', 'up' if state else 'down')
        await self.publish_status()

    # If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
    async def conn_han(self, client):
        await client.subscribe("micropython/{}/command".format(self.mac), 1)

    async def mqtt(self):
        while not self.client.isconnected():
            try:
                await self.client.connect()
            except OSError as e:
                print('Connection failed.')
                print(e)
                print('retrying in 10 sec')
                await asyncio.sleep(10)

        while True:
            await self.client.publish('homeassistant/climate/{}/config'.format(self.mac), json.dumps({
                "~": "micropython/{}".format(self.mac),
                "name": "Winefridge Upper Compartment",
                "min_temp": 5,
                "max_temp": 20,
                "temp_step": 0.5,
                "temp_unit": "C",
                "modes": ["off", "cool"],

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
            await self.publish_status()
            await asyncio.sleep(5)

    async def publish_status(self):
        await self.client.publish('micropython/{}/availability'.format(self.mac), 'online')
        await self.client.publish('micropython/{}/state'.format(self.mac), json.dumps(self.state_cb()))
