from __future__ import annotations

import logging
from typing import Callable, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from ..client import CudyClient

_LOGGER = logging.getLogger(__name__)

CreateIntegrationFn = Callable[
    [HomeAssistant, ConfigEntry, CudyClient],
    object,
]

REGISTRY: Dict[str, CreateIntegrationFn] = {}


def register_model(model: str, factory: CreateIntegrationFn) -> None:
    _LOGGER.debug("Registering model integration: %s", model)
    REGISTRY[model] = factory


def create_model_integration(
    model: str,
    hass: HomeAssistant,
    entry: ConfigEntry,
    client: CudyClient,
):
    try:
        factory = REGISTRY[model]
    except KeyError as exc:
        raise ValueError(f"Unsupported Cudy router model: {model}") from exc

    _LOGGER.info("Creating integration for model: %s", model)
    return factory(hass, entry, client)


from .generic import create_integration as generic_create
from .wr6500 import create_integration as wr6500_create
from .r700 import create_integration as r700_create
from .p5 import create_integration as p5_create

register_model("Generic", generic_create)
register_model("WR6500", wr6500_create)
register_model("R700", r700_create)
register_model("P5", p5_create)