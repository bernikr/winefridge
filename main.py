import json

from hass import HassIntegration

settings = None

entity_config = [
    {
        'type': 'climate',
        'settings': {
            "name": "Winefridge Test",
            "min_temp": 5,
            "max_temp": 20,
            "temp_step": 0.5,
            "temp_unit": "C",
            "modes": ["off", "cool"],
        },
        'states': {
            'mode_stat': 'mode',
            'temp_stat': 'target_temp',
            'curr_temp': 'current_temp',
        },
        'commands': {
            'mode': 'mode',
            'temp': 'target',
        }
    },
    {
        'type': 'sensor',
        'settings': {
            "name": "Winefridge Test2",
        },
        'states': {
            'stat': 'target_temp',
        }
    }
]

device_info = {
    "name": "Wine Fridge",
    "mf": "homemade",
}


def main():
    global settings
    try:
        with open('settings.json') as settings_file:
            settings = json.load(settings_file)
    except (OSError, ValueError) as e:
        settings = {'on': False, 'target': 10}
        save_settings()
    hass = HassIntegration(entity_config, device_info, get_state, command)
    hass.run()


def save_settings():
    with open('settings.json', 'w') as settings_file:
        json.dump(settings, settings_file)


def get_state():
    return {
        "mode": "cool" if settings['on'] else "off",
        "target_temp": settings['target'],
        "current_temp": 15,
    }


def command(cmd, arg):
    if cmd == 'target':
        settings['target'] = float(arg)
        print('set target to {}'.format(settings['target']))
    if cmd == 'mode':
        settings['on'] = arg == 'cool'
        print('set on to {}'.format(settings['on']))
    save_settings()


if __name__ == '__main__':
    main()
