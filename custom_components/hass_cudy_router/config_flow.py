"""Config flow for Cudy Router integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, OPTIONS_DEVICELIST
from .client import CudyClient

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PROTOCOL, default="http"): str,
        vol.Required(CONF_HOST, default="192.168.10.1"): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    This will attempt to authenticate using the async CudyClient.
    """
    protocol = data.get(CONF_PROTOCOL, "http")
    use_https = protocol.lower() in ("https", "ssl", "tls")
    host = data[CONF_HOST]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    client = CudyClient(host=host, username=username, password=password, use_https=use_https)

    try:
        ok = await client.authenticate()
    except Exception as err:
        _LOGGER.debug("Error while validating connection to %s: %s", host, err)
        raise CannotConnect from err
    finally:
        try:
            await client.close()
        except Exception:
            pass

    if not ok:
        raise InvalidAuth

    return {"title": f"Cudy Router ({host})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cudy Router."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(CONF_SCAN_INTERVAL, 30),
                    ): int,
                    vol.Optional(
                        OPTIONS_DEVICELIST,
                        default=self.config_entry.options.get(OPTIONS_DEVICELIST, ""),
                    ): str,
                }
            ),
        )