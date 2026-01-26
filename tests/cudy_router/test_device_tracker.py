from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.hass_cudy_router.const import DOMAIN, OPTIONS_DEVICE_LIST, MODULE_DEVICES
from custom_components.hass_cudy_router.models.base_device_tracker import BaseCudyDeviceTracker
from custom_components.hass_cudy_router.models.wr6500.device_tracker import (
    async_setup_entry,
)

try:
    from custom_components.hass_cudy_router.const import DEVICE_LIST as DEVICE_LIST_KEY  # type: ignore
except Exception:
    DEVICE_LIST_KEY = "device_list"

try:
    from custom_components.hass_cudy_router.const import DEVICE_COUNT as DEVICE_COUNT_KEY  # type: ignore
except Exception:
    DEVICE_COUNT_KEY = "device_count"


@pytest.fixture
def coordinator() -> MagicMock:
    """Create a lightweight coordinator mock."""
    c = MagicMock()
    c.host = "192.168.0.1"
    c.last_update_success = True
    c.data = {}
    return c


def _set_devices(coordinator: MagicMock, device_list: list[dict[str, Any]]) -> None:
    """Helper to inject devices into coordinator data."""
    coordinator.data = {
        MODULE_DEVICES: {
            DEVICE_LIST_KEY: device_list,
            DEVICE_COUNT_KEY: len(device_list),
        }
    }


@pytest.mark.asyncio
async def test_async_setup_entry_adds_entities(
    hass: HomeAssistant, coordinator: MagicMock
):
    """async_setup_entry should create one entity per MAC in OPTIONS_DEVICE_LIST."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.options = {OPTIONS_DEVICE_LIST: "AA:BB:CC:DD:EE:FF, 11-22-33-44-55-66"}

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    added: list[Any] = []

    def _add_entities(entities) -> None:
        added.extend(list(entities))

    await async_setup_entry(hass, entry, _add_entities)

    assert len(added) == 2
    assert all(isinstance(ent, BaseCudyDeviceTracker) for ent in added)

    # MACs should be normalized to lowercase
    assert added[0]._mac == "aa:bb:cc:dd:ee:ff"
    assert added[1]._mac == "11-22-33-44-55-66".lower()


def test_tracker_available_reflects_coordinator_state(coordinator: MagicMock):
    """available should mirror coordinator.last_update_success."""
    tracker = BaseCudyDeviceTracker(coordinator, "aa:bb:cc:dd:ee:ff")

    coordinator.last_update_success = True
    assert tracker.available is True

    coordinator.last_update_success = False
    assert tracker.available is False


def test_tracker_is_connected_wired_true(coordinator: MagicMock):
    """Wired device should be connected regardless of signal."""
    _set_devices(
        coordinator,
        [
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "connection_type": "wired",
                "signal": "",
            }
        ],
    )

    tracker = BaseCudyDeviceTracker(coordinator, "aa:bb:cc:dd:ee:ff")
    assert tracker.is_connected is True


def test_tracker_is_connected_wifi_with_signal_true(coordinator: MagicMock):
    """Wireless device with non-empty/non-'---' signal should be connected."""
    _set_devices(
        coordinator,
        [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "connection_type": "wifi",
                "signal": "-53",
            }
        ],
    )

    tracker = BaseCudyDeviceTracker(coordinator, "aa:bb:cc:dd:ee:ff")
    assert tracker.is_connected is True


@pytest.mark.parametrize("signal", ["", "   ", "---", None])
def test_tracker_is_connected_wifi_without_signal_false(
    coordinator: MagicMock, signal
):
    """Wireless device without meaningful signal should be disconnected."""
    _set_devices(
        coordinator,
        [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "connection_type": "wifi",
                "signal": signal,
            }
        ],
    )

    tracker = BaseCudyDeviceTracker(coordinator, "aa:bb:cc:dd:ee:ff")
    assert tracker.is_connected is False


def test_tracker_is_connected_missing_device_false(coordinator: MagicMock):
    """If MAC not present in device_list, is_connected should be False."""
    _set_devices(
        coordinator,
        [
            {
                "mac": "11:22:33:44:55:66",
                "connection_type": "wired",
            }
        ],
    )

    tracker = BaseCudyDeviceTracker(coordinator, "aa:bb:cc:dd:ee:ff")
    assert tracker.is_connected is False


def test_extra_state_attributes_returns_device_dict(coordinator: MagicMock):
    """extra_state_attributes should return full device dict for matching MAC."""
    device = {
        "mac": "aa:bb:cc:dd:ee:ff",
        "connection_type": "wifi",
        "signal": "-60",
        "ip": "192.168.0.50",
        "hostname": "Phone",
    }
    _set_devices(coordinator, [device])

    tracker = BaseCudyDeviceTracker(coordinator, "aa:bb:cc:dd:ee:ff")
    assert tracker.extra_state_attributes == device


def test_unique_id_and_name_and_device_info(coordinator: MagicMock):
    """Unique id formatting and device_info should be stable."""
    tracker = BaseCudyDeviceTracker(coordinator, "aa:bb:cc:dd:ee:ff")

    assert tracker.unique_id == "cudy_device_aabbccddeeff"
    assert tracker.name == "Cudy Device aa:bb:cc:dd:ee:ff"

    # Attached to router device
    assert tracker.device_info is not None
    assert tracker.device_info["identifiers"] == {(DOMAIN, "192.168.0.1")}