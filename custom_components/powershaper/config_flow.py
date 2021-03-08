import logging

import requests
import voluptuous as vol

from . import balena
from . import const
from homeassistant import config_entries

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(const.DOMAIN)
class PowerShaperFlowHandler(config_entries.ConfigFlow):
    """Configuration flow for the openadr ven component."""

    async def async_step_get_ca(self):
        """Gets the certificate authority cert from a vtn endpoint."""
        config = self.hass.data[const.DOMAIN][const.DATA_CONFIG]
        ven_config = config.get(const.DOMAIN)
        ca_response = requests.get(url=ven_config.get(const.CA_CERT_URL))
        ca_response.raise_for_status()

        try:
            ca_cert_file = open(ven_config.get(const.CA_CERT_FILEPATH), "w")
            ca_cert_file.write(ca_response.text)
            ca_cert_file.close()
        except OSError as error:
            _LOGGER.exception("file error: %s", error)
            raise OSError

        return self.async_create_entry(
            title="PowerShaper", data={"config_worked": "yes"}
        )

    async def async_step_user(self, user_input):
        """Handle a flow initialized by the user."""
        if user_input is not None:

            try:
                await self._call_hub_for_certificate(
                    balena.get_device_uuid, user_input[const.INSTALLATION_SHORTCODE]
                )
            except requests.HTTPError as e:
                _LOGGER.exception(f"Error getting client PEM bundle {e}")
                return self.async_abort(reason="problem_getting_client_pem")
            except OSError:
                return self.async_abort(reason="problem_saving_client_pem")

            try:
                return await self.async_step_get_ca()
            except requests.HTTPError:
                return self.async_abort(reason="problem_getting_CA_cert")
            except OSError:
                return self.async_abort(reason="problem_saving_CA_cert")

        return await self._show_pem_input_form()

    async def _show_pem_input_form(self):
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(const.INSTALLATION_SHORTCODE): str}),
        )

    async def _call_hub_for_certificate(self, device_id: str, shortcode: str):
        """Use the shortcode to authenticate against a hub url.
        Send the balena device uuid and shortcode.
        Get back a pem bundle and store it as a file in const.CLIENT_PEM_BUNDLE_FILEPATH
        """
        _LOGGER.info("installation shortcode is %s", shortcode)
        config = self.hass.data[const.DOMAIN][const.DATA_CONFIG]
        ven_config = config.get(const.DOMAIN)
        payload = {
            "hems_id": balena.get_device_uuid(),
            "code": shortcode,
            "hems_name": balena.get_device_name(),
        }
        hub_response = requests.post(
            url=ven_config.get(const.HUB_HEMS_REGISTRATION_URL), data=payload
        )
        _LOGGER.info("request made: %s", hub_response.status_code)
        hub_response.raise_for_status()

        try:
            pem_file = open(ven_config.get(const.CLIENT_PEM_BUNDLE_FILEPATH), "w")
            pem_file.write(hub_response.json()["pem_bundle"])

            pem_file.close()
        except OSError as error:
            _LOGGER.info("file error: %s", error)
            raise OSError
        return
