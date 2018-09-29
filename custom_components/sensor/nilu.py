
"""
Unifi sensor. Shows the total number os devices connected. Also shows the number of devices per
AP and per essid as attributes.

with code from https://github.com/frehov/Unifi-Python-API

Version 0.2
"""

from datetime import timedelta
import requests
import json
import re
from typing import Pattern, Dict, Union
import logging

import voluptuous as vol

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_REGION, STATE_UNKNOWN)
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import template


REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)


DOMAIN = 'sensor'
ENTITY_ID_FORMAT = DOMAIN + '.{}'


SCAN_INTERVAL = timedelta(seconds=300)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_REGION): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Nilu Sensors."""
    area, station = config.get(CONF_REGION).split(',')
    data = NiluSensorData(hass, area, station)

    for k in data.attrs.keys():
        name = data.attrs[k]['municipality'].lower() + "_" + data.attrs[k]['station'].lower() + "_" + k.lower()
        add_devices([NiluSensor(hass, data, k, name)], True)


class NiluSensor(Entity):
    """Representation of a Unifi Sensor."""

    def __init__(self, hass, data, component, name):
        """Initialize the sensor."""
        self._hass = hass
        self._data = data
        self._component= component
        self._name= name
        self._state = None
        self._attributes = None
        self._unit_of_measurement = 'ug/m3'

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

#    @property
#    def precision(self):
#        """Return the precision of the system."""
#        return PRECISION_WHOLE

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes    

    def update(self):
        """Fetch new state data for the sensor."""
        self._data.update()
        value = self._data.attrs[self._component]['value']
        if value is None:
            value = STATE_UNKNOWN
            self._attributes = {}
        else:
            self._state = value   
            self._attributes = self._data.attrs[self._component] 

    

class NiluSensorData(object):
    """
    Nilu API

    """
    _current_status_code = None

    def __init__(self, hass, area, station):
        """
        Initiates tha api and grab the components.
        """
        self._hass = hass
        self._url = 'https://api.nilu.no/aq/utd.json?areas={}&stations={}'.format(area, station)
        self.attrs = {}

        self.update()

    def get_data(self):
        """
        download Nilu data
        """
        
        try:
            myData = json.loads(requests.get(self._url).text)
        except:
            _LOGGER.error("couldnt get data from Nilu API. Check if parameters are correct.")
            return None

        for i in range(len(myData)):
            component = myData[i]['component'].replace(".","")
            self.attrs[component] = myData[i]

    def update(self):
        self.get_data()
