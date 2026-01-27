from ..base import ModelIntegration
from .coordinator import P5Coordinator

class P5Integration(ModelIntegration):
    model = "P5"
    platforms = {"sensor"}  # add switch/button if present

    def __init__(self, hass, entry, client):
        super().__init__(hass, entry, client)
        self.coordinator = None

    async def async_setup(self):
        self.coordinator = P5Coordinator(self.hass, self.client)
        await self.coordinator.async_config_entry_first_refresh()

    async def async_unload(self):
        # usually nothing special; platforms unload handles entities
        return

def create_integration(hass, entry, client):
    return P5Integration(hass, entry, client)