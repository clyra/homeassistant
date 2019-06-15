"""
sensor for humanity today/tomorrow shift

"""
import datetime
import logging
import requests
import json

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION, CONF_NAME, CONF_USERNAME, CONF_PASSWORD )
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['requests']

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Data provided by Humanity"
CONF_APP_ID = "app_id"
CONF_APP_SECRET = "app_secret"

DEFAULT_NAME = 'humanity'

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=300)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_APP_ID): cv.string,
    vol.Required(CONF_APP_SECRET): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Humanity sensor."""

    name = config.get(CONF_NAME)
    
    hu = HumanityData(config.get(CONF_APP_ID), config.get(CONF_APP_SECRET), config.get(CONF_USERNAME), config.get(CONF_PASSWORD) )

    if not hu:
        _LOGGER.error("Unable to connect to Humanity")
        return

    dev = []
    dev.append(HumanitySensor(name, hu, 'today'))
    dev.append(HumanitySensor(name, hu, 'tomorrow'))

    add_entities(dev, True)

class HumanitySensor(Entity):
    """Implementation of an humanity sensor."""

    def __init__(self, name, hu, sensor_type):
        """Initialize the sensor."""
        self._name = name
        self._type = sensor_type
        self.hu_client = hu
        self._state = None
        self._unit_of_measurement = 'ppl'

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self._name, self._type)

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

#    @property
#    def unit_of_measurement(self):
#        """Return the unit of measurement of this entity, if any."""
#        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }

    def update(self):
        """Get the latest data from humanity and update the states."""

        try:
            self.hu_client.update()
        except:
            _LOGGER.error("Error when calling humanity to update data")
            return

        try:
            if self._type == 'today':
                self._state = ', '.join(self.hu_client.today)
            elif self._type == 'tomorrow':
                self._state = ', '.join(self.hu_client.tomorrow)
        except KeyError:
            self._state = None
            _LOGGER.warning(
                "Information is currently not available: %s", self.type)

    @property
    def units(self):
        """Get the unit system of returned data."""
        return 'ppl' 


class HumanityData:

  def __init__(self, app_id, app_secret, user, pwd):

    self.app_id = app_id
    self.app_secret = app_secret 
    self.user = user
    self.pwd = pwd
    self.token = ''
    self.refresh_token = ''
    self.today = 'Nobody'
    self.tomorrow = 'Nobody'
    self.data = None
    self.count = 0

    self.get_token()

  def get_token(self):
    """get access token from humanity api"""

    auth_url = 'https://www.humanity.com/oauth2/token.php'
    auth_data = {  "client_id": self.app_id, 
                   "client_secret": self.app_secret,
                   "grant_type": "password",
                   "username": self.user,
                   "password": self.pwd }
    try:
      r = requests.post( auth_url, data = auth_data )
      self.token = r.json()["access_token"]
      self.refresh_token = r.json()["refresh_token"]
      self.count = 0    
    except:
      _LOGGER.error(
                'couldnt get the access token. check config')

  def get_new_token(self):
  
    auth_url = 'https://www.humanity.com/oauth2/token.php'
    auth_data = {  "client_id": self.app_id, 
                   "client_secret": self.app_secret,
                   "grant_type": "refresh_token",
                   "refresh_token": self.refresh_token
                 }
    try:
      r = requests.post( auth_url, data = auth_data )
      self.token = r.json()["access_token"]
      self.refresh_token = r.json()["refresh_token"]
      self.count = 0    
    except:
      _LOGGER.error(
                'couldnt get access token from refresh_token')

  def check_count(self):
     """check if it's time to refresh token"""

     self.count +=1
     if self.count > 50:
     	self.get_new_token()

  
  def get_me(self):
  
    url = 'https://www.humanity.com/api/v2/me'
    payload = { 'access_token': self.token }

    try:
      self.check_count()
      r = requests.get( url, params = payload )
      print(r.text)
    except:
      print('something went wrong')

  def get_onnow(self):

    url = 'https://www.humanity.com/api/v2/dashboard/onnow'
    payload = { 'access_token': self.token }

    try:
      self.check_count()
      r = requests.get( url, params = payload )
      print(r.text)
    except:
      print('something went wrong')  	

  def get_shifts(self):
    """get shifts from humnanit"""

    url = 'https://www.humanity.com/api/v2/shifts'

    # limit to only 3 days from now. can be changed later
    start_date = "{:%Y-%m-%d}".format(datetime.datetime.now())
    end_date = "{:%Y-%m-%d}".format(datetime.datetime.now() + datetime.timedelta(days=3))
    payload = { 'start_date': start_date, 'end_date': end_date, 'access_token': self.token }

    try:
      self.check_count()
      r = requests.get( url, params = payload )
      shifts = r.json()['data']
    except:
      _LOGGER.warning(
                'something went wrong while trying to get shifts')
      shifts = []

    return shifts  

  def get_date_shift(self, shifts, shift_date):

     employees = []
     for i in shifts:
      if i['start_date']['day'] == shift_date.day and i['start_date']['month'] == shift_date.month and i['start_date']['year'] == shift_date.year:
        for j in i['employees']:
          employees.append(j['name'])
     if len(employees) == 0:
          employees.append('Nobody')     
     return employees     
    
  @Throttle(MIN_TIME_BETWEEN_UPDATES)
  def update(self):
     shifts = self.get_shifts()

     self.today = self.get_date_shift(shifts, datetime.datetime.now())
     self.tomorrow = self.get_date_shift(shifts, datetime.datetime.now() + datetime.timedelta(days=1))

     #print(self.today, self.tomorrow)

