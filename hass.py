import binascii
import json

import network
import uasyncio as asyncio

import mqtt_as
from config import make_config


class HassIntegration:
    def __init__(self, entity_config, device_info, state_cb, command_cb):
        self.entity_config = entity_config
        self.device_info = device_info
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
            cmd, arg = msg.decode().split(':')
            self.command_cb(cmd, arg)
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
            await self.publish_discovery()
            await self.publish_status()
            await asyncio.sleep(5)

    async def publish_status(self):
        await self.client.publish('micropython/{}/availability'.format(self.mac), 'online')
        await self.client.publish('micropython/{}/state'.format(self.mac), json.dumps(self.state_cb()))

    async def publish_discovery(self):
        counter = {}
        for e in self.entity_config:
            n = counter.get(e['type'], 0)
            counter[e['type']] = n + 1

            payload = {
                "~": "micropython/{}".format(self.mac),
                "avty_t": "~/availability",
                "dev": {
                    "cns": [["mac", self.mac]]
                },
                "uniq_id": "{}_{}".format(self.mac, n),
            }
            payload['dev'].update(self.device_info)
            payload.update(e['settings'])
            for k, v in e.get('states', {}).items():
                payload[k + '_t'] = "~/state"
                if k == 'stat':
                    payload['val_tpl'] = "{{{{ value_json.{} }}}}".format(v)
                else:
                    payload[k + '_tpl'] = "{{{{ value_json.{} }}}}".format(v)
            for k, v in e.get('commands', {}).items():
                payload[k + '_cmd_t'] = "~/command"
                payload[k + '_cmd_tpl'] = "{}:{{{{ value }}}}".format(v)

            await self.client.publish('homeassistant/{}/{}_{}/config'.format(e['type'], self.mac, n), json.dumps(payload))
