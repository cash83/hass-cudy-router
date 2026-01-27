from __future__ import annotations

from custom_components.hass_cudy_router.models.base_coordinator import BaseCudyCoordinator


class GenericCoordinator(BaseCudyCoordinator):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, name_prefix="cudy_p5", **kwargs)


CudyRouterDataUpdateCoordinator = GenericCoordinator
CudyRouterCoordinator = GenericCoordinator