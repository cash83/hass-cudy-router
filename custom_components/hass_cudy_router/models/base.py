from __future__ import annotations
from abc import ABC, abstractmethod

class ModelIntegration(ABC):
    model: str  # e.g. "WR6500"
    platforms: set[str]  # {"sensor", "switch", ...}

    def __init__(self, hass, entry, client):
        self.hass = hass
        self.entry = entry
        self.client = client

    @abstractmethod
    async def async_setup(self) -> None:
        """Create coordinator, store it in hass.data, etc."""

    @abstractmethod
    async def async_unload(self) -> None:
        """Unload anything model-specific."""