import asyncio
import logging
from typing import Any

import aiohttp.web
import socketio

from src.core.config import settings
from src.core.interfaces import NotificationService
from src.infrastructure.auth.keycloak_validator import AuthError, KeycloakTokenValidator

logger = logging.getLogger(__name__)


class SocketIONotifier(NotificationService):
    """
    Concrete implementation of :class:`NotificationService` using
    python-socketio.
    """

    def __init__(self, validator: KeycloakTokenValidator | None = None) -> None:
        self._validator = validator or KeycloakTokenValidator()
        self._sio = socketio.AsyncServer(
            async_mode="aiohttp",
            cors_allowed_origins=settings.cors_allowed_origins,
            logger=False,
            engineio_logger=False,
        )
        self._app = aiohttp.web.Application()
        self._sio.attach(self._app)
        self._runner: aiohttp.web.AppRunner | None = None
        self._server_task: asyncio.Task[None] | None = None

        # Register Socket.IO event handlers
        self._sio.on("connect", handler=self._on_connect)
        self._sio.on("disconnect", handler=self._on_disconnect)

    # Lifecycle

    async def start(self) -> None:
        """
        Starts the aiohttp/Socket.IO server in the background.
        Returns as soon as the server is listening.
        """
        self._runner = aiohttp.web.AppRunner(self._app)
        await self._runner.setup()
        site = aiohttp.web.TCPSite(
            self._runner,
            host=settings.socketio_host,
            port=settings.socketio_port,
        )
        await site.start()
        logger.info(
            "SocketIO server listening on %s:%d",
            settings.socketio_host,
            settings.socketio_port,
        )

    async def stop(self) -> None:
        """Shuts down the aiohttp server and cleans up resources."""
        if self._runner is not None:
            await self._runner.cleanup()
            logger.info("SocketIO server stopped.")

    # Socket.IO event handlers

    async def _on_connect(
        self, sid: str, environ: dict[str, Any], auth: dict[str, Any] | None = None
    ) -> bool:
        """
        Validates the JWT on every new connection.
        """
        # Socket.IO auth payload (python-socketio AsyncSimpleClient passes this)
        token: str | None = None
        if auth and isinstance(auth, dict):
            token = auth.get("token")

        # Fallback: WSGI query string (?token=<JWT>)
        if not token:
            query_string: str = environ.get("QUERY_STRING", "")
            token = _extract_query_param(query_string, "token")

        if not token:
            logger.warning("Connection refused — no token provided (sid=%s)", sid)
            return False

        try:
            user_id = await self._validator.validate(token)
        except AuthError as exc:
            logger.warning("Connection refused — %s (sid=%s)", exc, sid)
            return False

        # Join a private room named after the user so emits are scoped
        await self._sio.enter_room(sid, room=user_id)
        # Store user_id in session for logging on disconnect
        await self._sio.save_session(sid, {"user_id": user_id})
        logger.info("Client connected — sid=%s user_id=%s", sid, user_id)
        return True

    async def _on_disconnect(self, sid: str) -> None:
        session = await self._sio.get_session(sid)
        user_id = session.get("user_id", "unknown")
        logger.info("Client disconnected — sid=%s user_id=%s", sid, user_id)

    # NotificationService implementation

    async def notify_status(
        self, user_id: str, image_id: str, status: str, message: str = ""
    ) -> None:
        """
        Emits a ``pipeline_status`` event to the private room of *user_id*.
        """
        payload = {"image_id": image_id, "status": status, "message": message}
        await self._sio.emit("pipeline_status", payload, room=user_id)
        logger.info(
            "Emitted pipeline_status to user_id=%s image_id=%s status=%s",
            user_id,
            image_id,
            status,
        )


# Helpers


def _extract_query_param(query_string: str, key: str) -> str | None:
    """Parses a single value from a raw WSGI query string."""
    for part in query_string.split("&"):
        if "=" in part:
            k, _, v = part.partition("=")
            if k == key:
                return v
    return None
