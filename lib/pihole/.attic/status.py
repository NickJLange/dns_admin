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

# from ..dependencies import get_token_header


from .alldns import MasterEnabler
from .pihole import PiHoleOverlord


class StatusCheck(MasterEnabler):
    def get_general(self):
        logger.info("Getting Status for rpis")
        resps = list()
        sumResp = defaultdict(list)

        for pi in self.piList:
            resps.append(self.cmd(cmd="status", pi=pi))
        #        pprint(domain_block)
        stateMap = {"enabled": "on", "disabled": "off"}

        for pi in resps:
            sumResp[stateMap[pi["status"]]].append(pi)
        # FIXME: Can HomeKit represent this???
        if len(sumResp.keys()) > 1:
            return {"Status": "off"}
        return {"Status": list(sumResp.keys())[0]}

    def get(self, domain_block=None):
        if domain_block is None:
            return self.get_general()
        else:
            logger.info("Getting Status for domain: %s" % domain_block)
            a = PiHoleOverlord()
            return a.get(domain_block)


class HealthCheck(MasterEnabler):
    def get(self, domain_block=None):
        if not domain_block:
            a = PiHoleOverlord()
            b = MasterEnabler()
            x = a.get()
            y = b.get()
            return {"Status1": x, "Status2": y}
        return {"Boo": "Doo2"}


logger = logging.getLogger()


status_router = APIRouter(
    prefix="/pihole/status",
    tags=["pihole"],
    #    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@status_router.get("/status/{domain_block}")
def get_pihole(domain_block: str):
    return pihole.get(domain_block)


@status_router.post("/disable/{domain_block}")
def post_pihole(domain_block: str):
    return pihole.post("disable", domain_block)


@status_router.post("/enable/{domain_block}")
def delete_pihole(domain_block: str):
    return pihole.post("enable", domain_block)
