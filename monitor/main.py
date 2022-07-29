import logging
import os
import sys
import threading
import time

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app.raft.discovery import discover_by_dns, get_hostname_by_ip
import requests
import dns

main_app_name = os.environ.get("MAIN_APP_NAME")
my_hostname = os.environ.get("HOSTNAME")
address = os.environ.get("ADDRESS", "localhost:8080")
templates_dir = os.environ.get("TEMPLATES_DIR", "/app/monitor/templates/")

app = FastAPI()
templates = Jinja2Templates(directory=templates_dir)
logging.basicConfig(
    format="%(message)s", stream=sys.stdout, encoding="utf-8", level="DEBUG"
)

nodes_info = {"monitor": {
    "id": my_hostname,
    "app_name": "monitor",
    "term": "-",
    "state": "-",
}}

@app.get("/nodes")
async def nodes():
    return {"nodes": [v for k, v in nodes_info.items()]}

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "host": address})

class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def update_node_info(node_info: dict) -> None:
    services = {}
    try:
        ip_list = discover_by_dns(main_app_name)
        for ip in ip_list:
            services[str(ip)] = get_hostname_by_ip(ip)

    except dns.exception.DNSException as error:
        logging.warning(f"DNS raised error: {str(error)}")

    for replica, replica_ip in services.items():
        try:
            response = requests.get(f"http://{replica}/api/v1/raft/")
            node_info[replica] = response.json()["data"]
        except requests.RequestException as error:
            logging.warning(f"could not request service status: {str(error)}")
            pass
        except KeyError:
            pass

thread = RepeatTimer(1.0, update_node_info, [nodes_info])
thread.start()

