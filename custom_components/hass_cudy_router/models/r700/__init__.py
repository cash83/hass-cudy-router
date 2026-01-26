from ..base import ModelIntegration
from .coordinator import R700Coordinator

class R700Integration(ModelIntegration):
    model = "R700"
    platforms = {"sensor"}  # add switch/button if present

    def __init__(self, hass, entry, client):
        super().__init__(hass, entry, client)
        self.coordinator = None

    async def async_setup(self):
        self.coordinator = R700Coordinator(self.hass, self.client)
        await self.coordinator.async_config_entry_first_refresh()

    async def async_unload(self):
        # usually nothing special; platforms unload handles entities
        return

def create_integration(hass, entry, client):
    return R700Integration(hass, entry, client)