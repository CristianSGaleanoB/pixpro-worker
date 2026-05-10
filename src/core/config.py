from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # RabbitMQ
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    exchange: str = "pixpro.events"
    exchange_type: str = "topic"
    queue_name: str = "pixpro.image.uploaded"
    routing_key: str = "image.uploaded"

    # SocketIO server
    socketio_host: str = "0.0.0.0"
    socketio_port: int = 8765
    cors_allowed_origins: str = "*"

    # Keycloak — public JWKS endpoint
    keycloak_jwks_url: str = (
        "http://localhost:8085/realms/pixpro-realm/protocol/openid-connect/certs"
    )
    keycloak_issuer: str = "http://localhost:8085/realms/pixpro-realm"
    keycloak_audience: str = "pixpro-backend-client"
    keycloak_allowed_clients: str = "pixpro-backend-client,pixpro-frontend-client"

    # Only required for integration tests (ROPC grant)
    keycloak_client_secret: str | None = None
    keycloak_token_url: str = (
        "http://localhost:8085/realms/pixpro-realm/protocol/openid-connect/token"
    )
    test_user_username: str = "meyer-test"
    test_user_password: str = "meyer-test"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Cloudinary — populated from .env at runtime (pydantic-settings)
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""


settings = Settings()
