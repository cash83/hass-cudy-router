from __future__ import annotations

from typing import Any, Mapping

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class BaseCudySensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self,
        coordinator: Any,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        *,
        module_map: Mapping[str, str],
        name_prefix: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._module_map = dict(module_map)

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True

        if name_prefix:
            self._attr_name = f"{name_prefix} {description.name}"

    def _read_from_module(self, module_key: str, key: str) -> Any:
        data = getattr(self.coordinator, "data", None) or {}
        module = data.get(module_key, {})
        if isinstance(module, dict):
            return module.get(key)
        return None

    @property
    def native_value(self) -> Any:
        data = getattr(self.coordinator, "data", None) or {}

        desc = getattr(self, "entity_description", None)
        if not desc:
            return None

        key = desc.key

        for prefix, module_key in self._module_map.items():
            if key.startswith(prefix):
                return self._read_from_module(module_key, key)

        return data.get(key)