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

import http.client as http_client
http_client.HTTPConnection.debuglevel = 0

# You must initialize logging, otherwise you'll not see debug output.

logger = logging.getLogger()
requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True


from .base import BaseHTTPHandler
logger = logging.getLogger()

class PiHoleOverlord(BaseHTTPHandler):
    app_config: dict
    piList: List[str]
    domains: dict
    password: str
    token: str
    timer: int #unused, FIXME for optional fields in base class
    sessions: dict


    def __init__(self, app_config: dict) -> None:
        super().__init__(app_config = app_config,
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

        if domain_block is None or domain_block not in self.domains:
            return {"status": resps}

        logger.info(f"Checking status for domain block: {domain_block}")
        domain_statuses = {}
        for domain in self.domains[domain_block]:
            transformed_domain = self.transform(domain)
            domain_statuses[domain] = "off"  # Default to off
            logger.debug(f"Checking domain: {domain} -> {transformed_domain}")

            for pi_response in resps:
                if 'data' in pi_response:
                    for d in pi_response["data"]:
                        if d.get("domain") == transformed_domain:
                            if d.get("enabled") == 1:
                                domain_statuses[domain] = "on"
                                logger.info(f"Domain {domain} is ON on a pihole")
                                break  # Found status for this domain, move to next
                            else:
                                logger.info(f"Domain {domain} is OFF on a pihole")
                if domain_statuses[domain] == "on":
                    break  # already found it's on for this domain

        # If any domain in the block is "on", the whole block is considered "on"
        final_state = "off"
        for domain, status in domain_statuses.items():
            if status == "on":
                final_state = "on"
                break

        logger.info(f"Final status for domain block {domain_block}: {final_state}")
        return {"status": final_state}

    def post(self, direction: str, domain_block: str | None = None):
        if not domain_block:
            raise HTTPException(status_code=404, detail="Domain Block not configured")
        logger.info(f"Request to {direction} {domain_block}")
        for pi in self.piList:
            for domain in self.domains[domain_block]:
                if direction == "disable":
                    self.cmd("add", "regex_black", pi=pi, domain=self.transform(domain))
                elif direction == "enable":
                    self.cmd("sub", "regex_black", pi=pi, domain=self.transform(domain))
        return self.get(domain_block)
