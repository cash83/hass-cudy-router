from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.hass_cudy_router.models.p5.coordinator import (
    P5Coordinator,
    CudyRouterDataUpdateCoordinator,
    CudyRouterCoordinator,
)


@pytest.mark.asyncio
async def test_coordinator_init_with_positional_args(hass: HomeAssistant):
    api = AsyncMock()
    entry = MagicMock()
    entry.data = {"host": "192.168.0.1"}

    coord = P5Coordinator(hass, entry, api)

    assert coord.hass is hass
    assert coord.api is api
    assert coord.host == "192.168.0.1"
    assert coord.data == {}


@pytest.mark.asyncio
async def test_coordinator_init_with_keyword_args(hass: HomeAssistant):
    api = AsyncMock()

    coord = P5Coordinator(
        hass=hass,
        host="router.local",
        api=api,
    )

    assert coord.host == "router.local"
    assert coord.api is api


@pytest.mark.asyncio
async def test_coordinator_backwards_compatible_aliases(hass: HomeAssistant):
    api = AsyncMock()

    c1 = CudyRouterDataUpdateCoordinator(hass=hass, host="1.1.1.1", api=api)
    c2 = CudyRouterCoordinator(hass=hass, host="2.2.2.2", api=api)

    assert isinstance(c1, P5Coordinator)
    assert isinstance(c2, P5Coordinator)
    assert c1.host == "1.1.1.1"
    assert c2.host == "2.2.2.2"


@pytest.mark.asyncio
async def test_coordinator_async_update_success(hass: HomeAssistant):
    api = AsyncMock()
    api.get_data = AsyncMock(return_value={"foo": "bar"})

    coord = P5Coordinator(hass=hass, host="router", api=api)

    data = await coord._async_update_data()

    assert data == {"foo": "bar"}
    assert coord.data == {"foo": "bar"}
    api.get_data.assert_awaited_once()


@pytest.mark.asyncio
async def test_coordinator_async_update_failure(hass: HomeAssistant):
    api = AsyncMock()
    api.get_data = AsyncMock(side_effect=RuntimeError("boom"))

    coord = P5Coordinator(hass=hass, host="router", api=api)

    with pytest.raises(UpdateFailed):
        await coord._async_update_data()