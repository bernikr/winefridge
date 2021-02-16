from controll import get_state, init, command
from hass import HassIntegration

hass = HassIntegration(get_state, command)
init()
hass.run()
