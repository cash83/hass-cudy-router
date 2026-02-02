from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.helpers import entity_registry as er

from custom_components.hass_cudy_router.const import *

from tests.cudy_router.fixtures import FakeClient, html_exists

MODULES = [
    MODULE_SYSTEM,
    MODULE_LAN,
    MODULE_DEVICES,
    MODULE_MESH,
    MODULE_WAN,
    MODULE_WAN_SECONDARY,
    MODULE_MULTI_WAN,
    MODULE_WIRELESS_24G,
    MODULE_WIRELESS_5G,
    MODULE_WIRELESS_6G,
    MODULE_DHCP,
    MODULE_GSM,
    MODULE_SMS,
    MODULE_VPN,
    MODULE_USB,
]


@pytest.mark.asyncio
@pytest.mark.parametrize("model", CUDY_DEVICES)
async def test_platform_setup_creates_entities(
    hass,
    monkeypatch,
    model: str,
) -> None:

    fake = FakeClient(model)

    async def _noop(*args, **kwargs):
        return None

    async def _auth_ok(*args, **kwargs):
        return True

    setattr(fake, "authenticate", _auth_ok)
    setattr(fake, "close", _noop)
    setattr(fake, "async_close", _noop)

    # Patch the integration to use FakeClient instead of real CudyClient
    monkeypatch.setattr(
        "custom_components.hass_cudy_router.CudyClient",
        lambda *args, **kwargs: fake,
    )

    # Patch model detection to return the requested model
    async def _detect_model(_client):
        return model

    monkeypatch.setattr(
        "custom_components.hass_cudy_router.detect_model",
        _detect_model,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=f"Cudy Router ({model})",
        data={
            "protocol": "http",
            "host": "192.168.1.1",
            "username": "admin",
            "password": "admin",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    entries = [
        e for e in ent_reg.entities.values()
        if e.config_entry_id == entry.entry_id
    ]

    assert entries, f"No entities created for model={model}"

    unique_ids = [e.unique_id for e in entries if e.unique_id]
    assert len(unique_ids) == len(set(unique_ids)), (
        f"Duplicate unique_id detected for model={model}: {unique_ids}"
    )
    coord = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    uuid = entry.entry_id
    sensor_list = {}
    for sensor in entries:
        if sensor.unique_id:
            sensor_list[sensor.unique_id] = sensor
    for module in MODULES:
        data = coord.data
        if html_exists(model, module):
            for submodule in SENSORS[module]:
                entity_id = f"{uuid}_{module}_{submodule[SENSORS_KEY_KEY]}"
                assert entity_id in sensor_list.keys()
                sensor = sensor_list[entity_id]
                assert sensor
        else:
            assert module not in data