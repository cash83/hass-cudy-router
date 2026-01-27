from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, Optional, Final

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.hass_cudy_router.const import DOMAIN, BUTTON_REBOOT
from custom_components.hass_cudy_router.models.base_coordinator import BaseCudyCoordinator, resolve_coordinator

PressFn = Callable[[HomeAssistant, ConfigEntry, BaseCudyCoordinator], Awaitable[None]]

@dataclass(frozen=True)
class CudyButtonSpec:
    description: ButtonEntityDescription
    press: PressFn


class BaseCudyButton(CoordinatorEntity, ButtonEntity):

    def __init__(
        self,
        coordinator: BaseCudyCoordinator,
        entry: ConfigEntry,
        spec: CudyButtonSpec,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = spec.description
        self._press = spec.press
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_{self.entity_description.key}"
        self._attr_has_entity_name = True

    async def async_press(self) -> None:
        await self._press(self.hass, self._entry, self.coordinator)

async def _press_reboot(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: BaseCudyCoordinator,
) -> None:
    await coordinator.api.reboot()
    await coordinator.async_request_refresh()

BUTTON_SPECS: Final = (
    CudyButtonSpec(
        description=ButtonEntityDescription(
            key=BUTTON_REBOOT,
            name="Reboot",
            icon="mdi:restart",
        ),
        press=_press_reboot,
    ),
)

async def async_setup_model_buttons(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
    specs: Iterable[CudyButtonSpec],
    *,
    coordinator_cls: Optional[type[BaseCudyCoordinator]] = None,
) -> None:
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = resolve_coordinator(stored, coordinator_cls=coordinator_cls)

    async_add_entities(BaseCudyButton(coordinator, entry, spec) for spec in specs)