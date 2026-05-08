import pytest
import uuid
from src.infrastructure.storage.cdn import CloudinaryCDNStorage


@pytest.fixture
def cdn():
    return CloudinaryCDNStorage()


@pytest.fixture
def sample_image_bytes():
    """
    Minimal valid PNG image of 1x1 pixel (hardcoded in bytes).
    """
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
        b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )


@pytest.mark.asyncio
async def test_upload_image_returns_valid_url(cdn, sample_image_bytes):
    """
    When uploading an image, Cloudinary should return a valid HTTPS URL pointing to the 
    res.cloudinary.com domain.
    """
    image_id = f"test-{uuid.uuid4()}"

    url = await cdn.upload_image(
        image_id=image_id,
        image_data=sample_image_bytes,
        folder="test",
    )

    assert url.startswith("https://"), "The URL must start with https://"
    assert "cloudinary.com" in url, "The URL must point to Cloudinary"
    assert image_id in url, "The URL must contain the image_id as public_id"


@pytest.mark.asyncio
async def test_download_image_returns_bytes(cdn, sample_image_bytes):
    """
    An image previously uploaded must be downloadable
    and return non-empty bytes.
    """
    image_id = f"test-{uuid.uuid4()}"

    url = await cdn.upload_image(
        image_id=image_id,
        image_data=sample_image_bytes,
        folder="test",
    )

    downloaded = await cdn.download_image(url)

    assert isinstance(downloaded, bytes)
    assert len(downloaded) > 0, "The downloaded image must not be empty"


@pytest.mark.asyncio
async def test_upload_overwrite_same_image_id(cdn, sample_image_bytes):
    """
    Uploading an image twice with the same image_id should work without errors
    (overwrite=True in Cloudinary's configuration).
    """
    image_id = f"test-{uuid.uuid4()}"

    url_first = await cdn.upload_image(
        image_id=image_id,
        image_data=sample_image_bytes,
        folder="test",
    )
    url_second = await cdn.upload_image(
        image_id=image_id,
        image_data=sample_image_bytes,
        folder="test",
    )

    assert url_first.startswith("https://")
    assert url_second.startswith("https://")