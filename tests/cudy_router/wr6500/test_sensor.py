"""Tests for the Cudy Router WR6500 sensor platform (const.py key mapping)."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.hass_cudy_router.const import (
    DOMAIN,
    MODULE_SYSTEM,
    MODULE_WAN,
    MODULE_LAN,
    MODULE_DEVICES,
    SENSOR_FIRMWARE_VERSION,
    SENSOR_WAN_IP,
    SENSOR_LAN_IP,
    SENSOR_DEVICE_COUNT,
)
from custom_components.hass_cudy_router.models.wr6500.coordinator import WR6500Coordinator
from custom_components.hass_cudy_router.models.wr6500.sensor import (
    SENSOR_TYPES,
    WR6500Sensor,
    async_setup_entry,
)


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
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
) -> WR6500Coordinator:
    config_entry.add_to_hass(hass)
    coord = WR6500Coordinator(hass=hass, entry=config_entry, api=mock_api)
    coord.data = {}
    return coord


def _desc_by_key(key: str):
    for d in SENSOR_TYPES:
        if d.key == key:
            return d
    raise AssertionError(f"Missing sensor description for key={key}")


@pytest.mark.asyncio
async def test_async_setup_entry_adds_all_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    coordinator: WR6500Coordinator,
):
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    added: list[Any] = []

    def _add_entities(entities):
        added.extend(list(entities))

    await async_setup_entry(hass, config_entry, _add_entities)

    assert len(added) == len(SENSOR_TYPES)
    assert all(isinstance(e, WR6500Sensor) for e in added)
    assert all(getattr(e, "unique_id", None) for e in added)


def test_native_value_system_key(coordinator: WR6500Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_FIRMWARE_VERSION)
    coordinator.data = {MODULE_SYSTEM: {SENSOR_FIRMWARE_VERSION: "1.2.3"}}
    entity = WR6500Sensor(coordinator, desc, config_entry)
    assert entity.native_value == "1.2.3"


def test_native_value_wan_key(coordinator: WR6500Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_WAN_IP)
    coordinator.data = {MODULE_WAN: {SENSOR_WAN_IP: "203.0.113.10"}}
    entity = WR6500Sensor(coordinator, desc, config_entry)
    assert entity.native_value == "203.0.113.10"


def test_native_value_lan_key(coordinator: WR6500Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_LAN_IP)
    coordinator.data = {MODULE_LAN: {SENSOR_LAN_IP: "192.168.0.1"}}
    entity = WR6500Sensor(coordinator, desc, config_entry)
    assert entity.native_value == "192.168.0.1"


def test_native_value_devices_key(coordinator: WR6500Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_DEVICE_COUNT)
    coordinator.data = {MODULE_DEVICES: {SENSOR_DEVICE_COUNT: 7}}
    entity = WR6500Sensor(coordinator, desc, config_entry)
    assert entity.native_value == 7


def test_native_value_missing_module_returns_none(coordinator: WR6500Coordinator, config_entry: MockConfigEntry):
    desc = _desc_by_key(SENSOR_WAN_IP)
    coordinator.data = {MODULE_SYSTEM: {SENSOR_FIRMWARE_VERSION: "1.2.3"}}
    entity = WR6500Sensor(coordinator, desc, config_entry)
    assert entity.native_value is None