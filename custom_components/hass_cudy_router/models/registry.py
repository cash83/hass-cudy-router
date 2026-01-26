from __future__ import annotations

import logging
from typing import Callable, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..client import CudyClient

_LOGGER = logging.getLogger(__name__)

# Factory signature for model integrations
CreateIntegrationFn = Callable[
    [HomeAssistant, ConfigEntry, CudyClient],
    object,
]

# -------------------------------------------------------------------
# Model registry
# -------------------------------------------------------------------
REGISTRY: Dict[str, CreateIntegrationFn] = {}


# -------------------------------------------------------------------
# Registration helper
# -------------------------------------------------------------------
def register_model(model: str, factory: CreateIntegrationFn) -> None:
    """Register a model integration factory."""
    _LOGGER.debug("Registering model integration: %s", model)
    REGISTRY[model] = factory


# -------------------------------------------------------------------
# Public factory
# -------------------------------------------------------------------
def create_model_integration(
    model: str,
    hass: HomeAssistant,
    entry: ConfigEntry,
    client: CudyClient,
):
    """Create a model integration instance."""
    try:
        factory = REGISTRY[model]
    except KeyError as exc:
        raise ValueError(f"Unsupported Cudy router model: {model}") from exc

    _LOGGER.info("Creating integration for model: %s", model)
    return factory(hass, entry, client)


# -------------------------------------------------------------------
# Register implemented models ONLY
# -------------------------------------------------------------------
# Each model package MUST expose `create_integration` in its __init__.py

from .wr6500 import create_integration as wr6500_create

register_model("WR6500", wr6500_create)

# ⚠️ DO NOT enable until implemented
# from .r700 import create_integration as r700_create
# register_model("R700", r700_create)