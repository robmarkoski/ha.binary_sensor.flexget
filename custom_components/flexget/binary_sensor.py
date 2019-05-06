'''
Custom binary_sensor platform for flexget.

Stolen from @Tommatheussen who developed the original script.
https://github.com/Tommatheussen/Home-Assistant-Configuration/tree/master/custom_components/binary_sensor

Somehow i managed to get it working.

'''
import logging
import voluptuous as vol
from homeassistant.components.binary_sensor import (BinarySensorDevice, 
                                                    PLATFORM_SCHEMA)
from homeassistant.const import (CONF_HOST, CONF_PORT, 
                                 CONF_USERNAME, CONF_PASSWORD, 
                                 CONF_SSL)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from datetime import timedelta

import requests

__version__ = '0.0.3'

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Flexget'

TIME_BETWEEN_UPDATES = timedelta(minutes=5)

# TODO:
# Clean this up. Only have a single base URL and add API call points after.

BASE_URL_VERSION = "http://{}:{}/api/server/version/"
BASE_URL_STATUS = "http://{}:{}/api/status/"
BASE_URL_TASK = "http://{}:{}/api/status/{}/"

CONF_TASKS = 'tasks'
CONF_CHECK_VERSION = 'check_version'

ICON = 'mdi:download'

def versioncompare(version):
    """ Turn Version into tuple to allow compairson"""
    return tuple(map(int, (version.split("."))))

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default='localhost'): cv.string,
    vol.Optional(CONF_PORT, default=5050): cv.port,
    vol.Optional(CONF_SSL, default=False): cv.boolean,
    vol.Optional(CONF_CHECK_VERSION, default=True): cv.boolean,
    vol.Optional(CONF_USERNAME, default='flexget'): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_TASKS, default=[]): cv.ensure_list
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Setup the sensor platform."""
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    tasks = config.get(CONF_TASKS)
    ssl = config[CONF_SSL]
    check_version = config.get(CONF_CHECK_VERSION)

    url = BASE_URL_STATUS.format(host, port)

    try:
        r = requests.get(url,
                         auth=(username, password),
                         params=({'include_execution': False}),
                         verify=ssl,
                         timeout=25)
    except requests.exceptions.RequestException:
        _LOGGER.error("Failed to connect to the configured Flexget instance: %e",
                      requests.exceptions.RequestException)
        return False

    if (r.status_code == 401):
        _LOGGER.error("Authentication with Flexget failed")
        return False

    devices = []
    for task in r.json():
        if task['name'] in tasks or tasks == []:
            _LOGGER.debug("Adding Task {} with Task ID {}".format(task['name'], task['id']))
            devices.append(FlexgetTaskSensor(task['name'], task['id'], host, port, username, password, ssl))

    if check_version == True:
        devices.append(FlexgetVersionSensor("flexget_update", host, port, username, password, ssl))
    #
    #Debugger
    #_LOGGER.debug(devices)
    async_add_entities(devices, True)

class FlexgetVersionSensor(BinarySensorDevice):
    """ Representation of a Binary Sensor. """
    def __init__(self, name, host, port, username, password, ssl):
        self._name = name
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._ssl = ssl
        self._state = None
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor. Based on whether there is a new version available."""
        if versioncompare(self._version_data['flexget_version']) < versioncompare(self._version_data['latest_version']):
            return True
        return False 

    @property
    def device_state_attributes(self):
        """Return version details in state attributes"""
        if self._version_data:
            return self._version_data
        return "None"
    
    @Throttle(TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data and updates the state and """

        url = BASE_URL_VERSION.format(self._host, self._port)
        _LOGGER.debug("Connecting to URL: {}".format(url))
        try:
            r = requests.get(url,
                            auth=(self._username, self._password),
                            verify=self._ssl, timeout=10)
            self._version_data = r.json()
            _LOGGER.debug("Version Data Recieved - {}".format(self._version_data))
        except Exception as error:
            _LOGGER.debug("Error Receiving Version Data - {}".format(error))

class FlexgetTaskSensor(BinarySensorDevice):
    """Representation of a Sensor."""
    def __init__(self, name, task_id, host, port, username, password, ssl):
        self._name = name
        self._id = task_id
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._ssl = ssl
        self._state = None
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        if self._last_execution['succeeded']:
            self._state = True
        return self._state

    @property
    def device_state_attributes(self):
        """Return the last execution details"""
        if self._last_execution:
            return self._last_execution
        return "None"

    @property
    def icon(self):
        """Return a icon for the binary sensor."""
        return ICON

    @Throttle(TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data and updates the state and """
        url = BASE_URL_TASK.format(self._host, self._port, self._id)
        _LOGGER.debug("Updating Status via Url: {}".format(url))
        try:
            r = requests.get(url,
                             auth=(self._username, self._password),
                             verify=self._ssl, timeout=15)
            self._last_execution = r.json()['last_execution']
            _LOGGER.debug("Recieved value {}".format(self._last_execution))
        except Exception as error:
            _LOGGER.debug("Task {} - Could not be updated - {}".format(self._name, error))
