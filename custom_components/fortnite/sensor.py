"""Fortnite Sensor integration
to use, add something like this to HA config:

sensor:
 - platform: fortnite
   name: myfortnite_integration
   api_key: <your_api_key>
   player_id: <player_name>
   game_platform: "GAMEPAD"
   game_mode: "SQUAD"
"""

import voluptuous as vol
import logging

from .fortnite import FortniteData

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_API_KEY  )
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'sensor'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required('player_id'): cv.string,
    vol.Required('game_platform'): cv.string,
    vol.Required('game_mode'): cv.string,
    vol.Required(CONF_NAME): cv.string
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the fortnite sensor."""

    _LOGGER.info("init sensor")
    name = config.get(CONF_NAME)
    api_key = config.get(CONF_API_KEY)
    player_id = config.get('player_id')
    game_platform = config.get('game_platform')
    game_mode = config.get('game_mode')

    fn = FortniteData(name, api_key, player_id, game_platform, game_mode)

    if not fn:
        _LOGGER.error("Unable to create the fortnite sensor")
        return

    add_entities([FortniteSensor(hass, fn)], True)

class FortniteSensor(Entity):

    def __init__(self, hass, fn):
        self._hass = hass
        self.data = fn
         
    @property
    def name(self):
        """Return the name of the sensor."""
        return '{}'.format(self.data.name)

    @property
    def state(self):
        """Return the state of the device."""
        return self.data.attr['kills']

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.data.attr

    def update(self):
        self.data.update_stats()

