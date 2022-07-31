"""Monitor shows status information about the nodes in the cluster.

The monitor.main module is a small FastAPI app, that periodically aggregates
status information on all nodes in the cluster by calling their status
endpoints.

A static webpage is then served, which refreshes itself every 1 second and
displays the cluster status.

"""

import logging
import sys
import threading

import dns
import requests
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings

from app.raft.discovery import discover_by_dns, get_hostname_by_ip


class Settings(BaseSettings):
    """Settings / Configuration variables"""

    RAFT_SERVICE_NAME: str
    BIND_HOST: str
    BIND_PORT: str
    TEMPLATES_DIR: str
    REFRESH_RATE_MILLIS: int

    # set by docker
    HOSTNAME: str


class RepeatTimer(threading.Timer):
    """Subclass of python threading.Timer that repeats itself"""

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


app = FastAPI()
settings = Settings()
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)
logging.basicConfig(
    format="%(message)s", stream=sys.stdout, encoding="utf-8", level="DEBUG"
)

nodes_info = {}


def update_node_info(node_info: dict) -> None:
    """Refresh info about all nodes in cluster

    Parameters
    ----------
    node_info : dict
        Dict to be updated
    """
    services = {}
    node_info_new = {
        "monitor": {
            "id": settings.HOSTNAME,
            "app_name": "monitor",
            "term": "-",
            "state": "-",
        }
    }
    try:
        ip_list = discover_by_dns(settings.RAFT_SERVICE_NAME)
        for ip_address in ip_list:
            services[str(ip_address)] = get_hostname_by_ip(ip_address)

    except dns.exception.DNSException as error:
        logging.warning("DNS raised error: %s", str(error))

    for replica, _ in services.items():
        try:
            response = requests.get(f"http://{replica}/api/v1/raft/", timeout=0.5)
            node_info_new[replica] = response.json()["data"]
            logging.debug(
                "response from node %s, status %s", replica, response.status_code
            )
        except (requests.RequestException, KeyError) as error:
            logging.warning("could not request service status: %s", str(error))
            continue

    node_info.clear()
    node_info.update(dict(sorted(node_info_new.items())))


thread = RepeatTimer(
    settings.REFRESH_RATE_MILLIS / 1000, update_node_info, [nodes_info]
)
thread.start()


@app.get("/nodes")
async def nodes():
    """Serve status information on all hosts in docker network.

    Returns
    -------
    Dict[str, Any]
        A dict containing a list of nodes
    """
    return {"nodes": list(nodes_info.values())}


@app.get("/")
async def root(request: Request):
    """Serve a small webpage displaying status information

    Parameters
    ----------
    request : Request
        FastAPI/Starlette Request

    Returns
    -------
    Jinja2Template
        Rendered HTML page
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "host": settings.BIND_HOST,
            "port": settings.BIND_PORT,
            "refresh_rate": settings.REFRESH_RATE_MILLIS,
        },
    )
