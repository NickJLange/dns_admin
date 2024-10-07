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


from .base import BaseHTTPHandler
logger = logging.getLogger()

class PiHoleOverlord(BaseHTTPHandler):
    app_config: dict
    piList: List[str]
    domains: dict
    password: str
    token: str

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
        #        pprint(domain_block)
        if domain_block is None or domain_block not in self.domains:
            return {"Status": resps}
        state = "off"

        for domain in self.domains[domain_block]:
            logger.debug("%s -> %s" % (domain, self.transform(domain)))
            #            pprint(self.transform(domain))
            for pi in resps:
                for d in pi["data"]:
                    #                    pprint(d)
                    if (
                        "domain" in d
                        and "enabled" in d
                        and self.transform(domain) == d["domain"]
                        and d["enabled"] == 1
                    ):
                        logger.info("Switching on %s %s" % (domain, d))
                        state = "on"
                    if (
                        "domain" in d
                        and "enabled" in d
                        and self.transform(domain) == d["domain"]
                        and d["enabled"] == 0
                    ):
                        logger.info("Switching off %s %s" % (domain, d))
                        state = "off"
        return {"Status": state}

    def post(self, domain_block=None):
        if not domain_block:
            return "No", 404
        logger.info("Request to turn on %s" % domain_block)
        for pi in self.piList:
            #            pprint(pi)
            for domain in self.domains[domain_block]:
                self.add("regex_black", self.transform(domain), "Unfeeling", pi=pi)
        #                pprint(resp)
        return self.get(domain_block)

    def delete(self, domain_block=None):
        if not domain_block:
            return "No", 404
        logger.info("Request to turn off %s" % domain_block)
        for pi in self.piList:
            #            pprint(pi)
            for domain in self.domains[domain_block]:
                self.sub("regex_black", self.transform(domain), "Unfeeling", pi=pi)
        #                pprint(resp)
        return self.get(domain_block)
