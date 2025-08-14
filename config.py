from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class RabbitMQConfig:
    username: str
    password: str
    host: str
    port: int
    queue_name: str = "olymps"
    prefetch_count: int = 1


@dataclass(frozen=True)
class DatabaseApiConfig:
    host: str
    port: int
    token: Optional[str] = None
    scheme: str = "http"

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"


@dataclass(frozen=True)
class AppConfig:
    rmq: RabbitMQConfig
    db: DatabaseApiConfig
    log_level: str = "INFO"


class ConfigError(RuntimeError):
    pass


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Required environment variable {name} is not set")
    return value


def _require_int(value: str, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ConfigError(f"Environment variable {name} must be an integer, got: {value!r}")


def load_config() -> AppConfig:
    # RabbitMQ
    rmq_user = _require_env("RMQ_USER")
    rmq_pass = _require_env("RMQ_PASS")
    rmq_host = _require_env("RMQ_HOST")
    rmq_port = _require_int(os.getenv("RMQ_PORT", "5672"), "RMQ_PORT")

    # Database API
    db_host = _require_env("DB_SERVER_HOST")
    db_port = _require_int(_require_env("DB_SERVER_PORT"), "DB_SERVER_PORT")
    db_token = os.getenv("DB_API_TOKEN")

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    return AppConfig(
        rmq=RabbitMQConfig(
            username=rmq_user,
            password=rmq_pass,
            host=rmq_host,
            port=rmq_port,
        ),
        db=DatabaseApiConfig(
            host=db_host,
            port=db_port,
            token=db_token,
        ),
        log_level=log_level,
    )