"""Configuration object.

Reads configuration from .env files or from environment variables. Defaults and
fallbacks are specified in this file.

"""

from functools import lru_cache
from typing import Dict
import structlog

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Settings class emulating Flasks config mechanism in FastAPI.
    """

    HOSTNAME: str  # set by docker

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

    ROOT_PATH: str = ""
    APP_NAME: str = "consensus-cluster-service"
    LOGGING: str = "DEBUG"

    ### RAFT SPECIFIC SETTINGS ###
    ELECTION_TIMEOUT_LOWER_MILLIS = 1500
    ELECTION_TIMEOUT_UPPER_MILLIS = 3000

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
        """pydantic config subclass"""

        case_sensitive: bool = True


@lru_cache()
def get_settings() -> Settings:
    """return a cached copy of the configuration"""
    return Settings()
