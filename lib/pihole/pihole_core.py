import requests
import hashlib
from urllib import parse as urlparse
import urllib3
import re
import sys
import os
import json

import logging
import configparser
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, BaseConfig
from typing import Optional, List
from pprint import pprint, pformat

#from ..dependencies import get_token_header


from .alldns import MasterEnabler
from .pihole import PiHoleOverlord


import http.client as http_client
http_client.HTTPConnection.debuglevel = 0

# You must initialize logging, otherwise you'll not see debug output.

logger = logging.getLogger()
requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True



logger = logging.getLogger()

pihole = None
all_dns = None

def init(app_config: dict):
  global pihole
  global all_dns
  pihole = PiHoleOverlord(app_config=app_config)
  all_dns = MasterEnabler(app_config=app_config)

main_router = APIRouter(
    prefix="/pihole",
    tags=["pihole"],
#    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@main_router.get("/status/{domain_block}")
async def get_pihole(domain_block: str):
    return pihole.get(domain_block)

@main_router.post("/disable/{domain_block}")
async def post_pihole(domain_block: str):
    return pihole.post("disable", domain_block)

@main_router.post("/enable/{domain_block}")
async def delete_pihole(domain_block: str):
    return pihole.post("enable",domain_block)

alldns_router = APIRouter(
    prefix="/pihole/alldns",
    tags=["alldns"],
#    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)



@alldns_router.get("/")
async def get_all_dns():
    return all_dns.get()

@alldns_router.delete("/")
async def delete_all_dns( command: str | None, timer: int | None):
    return all_dns.delete(command, timer)

@alldns_router.post("/")
async def post_all_dns( command: str | None, timer: int | None):
    return all_dns.disable(command, timer)
