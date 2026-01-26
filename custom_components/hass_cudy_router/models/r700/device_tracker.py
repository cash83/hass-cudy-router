from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.hass_cudy_router.const import DOMAIN, OPTIONS_DEVICE_LIST
from .coordinator import R700Coordinator
from ..base_device_tracker import BaseCudyDeviceTracker


def _resolve_coordinator(stored: Any) -> R700Coordinator:
    if isinstance(stored, R700Coordinator):
        return stored
    if isinstance(stored, dict):
        if "coordinator" in stored:
            return stored["coordinator"]
        if "integration" in stored:
            return stored["integration"].coordinator
    if hasattr(stored, "coordinator"):
        return stored.coordinator
    if hasattr(stored, "data"):
        return stored  # type: ignore
    raise ValueError("Could not resolve R700Coordinator")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = _resolve_coordinator(stored)

    macs = entry.options.get(OPTIONS_DEVICE_LIST, "")
    tracked = [m.strip().lower() for m in macs.split(",") if m.strip()]

    async_add_entities(
        BaseCudyDeviceTracker(coordinator, mac) for mac in tracked
    )