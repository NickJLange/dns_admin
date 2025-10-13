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

from .base import BaseHTTPHandler
from pihole6api import PiHoleAPI

# from ..dependencies import get_token_header

logger = logging.getLogger()

import http.client as http_client

http_client.HTTPConnection.debuglevel = 1


class MasterEnabler(BaseHTTPHandler):
    app_config: dict
    piList: List[str]
    domains: dict
    password: str
    token: str
    timer: int
    sessions: dict

    #        self.reqparse = reqparse.RequestParser()
    ### FIXME
    #        self.reqparse.add_argument("disable_timer", type=int, default=None)
    #        self.timer = 0
    def __init__(self, app_config: dict) -> None:
        super().__init__(app_config=app_config)
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    def cmd(self, cmd=None, phList=None, pi=None, domain=None, comment=None, method="post"):
        if not self.logged_in:
            logger.debug("Not logged in, logging in...")
            self.first_connect()
        url = "/admin/api.php"
        gArgs = {"auth": self.token}
        pArgs = {}
        if not cmd:
            return
        if cmd == "disable" or cmd == "enable":
            gArgs[cmd] = self.timer
            qs = urlparse.urlencode(gArgs)
        else:
            qs = cmd
        #        print(qs)

        furl = "http://" + str(pi) + url + "?" + qs
        pprint(furl)
        logger.debug(f"'{furl}' and cookies {self.sessions[pi].cookies}")
        if method == "get":
            temp = self.sessions[pi].get(furl)
            logger.debug(temp.json())
            return temp.json()
        temp = self.sessions[pi].post(furl, data=pArgs)
        logger.debug(temp.text)
        return temp.json()

    def disable(self, command=None, timer=None):
        if timer:
            self.timer = timer
        for pi in self.piList:
            logger.info(self.cmd(cmd="disable", pi=pi))

        #        self.cmd("disable, None, pi)
        return self.get(timer)

    def delete(self, command=None, timer=None):
        if timer:
            self.timer = timer
        for pi in self.piList:
            logger.info(self.cmd(cmd="enable", pi=pi))
        return self.get(timer)

    def get(self, command=None, timer=None):
        if timer:
            self.timer = timer
        resps = list()
        sumResp = defaultdict(list)
        for pi in self.piList:
            logger.debug(f"Checking status {pi}")
            resps.append(self.cmd(method="get", cmd="summaryRaw", pi=pi))
        logger.debug(pformat(resps))

        stateMap = {"enabled": "on", "disabled": "off"}
        ## enumerate states, accounting for fact some states might be different between devices...
        for piResp in resps:
            translated = stateMap[piResp["status"]]
            #           translated = "disabled"
            sumResp[translated].append(translated)
        # FIXME: Can HomeKit represent this???
        if len(sumResp.keys()) > 1:
            return {"status": "off"}
        logger.info({"status": list(sumResp.keys())[0]})

        return {"status": list(sumResp.keys())[0]}
