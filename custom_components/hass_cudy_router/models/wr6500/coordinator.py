from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)


class WR6500Coordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator for WR6500 routers.

    Constructor is intentionally flexible to support older tests and
    different call sites.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Supported constructor patterns:
        - WR6500Coordinator(hass, entry, api)
        - WR6500Coordinator(hass=hass, entry=entry, api=api)
        - WR6500Coordinator(hass=hass, host='192.168.0.1', api=api)
        """
        hass: Optional[HomeAssistant] = None
        entry = None
        api = None
        host = None

        update_interval = kwargs.pop("update_interval", None)

        # positional args
        if len(args) >= 1:
            hass = args[0]
        if len(args) >= 2:
            entry = args[1]
        if len(args) >= 3:
            api = args[2]

        # keyword args override
        hass = kwargs.pop("hass", hass)
        entry = kwargs.pop("entry", entry)
        api = kwargs.pop("api", api)
        host = kwargs.pop("host", host)

        if hass is None:
            raise TypeError("hass is required for WR6500Coordinator")

        self.hass: HomeAssistant = hass
        self.config_entry = entry
        self.api = api

        if host is None and entry is not None:
            try:
                host = (
                    entry.data.get("host")
                    or entry.unique_id
                    or getattr(entry, "entry_id", None)
                )
            except Exception:
                host = None

        self.host: Optional[str] = host

        if update_interval is None:
            update_interval = timedelta(seconds=30)

        super().__init__(
            hass,
            _LOGGER,
            name=f"cudy_wr6500_{self.host or 'unknown'}",
            update_interval=update_interval,
        )

        # Ensure data attribute exists for tests/entities
        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the WR6500 API."""
        if not self.api:
            raise UpdateFailed("No API client set on coordinator")

        try:
            result = await self.api.get_data()
            if result is None:
                result = {}
            self.data = result
            return result
        except Exception as err:
            _LOGGER.debug("Error updating WR6500 data: %s", err)
            raise UpdateFailed(err) from err


CudyRouterDataUpdateCoordinator = WR6500Coordinator
CudyRouterCoordinator = WR6500Coordinator