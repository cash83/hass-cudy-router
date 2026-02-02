from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hass_cudy_router.const import DOMAIN, SENSOR_SYSTEM_FIRMWARE_VERSION
from custom_components.hass_cudy_router.coordinator import CudyCoordinator


@pytest.mark.asyncio
async def test_coordinator_refresh_sets_data(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "test"}, options={})
    entry.add_to_hass(hass)

    api = AsyncMock()
    api.get_data.return_value = {"system": {SENSOR_SYSTEM_FIRMWARE_VERSION: "X"}}

    c = CudyCoordinator(hass=hass, entry=entry, api=api, host="test")

    await c.async_refresh()

    assert c.data["system"][SENSOR_SYSTEM_FIRMWARE_VERSION] == "X"


@pytest.mark.asyncio
async def test_coordinator_missing_api_raises_updatefailed(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "test"}, options={})
    entry.add_to_hass(hass)

    c = CudyCoordinator(hass=hass, entry=entry, api=None, host="test")

    with pytest.raises(UpdateFailed):
        await c._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_api_exception_wraps_updatefailed(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "test"}, options={})
    entry.add_to_hass(hass)

    api = AsyncMock()
    api.get_data.side_effect = RuntimeError("boom")

    c = CudyCoordinator(hass=hass, entry=entry, api=api, host="test")

    with pytest.raises(UpdateFailed):
        await c._async_update_data()