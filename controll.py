import json
settings = None

def init():
    global settings
    try:
        with open('settings.json') as settings_file:
            settings = json.load(settings_file)
    except (OSError, ValueError) as e:
        settings = {'on': False, 'target': 10}
        save_settings()

def save_settings():
    with open('settings.json', 'w') as settings_file:
        json.dump(settings, settings_file)

def get_state():
    return {
            "mode": "cool" if settings['on'] else "off",
            "target_temp": settings['target'],
            "current_temp": 15,
        }

def command(cmd_sting):
    cmd, arg = cmd_sting.split(':')
    if cmd == 'target':
        settings['target'] = float(arg)
    if cmd == 'mode':
        settings['on'] = arg == 'cool'
    save_settings()
