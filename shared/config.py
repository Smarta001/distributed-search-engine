"""
Central settings object, populated from environment variables (or a .env file
in local dev). Every service imports `get_settings()` instead of reading
os.environ directly, so there's one source of truth for connection strings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # PostgreSQL
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/search_engine"

    # Service-level
    log_level: str = "INFO"
    environment: str = "development"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached so we parse the environment once per process, not once per call."""
    return Settings()
