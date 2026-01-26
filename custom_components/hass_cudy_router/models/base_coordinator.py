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


class BaseCudyCoordinator(DataUpdateCoordinator):

    def __init__(
        self,
        *args,
        name_prefix: str,
        update_interval: timedelta | None = None,
        **kwargs: Any,
    ) -> None:
        hass: Optional[HomeAssistant] = None
        entry = None
        api = None
        host = None

        if len(args) >= 1:
            hass = args[0]
        if len(args) >= 2:
            entry = args[1]
        if len(args) >= 3:
            api = args[2]

        hass = kwargs.pop("hass", hass)
        entry = kwargs.pop("entry", entry)
        api = kwargs.pop("api", api)
        host = kwargs.pop("host", host)

        if update_interval is None:
            update_interval = kwargs.pop("update_interval", None)
        else:
            kwargs.pop("update_interval", None)

        if hass is None:
            raise TypeError("hass is required for BaseCudyCoordinator")

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
            name=f"{name_prefix}_{self.host or 'unknown'}",
            update_interval=update_interval,
        )

        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        if not self.api:
            raise UpdateFailed("No API client set on coordinator")

        try:
            result = await self.api.get_data()
            if result is None:
                result = {}
            self.data = result
            return result
        except Exception as err:
            _LOGGER.debug("Error updating Cudy router data: %s", err)
            raise UpdateFailed(err) from err