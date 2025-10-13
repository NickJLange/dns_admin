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

import http.client as http_client

http_client.HTTPConnection.debuglevel = 0

# You must initialize logging, otherwise you'll not see debug output.

logger = logging.getLogger()
requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


from .base import BaseHTTPHandler

logger = logging.getLogger()


class PiHoleOverlord(BaseHTTPHandler):
    app_config: dict
    piList: List[str]
    domains: dict
    password: str
    token: str
    timer: int  # unused, FIXME for optional fields in base class
    sessions: dict

    def __init__(self, app_config: dict) -> None:
        super().__init__(
            app_config=app_config,
        )

    def add(self, phList, domain, comment=None, pi="localpi"):
        return self.cmd("add", phList=phList, domain=domain, comment=comment, pi=pi)

    def sub(self, phList, domain, comment=None, pi="localpi"):
        return self.cmd("sub", phList=phList, domain=domain, comment=comment, pi=pi)

    def sGet(self, domain_block=None, pi="localhost"):
        response = self.cmd(method="get", cmd="list", phList="regex_black", pi=pi)
        return response

    def get(self, domain_block=None):
        resps = list()
        for pi in self.piList:
            resps.append(self.sGet(domain_block, pi))
        #        pprint(domain_block)
        if domain_block is None or domain_block not in self.domains:
            return {"status": resps}
        state = "off"
        logger.info(f"Checking status {domain_block}")
        for domain in self.domains[domain_block]:
            logger.debug("%s -> %s" % (domain, self.transform(domain)))
            #            pprint(self.transform(domain))
            for pi in resps:
                for d in pi["data"]:
                    #                    pprint(d)
                    if "domain" in d and "enabled" in d and self.transform(domain) == d["domain"] and d["enabled"] == 1:
                        logger.info("Switching on %s %s" % (domain, d))
                        state = "on"
                    if "domain" in d and "enabled" in d and self.transform(domain) == d["domain"] and d["enabled"] == 0:
                        logger.info("Switching off %s %s" % (domain, d))
                        state = "off"
        logger.info(f"Result Status {state} for {domain_block}")
        return {"status": state}

    def post(self, direction: str, domain_block: str | None = None):
        if not domain_block:
            raise HTTPException(status_code=404, detail="Domain Block not configured")
        logger.info(f"Request to {direction} {domain_block}")
        for pi in self.piList:
            for domain in self.domains[domain_block]:
                if direction == "disable":
                    pi.domain_management.delete_domain(self.transform(domain), "deny", "regex")
                #                    self.add("regex_black", self.transform(domain), "Unfeeling", pi=pi)
                elif direction == "enable":
                    #                    self.sub("regex_black", self.transform(domain), "Unfeeling", pi=pi)
                    pi.domain_management.add_domain(self.transform(domain), "deny", "regex")

        return self.get(domain_block)
