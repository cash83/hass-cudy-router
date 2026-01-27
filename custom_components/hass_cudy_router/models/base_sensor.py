from __future__ import annotations

from typing import Any, Iterable, List, Optional, Type

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from .base_coordinator import BaseCudyCoordinator
from .base_coordinator import resolve_coordinator as base_resolve_coordinator


class BaseCudySensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self,
        coordinator: BaseCudyCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        module_map: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = description
        self._entry = entry
        self._module_map = module_map or {}

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        data = getattr(self.coordinator, "data", None) or {}
        if not data:
            return None

        key = self.entity_description.key

        for prefix, module_name in self._module_map.items():
            if key.startswith(prefix):
                module_data = data.get(module_name, {})
                return module_data.get(key)

        return data.get(key)

    async def async_added_to_hass(self) -> None:
        self.coordinator.async_add_listener(self.async_write_ha_state)


async def async_setup_model_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    descriptions: Iterable[SensorEntityDescription],
    *,
    module_map: Optional[dict[str, str]] = None,
    coordinator_cls: Optional[Type[BaseCudyCoordinator]] = None,
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    # Prefer base resolve_coordinator from base_coordinator if present.
    try:
        coordinator = base_resolve_coordinator(stored, coordinator_cls=coordinator_cls)
    except Exception:
        # Fallback: basic naive resolver (keeps old behavior)
        coordinator = _fallback_resolve_coordinator(stored)

    entities: List[BaseCudySensor] = [
        BaseCudySensor(coordinator, entry, desc, module_map=module_map) for desc in descriptions
    ]
    async_add_entities(entities)


def _fallback_resolve_coordinator(stored: Any) -> BaseCudyCoordinator:
    if isinstance(stored, BaseCudyCoordinator):
        return stored

    if isinstance(stored, dict):
        if "coordinator" in stored and isinstance(stored["coordinator"], BaseCudyCoordinator):
            return stored["coordinator"]
        if "integration" in stored:
            integ = stored["integration"]
            c = getattr(integ, "coordinator", None)
            if isinstance(c, BaseCudyCoordinator):
                return c

    if hasattr(stored, "coordinator") and isinstance(getattr(stored, "coordinator"), BaseCudyCoordinator):
        return getattr(stored, "coordinator")

    if hasattr(stored, "data"):
        return stored

    raise ValueError("Could not resolve BaseCudyCoordinator from hass.data")