"""
Platform for retrieving meteorological data from Climatempo.

"""
from datetime import datetime, timedelta
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
    CONF_URL, CONF_NAME, CONF_API_KEY, TEMP_CELSIUS,
    CONF_MODE, TEMP_FAHRENHEIT)
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

REQUIREMENTS = ['requests']

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = 'Dados providos por Climatempo'

CONF_CITY = "city"

ATTR_FORECAST_UV = "UV index"
ATTR_FORECAST_PRECIPTATION_PROBABILITY = "rain probability"

MAP_CONDITION = {
    '1': 'sunny',
    '1n': 'clear-night',
    '2': 'partlycloudy',
    '2n': 'partlycloudy',
    '2r': 'cloudy',
    '2rn': 'cloudy',
    '2tm': 'cloudy',
    '3': 'rainy',
    '3n': 'rainy',
    '4': 'sunny',
    '4n': 'clear-night',
    '4r': 'rainy',
    '4rn': 'rainy',
    '4t': 'lightning',
    '4tn': 'lightning',
    '5': 'pouring',
    '5n': 'pouring',
    '6': 'lightning',
    '6n': 'lightning',
    '7': 'freezing',
    '7n': 'geada',
    '8': 'snow',
    '8n': 'snow',
    '9': 'fog',
    '9n': 'fog'
}

CONF_UNITS = 'units'

DEFAULT_NAME = 'climatempo'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_CITY): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=10)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Climatmepo weather."""
    name = config.get(CONF_NAME)

    units = 'si' 

    climatempo = ClimatempoData(
        config.get(CONF_API_KEY), config.get(CONF_CITY) )

    add_entities([ClimatempoWeather(name, climatempo)], True)


class ClimatempoWeather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, name, climatempo):
        """Initialize Simepar weather."""
        self._name = name
        self._ct = climatempo

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
        return self._ct.currently['temperature']

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS 

    @property
    def humidity(self):
        """Return the humidity."""
        return round(self._ct.currently['humidity'], 2 )

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return self._ct.currently['wind_velocity']

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return self._ct.currently['wind_direction']

    @property
    def pressure(self):
        """Return the pressure."""
        return self._ct.currently['pressure']

    @property
    def description(self):
        """Return the textual weather condition."""
        #return self._ct.currently['condition'].encode('UTF-8')
        return self._ct.currently['condition']

    @property
    def condition(self):
        """Return the weather condition."""
        return MAP_CONDITION.get(self._ct.currently['icon'])

    @property
    def forecast(self):
        """Return the forecast array."""

        if time.localtime().tm_isdst == 1:
            offset = time.altzone
        else:
            offset = time.timezone

        data = []
        data = [{
                ATTR_FORECAST_TIME:
                    datetime.fromtimestamp(entry['timestamp']+offset).isoformat(),
                ATTR_FORECAST_TEMP:
                    entry['temperature']['max'],
                ATTR_FORECAST_TEMP_LOW:
                    entry['temperature']['min'],
                ATTR_FORECAST_PRECIPITATION:
                    entry['rain']['precipitation'],
                ATTR_FORECAST_PRECIPTATION_PROBABILITY:
                    entry['rain']['probability'],
                ATTR_FORECAST_WIND_SPEED:
                    entry['wind']['velocity_avg'],
                ATTR_FORECAST_WIND_BEARING:
                    entry['wind']['direction'],
                ATTR_FORECAST_CONDITION:
                    MAP_CONDITION.get(entry['text_icon']['icon']['day']),
            } for entry in self._ct.daily]

        return data

    def update(self):
        """Get the latest data from Climatempo."""
        self._ct.update()


class ClimatempoData:
    """Class to hold climatempo data."""

    def __init__(self, api_key, cidade):
        """Initialize the data object."""

        self._url_forecast72 = "http://apiadvisor.climatempo.com.br/api/v1/forecast/locale/" + cidade + "/hours/72?token=" + api_key
        self._url_forecast15 = "http://apiadvisor.climatempo.com.br/api/v1/forecast/locale/" + cidade + "/days/15?token=" + api_key
        self._url_current  = "http://apiadvisor.climatempo.com.br/api/v1/weather/locale/" + cidade + "/current?token=" + api_key

        self.currently = None
        self.hourly = None
        self.daily = None


    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from climatempo."""
        import requests

        try:
            r = requests.get(self._url_current)
            self.currently = r.json()['data']

            #q = requests.get(self._url_forecast72)
            #self.hourly = q.json()

            s = requests.get(self._url_forecast15)
            self.daily = s.json()['data']

        except:
            _LOGGER.error("Unable to connect to climatempo, %s", self._url_current)
            self.currently = None
            self.hourly = None
            self.daily = None

        # fix date
        for i in self.daily:
          l = i['date'].split('-')
          d = datetime(int(l[0]), int(l[1]), int(l[2]))
          i['timestamp'] = d.timestamp()
