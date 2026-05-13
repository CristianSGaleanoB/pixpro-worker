import pytest
import asyncio
import os

from src.core.config import settings


def pytest_configure(config):
    config.option.asyncio_mode = "auto"
    config.addinivalue_line(
        "markers",
        "integration: marks tests that hit real external services (Cloudinary, Keycloak, etc.)",
    )


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Cloudinary helpers — shared by all integration tests that hit Cloudinary


@pytest.fixture(scope="module")
def cloudinary_credentials():
    """Skip the module if Cloudinary is not configured in .env."""
    if not settings.cloudinary_cloud_name:
        pytest.skip(
            "CLOUDINARY_CLOUD_NAME not set — skipping Cloudinary integration tests"
        )
    return settings


@pytest.fixture
def cloudinary_cleanup():
    """
    Tracks public_ids uploaded during a test and destroys them afterward.

    Usage::

        def test_something(cloudinary_cleanup):
            cleanup = cloudinary_cleanup
            # … upload image, get its public_id …
            cleanup.add("pixpro/test/my-id")

    After the test exits, every accumulated public_id is deleted from Cloudinary.
    """
    import cloudinary.uploader

    class _Cleanup:
        def __init__(self) -> None:
            self._ids: list[str] = []

        def add(self, public_id: str) -> None:
            self._ids.append(public_id)

        async def destroy_all(self) -> None:
            loop = asyncio.get_event_loop()
            for pid in self._ids:
                try:
                    await loop.run_in_executor(
                        None, lambda p=pid: cloudinary.uploader.destroy(p)  # type: ignore[misc]
                    )
                except Exception:
                    pass

    cleanup = _Cleanup()
    yield cleanup
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(cleanup.destroy_all())
    else:
        loop.run_until_complete(cleanup.destroy_all())
