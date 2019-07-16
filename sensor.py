"""
Support for the Flume smart water meter.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.flume/
"""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    VOLUME_GALLONS, CONF_USERNAME, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'client_secret'

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): vol.Email(),
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_CLIENT_ID): str,
    vol.Required(CONF_CLIENT_SECRET): str
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Flume sensor."""
    from . flume_homeassistant import FlumeClient

    flume = FlumeClient(creds={
        CONF_USERNAME: str(config.get(CONF_USERNAME)),
        CONF_PASSWORD: config.get(CONF_PASSWORD),
        CONF_CLIENT_ID: config.get(CONF_CLIENT_ID),
        CONF_CLIENT_SECRET: config.get(CONF_CLIENT_SECRET)
    })

    sensor_list = list(flume.get_usage().keys())
    add_entities(
        [FlumeSensor(sensor_type, flume) for sensor_type in sensor_list],
        True
    )


class FlumeSensor(Entity):
    """Implementation of a Flume sensor."""

    def __init__(self, sensor_type, flume):
        """Initialize the sensor."""
        self.sensor_type = sensor_type
        self.flume = flume

        self._name = None
        self._state = None
        self._attr = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return '{}-{}'.format(self.flume.device_id, self.sensor_type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.sensor_type

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attr

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return VOLUME_GALLONS

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update current conditions."""
        usage = self.flume.get_usage()
        self._state = round(usage.get(self.sensor_type), 1)
