import requests
import hashlib
from urllib import parse as urlparse
import urllib3
import re
import sys
import os
import json

import logging
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, BaseConfig
from typing import Optional, List
from pprint import pprint, pformat

# from ..dependencies import get_token_header


from .alldns import MasterEnabler
from .pihole import PiHoleOverlord


# import http.client as http_client

# http_client.HTTPConnection.debuglevel = 0

# You must initialize logging, otherwise you'll not see debug output.
logger = logging.getLogger(__name__)


pihole: PiHoleOverlord | None = None
all_dns: MasterEnabler | None = None
enabled: bool = False


def init(app_config: dict):
    global pihole
    global all_dns
    global logger

    #   logger = app_config["logger"]
    pihole = PiHoleOverlord(app_config=app_config)
    all_dns = MasterEnabler(app_config=app_config)
    logger = app_config["logger"]

    logger.debug("Started up pihole_core")


main_router = APIRouter(
    prefix="/pihole",
    tags=["pihole"],
    #    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found on earth."}},
)


@main_router.get("/status/{domain_block}")
async def get_pihole(domain_block: str):
    return pihole.get(domain_block)


@main_router.post("/disable/{domain_block}")
async def post_pihole(domain_block: str):
    return pihole.post("disable", domain_block)


@main_router.post("/enable/{domain_block}")
async def delete_pihole(domain_block: str):
    return pihole.post("enable", domain_block)


alldns_router = APIRouter(
    prefix="/alldns",
    tags=["alldns"],
    #    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@alldns_router.get("/")
def get_all_dns():
    return all_dns.get()


@alldns_router.delete("/")
def delete_all_dns():
    return all_dns.enable_dns_blocking()


@alldns_router.post("/")
def post_all_dns(timer: Optional[int] = None):
    return all_dns.disable_dns_blocking(timer)
