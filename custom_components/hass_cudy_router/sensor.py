from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *
from .coordinator import CudyCoordinator


@dataclass(frozen=True)
class _SensorDef:
    module: str
    key: str
    icon: str | None
    entity_category: Any | None
    state_class: Any | None
    translation_key: str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: CudyCoordinator = data["coordinator"]

    entities: list[CudySensor] = []
    modules: dict[str, dict[str, Any]] = coordinator.data or {}

    for module_name, module_data in modules.items():
        if module_name == MODULE_DEVICE_LIST:
            continue

        sensor_defs = SENSORS.get(module_name, [])
        if not isinstance(module_data, dict) or not sensor_defs:
            continue

        for sd in sensor_defs:
            sensor_key = sd.get(SENSORS_KEY_KEY)
            if not sensor_key:
                continue

            # create sensor only if API actually returned a value for it
            # (avoid flooding HA with "Unknown" entities on firmwares that
            # don't expose certain fields/features).
            if sensor_key not in module_data:
                continue
            if module_data.get(sensor_key) is None:
                continue

            entities.append(
                CudySensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_def=_SensorDef(
                        module=module_name,
                        key=sensor_key,
                        icon=sd.get(SENSORS_KEY_ICON),
                        entity_category=sd.get(SENSORS_KEY_CATEGORY),
                        state_class=sd.get(SENSORS_KEY_CLASS),
                        translation_key=sensor_key,  # 🔑 THIS fixes translations
                    ),
                )
            )

    async_add_entities(entities)


class CudySensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CudyCoordinator,
        entry: ConfigEntry,
        sensor_def: _SensorDef,
    ) -> None:
        self.coordinator = coordinator
        self._entry = entry
        self._def = sensor_def

        self._attr_unique_id = (
            f"{entry.entry_id}_{sensor_def.module}_{sensor_def.key}"
        )

        system = (self.coordinator.data or {}).get(MODULE_SYSTEM, {})
        model = None
        if isinstance(system, dict):
            model = system.get(SENSOR_SYSTEM_MODEL)

        model_slug = (model or "cudy").lower().replace(" ", "_").replace("-", "_")
        module_slug = sensor_def.module.lower().replace("-", "_")
        key_slug = sensor_def.key.lower().replace("-", "_")

        self._attr_suggested_object_id = (
            f"{model_slug}_{module_slug}_{key_slug}"
        )

        self._attr_icon = sensor_def.icon
        self._attr_entity_category = sensor_def.entity_category
        self._attr_state_class = sensor_def.state_class
        self._attr_translation_key = sensor_def.translation_key

    @property
    def available(self) -> bool:
        return getattr(self.coordinator, "last_update_success", True)

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        module = data.get(self._def.module, {})
        if not isinstance(module, dict):
            return None
        return module.get(self._def.key)

    async def async_added_to_hass(self) -> None:
        self.coordinator.async_add_listener(self.async_write_ha_state)

    @property
    def device_info(self) -> DeviceInfo:
        entry_uid = self._entry.entry_id

        model = None
        sw_version = None
        system = (self.coordinator.data or {}).get(MODULE_SYSTEM, {})
        if isinstance(system, dict):
            model = system.get(SENSOR_SYSTEM_MODEL)
            sw_version = system.get(SENSOR_SYSTEM_FIRMWARE_VERSION)

        return DeviceInfo(
            identifiers={(DOMAIN, entry_uid)},
            name=f"Cudy Router {model}" if model else "Cudy Router",
            manufacturer="Cudy",
            model=model,
            sw_version=sw_version,
        )