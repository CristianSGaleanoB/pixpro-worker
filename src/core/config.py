from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # RabbitMQ settings with default values
    amqp_url: str = "amqp://guest:guest@localhost:5672/"
    queue_name: str = "image_upload_events"
    
    # Environment file configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate the settings so they can be imported and used anywhere
settings = Settings()
