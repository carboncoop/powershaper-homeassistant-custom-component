import logging
import ipaddress
from urllib.parse import urlparse

import requests
import voluptuous as vol

from homeassistant.helpers import config_validation as cv

from . import const

_LOGGER = logging.getLogger(__name__)

SERVICE_REPORT_SPECIFIER_ID = "report_specifier_id"
SERVICE_VALUES = "values"
SERVICE_URL="url"

def validate_ip(value):
    """Validate ip."""
    try:
        urlparse(value)
        return value
    except:
        raise vol.Invalid("Invalid URL passed in: {}".format(value))

SERVICE_TELEMETRY_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_REPORT_SPECIFIER_ID): str,
            vol.Required(SERVICE_VALUES): dict,
        }
    ),
)

SERVICE_GET_TELEMETRY_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_REPORT_SPECIFIER_ID): str,
            vol.Required(SERVICE_URL): validate_ip,
        }
    ),
)

async def async_setup_services(hass):
    """Set up services for PowerShaper integration."""
    if hass.data.get(const.POWERSHAPER_SERVICES, False):
        return

    hass.data[const.POWERSHAPER_SERVICES] = True

    async def async_call_powershaper_service(service_call):
        """Service routing."""
        service = service_call.service
        service_data = service_call.data

        if service == const.SERVICE_TELEMETRY:
            await async_service_add_openadr_telemetry(hass, service_data)

        if service == const.SERVICE_GET_TELEMETRY:
            await async_service_get_openadr_telemetry_json_from_endpoint(hass, service_data)

        # Add any other service definition here

    hass.services.async_register(
        const.DOMAIN,
        const.SERVICE_TELEMETRY,
        async_call_powershaper_service,
        schema=SERVICE_TELEMETRY_SCHEMA,
    )
    
    hass.services.async_register(
        const.DOMAIN,
        const.SERVICE_GET_TELEMETRY,
        async_call_powershaper_service,
        schema=SERVICE_GET_TELEMETRY_SCHEMA,
    )

async def async_unload_services(hass):
    """Unload PowerShaper services."""
    if not hass.data.get(const.POWERSHAPER_SERVICES):
        return

    hass.data[const.POWERSHAPER_SERVICES] = False

    hass.services.async_remove(const.DOMAIN,const.SERVICE_TELEMETRY)

# Service definitions
async def async_service_add_openadr_telemetry(hass,data):
    oadr_agent=hass.data[const.DOMAIN][const.OADR_AGENT]
    oadr_agent.add_telemetry_json(data['report_specifier_id'],data['values'])
    
async def async_service_get_openadr_telemetry_json_from_endpoint(hass,data):
    
    report_specifier_id=data['report_specifier_id']
    
    if data['report_specifier_id'] == "ccoop_telemetry_evse_status":
        ip=urlparse(data['url']).netloc
    else:
        ip=data['url'] 
    
    _LOGGER.info("Doing GET /status on {}".format(ip))
    values=requests.get('http://{}/status'.format(ip)).json()
    _LOGGER.info("GET /status returned {}".format(values))
    
    # Get list of telemetry parameters from config.
    config = hass.data[const.DOMAIN][const.DATA_CONFIG]
    ven_config = config.get(const.DOMAIN)
    telemetry_parameters=ven_config.get('report_parameters').get(report_specifier_id).get("telemetry_parameters").keys()
    
    # Filter extra values from status that are not defined in config - if any are missing the call to add_telemetry_json below will error!
    values = {i:j for i,j in values.items() if i in telemetry_parameters}
    _LOGGER.info("Filtered telemetry values {}".format(values))
    
    oadr_agent=hass.data[const.DOMAIN][const.OADR_AGENT]
    oadr_agent.add_telemetry_json(report_specifier_id,values)
