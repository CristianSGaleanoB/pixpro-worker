import pytest
import time
import uuid
import statistics
from src.infrastructure.storage.cdn import CloudinaryCDNStorage
from PIL import Image
import io

pytestmark = [
    pytest.mark.integration,
]


def make_png(width: int, height: int) -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 149, 237))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


SMALL_IMAGE = make_png(10, 10)
MEDIUM_IMAGE = make_png(800, 600)
LARGE_IMAGE = make_png(2000, 1500)


@pytest.fixture
def cdn(cloudinary_credentials):
    return CloudinaryCDNStorage()


async def _measure_upload(cdn, image_data, label, cleanup):
    image_id = f"metric-{uuid.uuid4()}"
    cleanup.add(f"pixpro/metrics/{image_id}")
    start = time.perf_counter()
    url = await cdn.upload_image(
        image_id=image_id, image_data=image_data, folder="metrics"
    )
    elapsed = (time.perf_counter() - start) * 1000
    print(f"\n[METRIC] Upload {label}: {elapsed:.0f} ms — {url}")
    return {"label": label, "upload_ms": elapsed, "url": url}


async def _measure_download(cdn, url, label):
    start = time.perf_counter()
    data = await cdn.download_image(url)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"[METRIC] Download {label}: {elapsed:.0f} ms — {len(data)} bytes")
    return {"label": label, "download_ms": elapsed, "size_bytes": len(data)}


@pytest.mark.asyncio
async def test_upload_download_small(cdn, cloudinary_cleanup):
    r = await _measure_upload(cdn, SMALL_IMAGE, "small (~100B)", cloudinary_cleanup)
    d = await _measure_download(cdn, r["url"], "small")
    assert d["size_bytes"] > 0


@pytest.mark.asyncio
async def test_upload_download_medium(cdn, cloudinary_cleanup):
    r = await _measure_upload(cdn, MEDIUM_IMAGE, "medium (~500KB)", cloudinary_cleanup)
    d = await _measure_download(cdn, r["url"], "medium")
    assert d["size_bytes"] > 0


@pytest.mark.asyncio
async def test_upload_download_large(cdn, cloudinary_cleanup):
    r = await _measure_upload(cdn, LARGE_IMAGE, "large (~2MB)", cloudinary_cleanup)
    d = await _measure_download(cdn, r["url"], "large")
    assert d["size_bytes"] > 0


@pytest.mark.asyncio
async def test_upload_latency_consistency(cdn, cloudinary_cleanup):
    """
    Upload the same small image 5 times and measure variance.
    A well-configured CDN should have consistent upload latencies.
    """
    times = []
    for i in range(5):
        image_id = f"consistency-{uuid.uuid4()}"
        cloudinary_cleanup.add(f"pixpro/metrics/{image_id}")
        start = time.perf_counter()
        await cdn.upload_image(
            image_id=image_id,
            image_data=SMALL_IMAGE,
            folder="metrics",
        )
        times.append((time.perf_counter() - start) * 1000)

    avg = statistics.mean(times)
    stdev = statistics.stdev(times)
    print(
        f"\n[METRIC] Consistency — avg: {avg:.0f}ms | stdev: {stdev:.0f}ms | times: {[f'{t:.0f}' for t in times]}"
    )

    assert (
        stdev < avg * 0.8
    ), f"High variance in upload times: stdev={stdev:.0f}ms avg={avg:.0f}ms"
