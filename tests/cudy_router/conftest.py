# tests/conftest.py

pytest_plugins = "pytest_homeassistant_custom_component"

import os
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--cudy-live",
        action="store_true",
        default=False,
        help="Run tests that hit a real Cudy router (network tests).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "cudy_live: marks tests that require a real router / network access",
    )


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def cudy_live(request: pytest.FixtureRequest) -> bool:
    """Whether live router tests are enabled."""
    enabled = bool(request.config.getoption("--cudy-live"))
    if not enabled:
        enabled = os.getenv("CUDY_LIVE", "0") in ("1", "true", "yes", "on")
    return enabled


@pytest.fixture(autouse=True)
def _skip_cudy_live_tests(request: pytest.FixtureRequest, cudy_live: bool) -> None:
    """Skip tests marked cudy_live unless explicitly enabled."""
    if request.node.get_closest_marker("cudy_live") and not cudy_live:
        pytest.skip("Live Cudy router tests disabled (use --cudy-live or CUDY_LIVE=1)")