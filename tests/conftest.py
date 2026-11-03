"""Enable loading the custom integration in HA tests."""

import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield
