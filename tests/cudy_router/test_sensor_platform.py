import pytest
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.api import CudyApi
from custom_components.hass_cudy_router.coordinator import CudyCoordinator
from custom_components.hass_cudy_router.sensor import async_setup_entry as sensor_setup
from tests.cudy_router.fixtures import html_exists, FakeClient


@pytest.mark.asyncio
@pytest.mark.parametrize("model", CUDY_DEVICES)
async def test_sensor_platform(hass: HomeAssistant, model: str):
    client = FakeClient(model)
    api = CudyApi(client)
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = model
    entry.data = {"host": "test.local"}

    coordinator = CudyCoordinator(hass=hass, entry=entry, api=api, host="test.local")

    data = await coordinator._async_update_data()
    coordinator.data = data

    assert MODULE_SYSTEM in coordinator.data.keys()
    assert coordinator.data[MODULE_SYSTEM][SENSOR_SYSTEM_FIRMWARE_VERSION] is not None

    for module in SENSORS.keys():
        if html_exists(model, module):
            assert module in coordinator.data.keys()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}

    added = []
    def add_entities(entities):
        added.extend(entities)

    await sensor_setup(hass, entry, add_entities)

    fw_entities = [e for e in added if getattr(e, "unique_id", "").endswith(SENSOR_SYSTEM_FIRMWARE_VERSION)]
    assert fw_entities
    assert fw_entities[0].native_value == coordinator.data[MODULE_SYSTEM][SENSOR_SYSTEM_FIRMWARE_VERSION]