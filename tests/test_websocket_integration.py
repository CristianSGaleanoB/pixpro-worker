"""
Integration tests for WebSocket / Keycloak authentication.

These tests require REAL services to be running:
  - Keycloak   → http://localhost:8085
  - (RabbitMQ is NOT required for these tests)
"""

import asyncio
import socket
import pytest
import pytest_asyncio
import socketio as sio_client

from src.infrastructure.auth.keycloak_validator import (
    AuthError,
    KeycloakTokenValidator,
)
from src.infrastructure.notifications.websocket import SocketIONotifier
from src.core.config import settings

# Helpers


def _free_port() -> int:
    """Returns an ephemeral port guaranteed to be free at call time."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        res = s.getsockname()
        return int(res[1])


async def _fetch_real_token(client_secret: str) -> str:
    """
    Obtains a real access token from Keycloak using the Resource Owner
    Password Credentials grant (test environments only).
    """
    import aiohttp

    payload = {
        "grant_type": "password",
        "client_id": settings.keycloak_audience,
        "client_secret": client_secret,
        "username": settings.test_user_username,
        "password": settings.test_user_password,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(settings.keycloak_token_url, data=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                pytest.fail(
                    f"Could not obtain token from Keycloak (HTTP {resp.status}): {body}"
                )

            data = await resp.json()
            token = data["access_token"]
            return str(token)


# Fixtures


@pytest.fixture(scope="module")
def keycloak_client_secret() -> str:
    """
    Reads the Keycloak client secret from settings (loaded from .env).
    Skips the module if the secret is not configured.
    """
    secret = getattr(settings, "keycloak_client_secret", None)
    if not secret:
        pytest.skip(
            "KEYCLOAK_CLIENT_SECRET not set in .env — skipping Keycloak integration tests"
        )
    return str(secret)


@pytest_asyncio.fixture(scope="module")
async def real_token(keycloak_client_secret: str) -> str:
    """Fetches a real JWT from Keycloak once for the entire test module."""
    return await _fetch_real_token(keycloak_client_secret)


@pytest_asyncio.fixture
async def notifier():
    """
    Starts a SocketIONotifier on a free port and tears it down after the test.
    Overrides socketio_host/port via monkeypatching the settings object.
    """
    port = _free_port()
    original_port = settings.socketio_port
    settings.socketio_port = port

    n = SocketIONotifier()
    await n.start()

    yield n, port

    await n.stop()
    settings.socketio_port = original_port


# Token validation — unit-style but hits real Keycloak


@pytest.mark.asyncio
async def test_token_validation_valid(real_token: str):
    """A real Keycloak token must be accepted and return the sub claim."""
    validator = KeycloakTokenValidator()
    user_id = await validator.validate(real_token)

    assert user_id, "Expected a non-empty sub claim"
    assert isinstance(user_id, str)


@pytest.mark.asyncio
async def test_token_validation_invalid():
    """A fabricated token must raise AuthError."""
    validator = KeycloakTokenValidator()

    with pytest.raises(AuthError):
        await validator.validate("this.is.not.a.valid.jwt")


@pytest.mark.asyncio
async def test_token_validation_empty():
    """An empty token must raise AuthError immediately (no network call)."""
    validator = KeycloakTokenValidator()

    with pytest.raises(AuthError, match="No token provided"):
        await validator.validate("")


# SocketIO server — connection acceptance / rejection


@pytest.mark.asyncio
async def test_socketio_connect_with_valid_token(notifier, real_token: str):
    """A client with a valid JWT must be accepted by the server."""
    server, port = notifier

    client = sio_client.AsyncSimpleClient()
    try:
        await asyncio.wait_for(
            client.connect(
                f"http://127.0.0.1:{port}",
                socketio_path="/socket.io",
                auth={"token": real_token},
                transports=["websocket"],
                wait_timeout=5,
            ),
            timeout=10,
        )
        assert client.connected
    finally:
        if client.connected:
            await client.disconnect()


@pytest.mark.asyncio
async def test_socketio_connect_with_invalid_token(notifier):
    """A client with a bogus token must be refused by the server."""
    server, port = notifier

    client = sio_client.AsyncSimpleClient()
    with pytest.raises(Exception):
        # python-socketio raises ConnectionError / socketio.exceptions.ConnectionError
        # when the server returns False from the connect handler
        await asyncio.wait_for(
            client.connect(
                f"http://127.0.0.1:{port}",
                socketio_path="/socket.io",
                auth={"token": "not.a.real.token"},
                transports=["websocket"],
                wait_timeout=5,
            ),
            timeout=10,
        )


# End-to-end notification delivery


@pytest.mark.asyncio
async def test_socketio_notify_status_delivered(notifier, real_token: str):
    """
    notify_status() must deliver a 'pipeline_status' event to the connected
    client.  The event payload must match the call arguments exactly.
    """
    server, port = notifier

    # Connect the client
    client = sio_client.AsyncSimpleClient()
    await asyncio.wait_for(
        client.connect(
            f"http://127.0.0.1:{port}",
            socketio_path="/socket.io",
            auth={"token": real_token},
            transports=["websocket"],
            wait_timeout=5,
        ),
        timeout=10,
    )

    # Get the user_id that was assigned to this connection
    # The validator returns the sub claim; we need it to call notify_status
    validator = KeycloakTokenValidator()
    user_id = await validator.validate(real_token)

    # Emit from the server side
    await server.notify_status(
        user_id=user_id,
        image_id="img-001",
        status="complete",
        progress=100,
        message="Done!",
    )

    # Receive on the client side
    try:
        event, payload = await asyncio.wait_for(client.receive(), timeout=5)
    finally:
        await client.disconnect()

    assert event == "pipeline_status"
    assert payload["image_id"] == "img-001"
    assert payload["status"] == "complete"
    assert payload["progress"] == 100
    assert payload["message"] == "Done!"


@pytest.mark.asyncio
async def test_socketio_notify_status_not_delivered_to_other_user(
    notifier, real_token: str
):
    """
    A notification scoped to user A must NOT reach user B.
    We verify this by emitting to a non-existent user_id and confirming
    the connected client receives nothing within the timeout.
    """
    server, port = notifier

    client = sio_client.AsyncSimpleClient()
    await asyncio.wait_for(
        client.connect(
            f"http://127.0.0.1:{port}",
            socketio_path="/socket.io",
            auth={"token": real_token},
            transports=["websocket"],
            wait_timeout=5,
        ),
        timeout=10,
    )

    # Emit to a completely different user — our client must NOT receive this
    await server.notify_status(
        user_id="other-user-00000000-0000-0000-0000-000000000000",
        image_id="img-999",
        status="processing",
        progress=0,
        message="Should not arrive",
    )

    received = None
    try:
        received = await asyncio.wait_for(client.receive(), timeout=2)
    except asyncio.TimeoutError:
        pass  # Expected: nothing arrived
    finally:
        await client.disconnect()

    assert (
        received is None
    ), f"Client received an event that was meant for a different user: {received}"
