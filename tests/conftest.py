import pytest
import asyncio

# Configure pytest-asyncio to use the auto mode
# This allows tests to be defined as 'async def' without needing @pytest.mark.asyncio decorator
def pytest_configure(config):
    config.option.asyncio_mode = "auto"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
