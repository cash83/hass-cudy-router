from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import CudyClient
from .model_detect import detect_model
from .models import create_model_integration

DOMAIN = "hass_cudy_router"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = CudyClient.from_entry(entry)

    model = await detect_model(client)  # e.g. "WR6500"
    integration = create_model_integration(model, hass, entry, client)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "model": model,
        "integration": integration,
    }

    await integration.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, integration.platforms)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if not data:
        return True

    integration = data["integration"]
    await hass.config_entries.async_unload_platforms(entry, integration.platforms)
    await integration.async_unload()
    return True