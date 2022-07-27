from functools import lru_cache
from typing import Dict, List
import structlog

from pydantic import BaseSettings, AnyHttpUrl, validator


class Settings(BaseSettings):
    """
    Settings class emulating Flasks config mechanism in FastAPI.
    """

    HOSTNAME: str  # set by docker
    NUM_REPLICAS: int  # set by docker

    FASTAPI_TITLE: str = "Consensus Cluster Service"
    FASTAPI_MAINT: str = "Sebastian Kowalak"
    FASTAPI_EMAIL: str = "skowalak@techfak.uni-bielefeld.de"
    FASTAPI_DESCR: str = (
        "392155 Netzwerkprogrammierung Final Project.\n"
        "\n"
        "### Master Election\n"
        "\n"
        "* Master Election using RAFT algorithm.\n"
        "\n"
        "### Service Discovery\n"
        "\n"
        "* tbd\n"
    )
    FASTAPI_SCHEM: str = "/openapi.json"
    FASTAPI_DOCS: str = "/docs"
    API_PREFIX: str = "/api"

    ROOT_PATH: str = "/ccs"
    APP_NAME: str = "consensus-cluster-service"
    LOGGING: str = "DEBUG"

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", \
    # "http://localhost:8080", "http://ccs.local"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: List[str] | str) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    SECRET_KEY: str = "changeme"

    ### RAFT SPECIFIC SETTINGS ###
    ELECTION_TIMEOUT_LOWER_MILLIS = 150
    ELECTION_TIMEOUT_UPPER_MILLIS = 300

    LOGGING_CONFIG: Dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer()
                    # structlog.processors.LogfmtRenderer()
                    # structlog.dev.ConsoleRenderer(
                    #    colors=True, exception_formatter=structlog.dev.rich_traceback
                    # ),
                ],
                "foreign_pre_chain": [
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper("iso", utc=True),
                ],
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "ERROR"},
            "app": {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            },
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "asyncio": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }

    class Config:
        case_sensitive: bool = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
