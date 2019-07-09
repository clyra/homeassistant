"""
Support for the Simepar service.

"""
from datetime import timedelta
import logging
import requests
import json
import re

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION, CONF_URL, CONF_NAME, TEMP_CELSIUS )
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['requests']

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Data provided by Simepar"

DEFAULT_NAME = 'simepar'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)

MAP_CONDITION = {
    'wi wi-day-sunny': 'sunny',
    'wi wi-night-clear': 'clear-night',
    'wi wi-day-sunny-overcast': 'sunny',
    'wi wi-night-alt-partly-cloudy': 'partlycloudy',
    'wi wi-night-alt-cloudy': 'cloudy',
    'wi wi-rain': 'pouring',
    'wi wi-night-alt-rain': 'rainy',
    'wi wi-day-rain': 'rainy',
    'wind': 'windy',
    'wi wi-cloudy': 'cloudy',
    'wi wi-day-cloudy': 'partlycloudy',
    'wi wi-cloudy': 'cloudy',
    'wi wi-thunderstorm': 'lightning',
    'tornado': None
}

SENSOR_TYPES = {
    'weather_now': ['Condition Now', None],
    'weather_today': ['Condition Today', None],
    'weather_tomorrow': ['Condition Tomorrow', None],
    'temp_now': ['Temperature Now', TEMP_CELSIUS],
    'temp_max_today': ['Temperature Max Today', TEMP_CELSIUS],
    'temp_min_today': ['Temperature Min Today', TEMP_CELSIUS],
    'temp_max_tomorrow': ['Temperature Max Tomorrow', TEMP_CELSIUS],
    'temp_min_tomorrow': ['Temperature Min Tomorrow', TEMP_CELSIUS],
    'wind_speed_now': ['Wind speed', 'm/s'],
    'wind_bearing_now': ['Wind bearing', '°'],
    'humidity_now': ['Humidity', '%'],
    'pressure_now': ['Pressure', 'mbar'],
    'rain_now': ['Rain Now', 'mm'],
    'rain_today': ['Rain Today', 'mm'],
    'rain_chance_today': ['Chance of Rain Today', '%'],
    'rain_tomorrow': ['Rain Tomorrow', 'mm'],
    'rain_chance_tomorrow': ['Chance of Rain Tomorrow', '%'],
    'uv_index_now': ['UV index now', None],
    'uv_index_today': ['UV index today', None],
    'uv_index_tomorrow': ['UV index tomorrow', None]
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Simepar sensor."""

    name = config.get(CONF_NAME)
    
    sm = SimeparData(URL=config.get(CONF_URL))

    if not sm:
        _LOGGER.error("Unable to connect to Simepar")
        return

    dev = []
    for key in SENSOR_TYPES.keys():
        dev.append(SimeparSensor(name, sm, key))

    add_entities(dev, True)

class SimeparSensor(Entity):
    """Implementation of an Simepar sensor."""

    def __init__(self, name, weather_data, sensor_type):
        """Initialize the sensor."""
        self.client_name = name
        self._name = SENSOR_TYPES[sensor_type][0]
        self.sm_client = weather_data
        self.type = sensor_type
        self._state = None
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self.client_name, self._name)
        #return '{}'.format(self._name)

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    def update(self):
        """Get the latest data from Simepar and updates the states."""

        try:
            self.sm_client.update()
        except:
            _LOGGER.error("Error when calling Simepar to update data")
            return

        today = self.sm_client.currently
        tomorrow = self.sm_client.tomorrow
        lasthour = self.sm_client.hourly[0]

        if today is None:
            return

        try:
            if self.type == 'weather_now':
                self._state = MAP_CONDITION.get(today['icon_last_hour'])
            elif self.type == 'weather_today':
                self._state = MAP_CONDITION.get(today['icon'])
            elif self.type == 'weather_tomorrow':
                self._state = MAP_CONDITION.get(tomorrow['icon'])
            elif self.type == 'temp_now':
                self._state = today['temp_hour']
            elif self.type == 'temp_max_today':
                self._state = today['tempMax']
            elif self.type == 'temp_min_today':
                self._state = today['tempMin']
            elif self.type == 'temp_max_tomorrow':
                self._state = tomorrow['tempMax']
            elif self.type == 'temp_min_tomorrow':
                self._state = tomorrow['tempMin']
            elif self.type == 'pressure_now':
                self._state = today['pressure'] 
            elif self.type == 'humidity_now':
                self._state = today['humidity_hour'] 
            elif self.type == 'wind_speed_now':
                self._state = round(today['wind_hour']*3.6) 
            elif self.type == 'wind_bearing_now':
                self._state = today['windDirection_hour']
            elif self.type == 'rain_now':
                self._state = today['precIntensity_hour']
            elif self.type == 'rain_today':
                self._state = today['precIntensity']
            elif self.type == 'rain_tomorrow':
                self._state = tomorrow['precIntensity']
            elif self.type == 'rain_chance_today':
                self._state = today['precProbability'] * 100;
            elif self.type == 'rain_chance_tomorrow':
                self._state = tomorrow['precProbability'] * 100;
            elif self.type == 'uv_index_now':
                self._state = lasthour['uvIndex']
            elif self.type == 'uv_index_today':
                self._state = today['uvIndex']
            elif self.type == 'uv_index_tomorrow':
                self._state = tomorrow['uvIndex']


#            elif self.type == 'rain':
#                if data.get_rain():
#                    self._state = round(data.get_rain()['3h'], 0)
#                    self._unit_of_measurement = 'mm'
#                else:
#                    self._state = 'not raining'
#                    self._unit_of_measurement = ''

        except KeyError:
            self._state = None
            _LOGGER.warning(
                "Condition is currently not available: %s", self.type)


class SimeparData:
    """Get the latest data from Simepar."""

    def __init__(self, URL):
        """Initialize the data object."""
        self._url = URL

        self.data = None
        self.currently = None
        self.hourly = None
        self.daily = None

        self.json_re = re.compile(r'forecastJSON.*(\[.*\])')

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from Simepar."""

        _LOGGER.info("updating simepar")

        try:
            r = requests.get(self._url)
            f = self.json_re.search(r.text)
            self.data = json.loads(f.groups()[0])
            self.currently = self.data[0]
            self.tomorrow = self.data[1]
            self.hourly = []
            hourlylist = []
            for i in self.data[0]['hour'].keys():
               hourlylist.append(self.data[0]['hour'][i])
            self.hourly = sorted(hourlylist, key=lambda k: k['timestamp'])
            self.daily = self.data
        except:
            _LOGGER.error("Unable to connect to Simepar.")
            self.data  = None
            self.daily = None

    @property
    def units(self):
        """Get the unit system of returned data."""
        return self.data.json.get('flags').get('units')
