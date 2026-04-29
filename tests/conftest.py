import pytest
import asyncio


def pytest_configure(config):
    config.option.asyncio_mode = "auto"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
