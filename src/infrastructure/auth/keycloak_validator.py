import logging
from typing import Any

import aiohttp
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from src.core.config import settings

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised when a token is missing, malformed, expired, or untrusted."""


class KeycloakTokenValidator:
    """
    Validates a JWT access token issued by Keycloak.
    """

    def __init__(self) -> None:
        self._jwks_cache: dict[str, Any] | None = None

    async def _fetch_jwks(self) -> dict[str, Any]:
        """
        Downloads the JWKS from Keycloak and caches it in memory.
        """
        if self._jwks_cache is not None:
            return self._jwks_cache

        logger.debug("Fetching JWKS from %s", settings.keycloak_jwks_url)
        async with aiohttp.ClientSession() as session:
            async with session.get(settings.keycloak_jwks_url) as response:
                if response.status != 200:
                    raise AuthError(
                        f"Could not fetch JWKS from Keycloak "
                        f"(HTTP {response.status}): {settings.keycloak_jwks_url}"
                    )
                self._jwks_cache = await response.json()
                logger.debug(
                    "JWKS cached successfully (%d keys)",
                    len(self._jwks_cache.get("keys", [])),
                )
                return self._jwks_cache

    async def validate(self, token: str) -> str:
        """
        Validates *token* against Keycloak's public keys.
        """
        if not token:
            raise AuthError("No token provided.")

        try:
            jwks = await self._fetch_jwks()
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                issuer=settings.keycloak_issuer,
                options={"verify_aud": False},
            )
        except ExpiredSignatureError:
            raise AuthError("Token has expired.")
        except JWTError as exc:
            raise AuthError(f"Token validation failed: {exc}") from exc

        # Verify the Authorized Party matches our allowed clients
        azp: str | None = payload.get("azp")
        allowed_clients = set(settings.keycloak_allowed_clients.split(","))

        if azp not in allowed_clients:
            raise AuthError(
                f"Token azp '{azp}' is not authorized. "
                f"Expected one of {allowed_clients}."
            )

        user_id: str | None = payload.get("sub")
        if not user_id:
            raise AuthError("Token payload is missing the 'sub' claim.")

        logger.debug("Token validated — user_id=%s", user_id)
        return user_id

    def invalidate_cache(self) -> None:
        """Clears the in-memory JWKS cache (useful for testing)."""
        self._jwks_cache = None
