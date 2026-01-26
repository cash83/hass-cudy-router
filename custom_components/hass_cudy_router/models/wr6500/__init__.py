from ..base import ModelIntegration
from .coordinator import WR6500Coordinator

class WR6500Integration(ModelIntegration):
    model = "WR6500"
    platforms = {"sensor"}  # add switch/button if present

    def __init__(self, hass, entry, client):
        super().__init__(hass, entry, client)
        self.coordinator = None

    async def async_setup(self):
        self.coordinator = WR6500Coordinator(self.hass, self.client)
        await self.coordinator.async_config_entry_first_refresh()

    async def async_unload(self):
        # usually nothing special; platforms unload handles entities
        return

def create_integration(hass, entry, client):
    return WR6500Integration(hass, entry, client)