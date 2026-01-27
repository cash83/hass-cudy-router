from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.hass_cudy_router.const import DOMAIN, OPTIONS_DEVICE_LIST
from custom_components.hass_cudy_router.models.base_coordinator import resolve_coordinator
from custom_components.hass_cudy_router.models.base_device_tracker import BaseCudyDeviceTracker
from custom_components.hass_cudy_router.models.r700 import R700Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = resolve_coordinator(stored, coordinator_cls=R700Coordinator)

    macs = entry.options.get(OPTIONS_DEVICE_LIST, "")
    tracked = [m.strip().lower() for m in macs.split(",") if m.strip()]

    async_add_entities(
        BaseCudyDeviceTracker(coordinator, mac) for mac in tracked
    )