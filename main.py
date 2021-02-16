import json

from hass import HassIntegration

settings = None


def main():
    global settings
    try:
        with open('settings.json') as settings_file:
            settings = json.load(settings_file)
    except (OSError, ValueError) as e:
        settings = {'on': False, 'target': 10}
        save_settings()
    hass = HassIntegration(get_state, command)
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
