from __future__ import annotations

from custom_components.hass_cudy_router.models.base_coordinator import BaseCudyCoordinator


class R700Coordinator(BaseCudyCoordinator):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, name_prefix="cudy_r700", **kwargs)


CudyRouterDataUpdateCoordinator = R700Coordinator
CudyRouterCoordinator = R700Coordinator