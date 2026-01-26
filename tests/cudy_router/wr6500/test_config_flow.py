"""Tests for hass_cudy_router config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PROTOCOL,
    CONF_USERNAME,
)

from custom_components.hass_cudy_router.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow_shows_form_on_init(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM


@pytest.mark.asyncio
async def test_config_flow_success(hass):
    with patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.authenticate",
        new=AsyncMock(return_value=True),
    ), patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.close",
        new=AsyncMock(return_value=None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "http",
                CONF_HOST: "192.168.1.1",
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "admin",
            },
        )

        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result2["data"][CONF_HOST] == "192.168.1.1"


@pytest.mark.asyncio
async def test_config_flow_invalid_auth(hass):
    with patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.authenticate",
        new=AsyncMock(return_value=False),
    ), patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.close",
        new=AsyncMock(return_value=None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "http",
                CONF_HOST: "192.168.1.1",
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "wrong",
            },
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass):
    with patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.authenticate",
        new=AsyncMock(side_effect=OSError("boom")),
    ), patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.close",
        new=AsyncMock(return_value=None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "http",
                CONF_HOST: "192.168.1.1",
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "admin",
            },
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_config_flow_unknown_error(hass):
    with patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.authenticate",
        new=AsyncMock(side_effect=RuntimeError("unexpected")),
    ), patch(
        "custom_components.hass_cudy_router.config_flow.CudyClient.close",
        new=AsyncMock(return_value=None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "http",
                CONF_HOST: "192.168.1.1",
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "admin",
            },
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["errors"]["base"] == "cannot_connect"