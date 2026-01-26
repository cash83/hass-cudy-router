from __future__ import annotations

from custom_components.hass_cudy_router.models.base_coordinator import BaseCudyCoordinator


class WR6500Coordinator(BaseCudyCoordinator):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, name_prefix="cudy_wr6500", **kwargs)


# Backwards-compatible aliases for older code/tests
CudyRouterDataUpdateCoordinator = WR6500Coordinator
CudyRouterCoordinator = WR6500Coordinator