"""Binary sensor for the PowerShaper service.
   If True, an OpenADR event is in progress
"""
import logging
from datetime import timedelta

from . import const
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_devices
) -> bool:

    oadr_agent = hass.data[const.DOMAIN][const.OADR_AGENT]

    if oadr_agent:
        async_add_devices([VENConnectedSensor(hass, oadr_agent)])


class VENConnectedSensor(BinarySensorEntity):
    def __init__(self, hass, agent):
        self._name = const.BINARY_SENSOR_NAME
        self._state = False
        self._agent = agent
        self._agent.request_events()
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if an event is in progress"""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    def update(self):
        self._agent.tick()
        active_or_pending_events = self._agent.active_or_pending_events
        self._state = self._agent.is_event_in_progress

        for event in self._agent.active_events:
            _LOGGER.info(f"Event Active: {str(event)}")
        for event in active_or_pending_events:
            _LOGGER.info(f"Event Active or Pending: {str(event)}")

        # Create dictionary of active/pending events and add to attributes
        if active_or_pending_events:
            new_attributes = {}
            for event in active_or_pending_events:
                new_attributes[event["event_id"]] = {
                    "start_time": event["start_time"],
                    "end_time": event["end_time"],
                    "request_id": event["request_id"],
                    "created": event["created"],
                    "signals": event["signals"],
                    "status": event["status"],
                    "opt_type": event["opt_type"],
                    "priority": event["priority"],
                    "modification_number": event["modification_number"],
                    "test_event": event["test_event"],
                }

            # Set attributes on this entity using setter
            self._attributes = new_attributes
