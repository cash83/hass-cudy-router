import pytest

from custom_components.hass_cudy_router.const import *
from custom_components.hass_cudy_router.parser import parse_module_by_sensors
from tests.cudy_router.fixtures import read_html, html_exists

@pytest.mark.asyncio
@pytest.mark.parametrize("model", CUDY_DEVICES)
async def test_parse_system(model: str):
    for module_key in SENSORS.keys():
        sensors = SENSORS[module_key]
        if html_exists(model, module_key):
            text = read_html(model, f"{module_key}.html")
            data = parse_module_by_sensors(module_key, text)
            assert isinstance(data, dict)
            for sensor in sensors:
                sensor_key = sensor[SENSORS_KEY_KEY]
                assert sensor_key in data
                assert data[sensor_key] != 'n/a'