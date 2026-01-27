from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.hass_cudy_router.const import (
    DOMAIN,
    MODULE_SYSTEM,
    MODULE_LAN,
    MODULE_DEVICES,
    SENSOR_SYSTEM_FIRMWARE_VERSION,
    SENSOR_WAN_IP,
    SENSOR_LAN_IP,
    SENSOR_DEVICE_COUNT,
)
from custom_components.hass_cudy_router.models.base_sensor import BaseCudySensor
from custom_components.hass_cudy_router.models.p5.coordinator import P5Coordinator
from custom_components.hass_cudy_router.models.p5 import sensor as p5_sensor


@pytest.fixture
def config_entry() -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Cudy Router",
        data={
            "host": "192.168.0.1",
            "username": "admin",
            "password": "admin",
            "protocol": "http",
        },
        options={},
        unique_id="192.168.0.1",
    )
    return entry


@pytest.fixture
def mock_api():
    class _Api:
        async def get_data(self) -> dict[str, Any]:
            return {}
    return _Api()


@pytest.fixture
def coordinator(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_api,
) -> P5Coordinator:
    config_entry.add_to_hass(hass)
    coord = P5Coordinator(hass=hass, entry=config_entry, api=mock_api)
    coord.data = {}
    return coord


@pytest.mark.asyncio
async def test_async_setup_entry_adds_all_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    coordinator: P5Coordinator,
):
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    added: list[Any] = []

    def _add_entities(entities):
        added.extend(list(entities))

    await p5_sensor.async_setup_entry(hass, config_entry, _add_entities)

    assert len(added) == len(p5_sensor.SENSOR_DESCRIPTIONS)
    assert all(isinstance(e, BaseCudySensor) for e in added)
    assert all(getattr(e, "unique_id", None) for e in added)


def _desc_by_key(key: str):
    for d in p5_sensor.SENSOR_DESCRIPTIONS:
        if d.key == key:
            return d
    raise AssertionError(f"Missing sensor description for key={key}")


def test_native_value_system_key(coordinator: P5Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_SYSTEM_FIRMWARE_VERSION)

    coordinator.data = {
        MODULE_SYSTEM: {SENSOR_SYSTEM_FIRMWARE_VERSION: "1.2.3"},
    }

    entity = BaseCudySensor(coordinator, config_entry, desc, module_map=p5_sensor.P5_MODULE_MAP)
    assert entity.native_value == "1.2.3"


def test_native_value_lan_key(coordinator: P5Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_LAN_IP)

    coordinator.data = {
        MODULE_LAN: {SENSOR_LAN_IP: "192.168.0.1"},
    }

    entity = BaseCudySensor(coordinator, config_entry, desc, module_map=p5_sensor.P5_MODULE_MAP)
    assert entity.native_value == "192.168.0.1"


def test_native_value_devices_key(coordinator: P5Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_DEVICE_COUNT)

    coordinator.data = {
        MODULE_DEVICES: {SENSOR_DEVICE_COUNT: 7},
    }

    entity = BaseCudySensor(coordinator, config_entry, desc, module_map=p5_sensor.P5_MODULE_MAP)
    assert entity.native_value == 7


def test_native_value_missing_module_returns_none(coordinator: P5Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_LAN_IP)

    coordinator.data = {
        MODULE_SYSTEM: {SENSOR_SYSTEM_FIRMWARE_VERSION: "1.2.3"},
    }

    entity = BaseCudySensor(coordinator, config_entry, desc, module_map=p5_sensor.P5_MODULE_MAP)
    assert entity.native_value is None