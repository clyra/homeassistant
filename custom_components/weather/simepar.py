"""
Platform for retrieving meteorological data from Simepar.

"""
from datetime import datetime, timedelta
import re
import requests
import json
import logging
import time

from requests.exceptions import (
    ConnectionError as ConnectError, HTTPError, Timeout)
import voluptuous as vol

from homeassistant.components.weather import (
    ATTR_FORECAST_TEMP, ATTR_FORECAST_TIME, ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_WIND_SPEED, ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_TEMP_LOW, ATTR_FORECAST_PRECIPITATION,
    PLATFORM_SCHEMA, WeatherEntity)
from homeassistant.const import (
    CONF_URL, CONF_NAME, TEMP_CELSIUS,
    CONF_MODE, TEMP_FAHRENHEIT)
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

REQUIREMENTS = ['requests']

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = 'Dados providos por Simepar'

FORECAST_MODE = ['hourly', 'daily']

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

CONF_UNITS = 'units'

DEFAULT_NAME = 'simepar'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_MODE, default='hourly'): vol.In(FORECAST_MODE),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=3)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Simepar weather."""
    name = config.get(CONF_NAME)
    mode = config.get(CONF_MODE)

    units = 'si' 

    simepar = SimeparData(
        config.get(CONF_URL) )

    add_entities([SimeparWeather(name, simepar, mode)], True)


class SimeparWeather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, name, simepar, mode):
        """Initialize Simepar weather."""
        self._name = name
        self._simepar = simepar
        self._mode = mode

        self._sm_data = None
        self._sm_currently = None
        self._sm_hourly = None
        self._sm_daily = None

    def mstokmh(self, ms):
        return (round(ms*3.6))

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def temperature(self):
        """Return the temperature."""
        return self._sm_currently.get('temp_est')

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS 

    @property
    def humidity(self):
        """Return the humidity."""
        return round(self._sm_currently.get('humidity_est'), 2 )

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return (self.mstokmh(self._sm_currently.get('wind_est')))

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return self._sm_currently.get('windDirection_est')

    @property
    def pressure(self):
        """Return the pressure."""
        return self._sm_currently.get('pressure')

    @property
    def visibility(self):
        """Return the visibility."""
        return self._sm_currently.get('visibility')

    @property
    def condition(self):
        """Return the weather condition."""
        return MAP_CONDITION.get(self._sm_currently.get('icon'))

    @property
    def forecast(self):
        """Return the forecast array."""

        data = None
        if time.localtime().tm_isdst == 1:
           offset = time.altzone
        else:
           offset = time.timezone
        
        if self._mode == 'daily':
            data = [{
                ATTR_FORECAST_TIME:
                    datetime.fromtimestamp(entry.get('timestamp')+offset).isoformat(),
                ATTR_FORECAST_TEMP:
                    entry.get('tempMax'),
                ATTR_FORECAST_TEMP_LOW:
                    entry.get('tempMin'),
                ATTR_FORECAST_PRECIPITATION:
                    entry.get('precIntensity'), 
                ATTR_FORECAST_WIND_SPEED:
                    entry.get('wind'),
                ATTR_FORECAST_WIND_BEARING:
                    entry.get('windDirection'),
                ATTR_FORECAST_CONDITION:
                    MAP_CONDITION.get(entry.get('icon'))
            } for entry in self._sm_daily]
        else:
            data = [{
                ATTR_FORECAST_TIME:
                    datetime.fromtimestamp(entry.get('timestamp')+offset).isoformat(),
                ATTR_FORECAST_TEMP:
                    entry.get('temp'),
                ATTR_FORECAST_PRECIPITATION:
                    entry.get('precIntensity'),
                ATTR_FORECAST_CONDITION:
                    MAP_CONDITION.get(entry.get('icon'))
            } for entry in self._sm_hourly]

        return data

    def update(self):
        """Get the latest data from Simepar."""
        self._simepar.update()

        self._sm_data = self._simepar.data
        self._sm_currently = self._simepar.currently
        self._sm_hourly = self._simepar.hourly
        self._sm_daily = self._simepar.daily


class SimeparData:
    """Get the latest data from Simepar."""

    def __init__(self, api_key):
        """Initialize the data object."""
        self._url = api_key

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
            self.hourly = [] 
            hourlylist = [] 
            for i in self.data[0]['hour'].keys():
               hourlylist.append(self.data[0]['hour'][i])
            for i in self.data[1]['hour']:
               hourlylist.append(self.data[1]['hour'][i])
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

