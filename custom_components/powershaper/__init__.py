"""A Home Assistant component for the PowerShaper service"""
import logging
import os
import uuid

import voluptuous as vol

from . import const
from . import balena
from . import services

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import HomeAssistantType

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        const.DOMAIN: vol.Schema(
            {
                vol.Required(const.VTN_ID): cv.string,
                vol.Required(const.VTN_ADDRESS): cv.string,
                vol.Required(const.SECURITY_LEVEL): cv.string,
                vol.Required(const.POLL_INTERVAL_SECS): int,
                vol.Required(const.LOG_XML): bool,
                vol.Required(const.OPT_TIMEOUT_SECS): int,
                vol.Required(const.OPT_DEFAULT_DECISION): cv.string,
                vol.Required(const.REQUEST_EVENTS_ON_STARTUP): bool,
                vol.Required(const.REPORT_PARAMETERS): dict,
                vol.Required(const.CLIENT_PEM_BUNDLE_FILEPATH): cv.string,
                vol.Required(const.CA_CERT_FILEPATH): cv.string,
                vol.Required(const.CA_CERT_URL): cv.url,
                vol.Required(const.HUB_HEMS_REGISTRATION_URL): cv.url,
                vol.Required(const.DB_FILEPATH): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistantType, config: ConfigEntry) -> bool:
    """ Set up the OpenADR Ven client"""

    hass.data[const.DOMAIN] = {}
    hass.data[const.DOMAIN][const.DATA_CLIENT] = {}

    if const.DOMAIN not in config:
        return True

    # Store config for use during entry setup:
    hass.data[const.DOMAIN][const.DATA_CONFIG] = config

    # Report information about the Balena environment
    hass.states.async_set("powershaper.BALENA_DEVICE_UUID", balena.get_device_uuid())
    hass.states.async_set("powershaper.BALENA_DEVICE_NAME_AT_INIT", balena.get_device_name())

    # Return boolean to indicate that initialization was successful.
    _LOGGER.info("PowerShaper setup complete")
    return True


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry) -> bool:
    """Setup a VEN from a config flow entry"""

    config = hass.data[const.DOMAIN][const.DATA_CONFIG]

    from pyoadr_ven import OpenADRVenAgent

    ven_config = config.get(const.DOMAIN)
    oadr_agent = OpenADRVenAgent(
        ven_id=balena.get_device_uuid(),
        vtn_id=ven_config.get(const.VTN_ID),
        vtn_address=ven_config.get(const.VTN_ADDRESS),
        poll_interval_secs=ven_config.get(const.POLL_INTERVAL_SECS),
        log_xml=ven_config.get(const.LOG_XML),
        opt_timeout_secs=ven_config.get(const.OPT_TIMEOUT_SECS),
        opt_default_decision=ven_config.get(const.OPT_DEFAULT_DECISION),
        report_parameters=ven_config.get(const.REPORT_PARAMETERS),
        client_pem_bundle=ven_config.get(const.CLIENT_PEM_BUNDLE_FILEPATH),
        vtn_ca_cert=ven_config.get(const.CA_CERT_FILEPATH),
        db_filepath=ven_config.get(const.DB_FILEPATH),
    )

    hass.data[const.DOMAIN][const.OADR_AGENT] = oadr_agent

    # Register services defined in services.py
    await services.async_setup_services(hass)

    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )

    # Return boolean to indicate that initialization was successful.
    _LOGGER.info("PowerShaper entry setup complete")
    return True
