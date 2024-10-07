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

#from ..dependencies import get_token_header

logger = logging.getLogger()


class MasterEnabler(BaseHTTPHandler):
#        self.reqparse = reqparse.RequestParser()
### FIXME
#        self.reqparse.add_argument("disable_timer", type=int, default=None)
#        self.timer = 0

    def cmd(self, cmd=None, phList=None, pi=None, domain=None, comment=None):
        url = "/admin/api.php"
        gArgs = {"auth": self.token}
        pArgs = {}
        if not cmd:
            return
        if cmd:
            gArgs[cmd] = None
        if self.timer > 0:
            gArgs[cmd] = self.timer
        qs = urlparse.urlencode(gArgs)
        #        print(qs)
        with requests.session() as s:
            furl = "http://" + str(pi) + url + "?" + qs
            pprint(furl)
            return s.post(furl, data=pArgs).json()

    def post(self, command=None, timer=None):
        if timer:
            self.timer = timer
        for pi in self.piList:
            pprint(self.cmd(cmd="disable", pi=pi))

        #        self.cmd("disable, None, pi)
        return self.get(timer)

    def delete(self, command=None, timer=None):
        if timer:
            return
        for pi in self.piList:
            pprint(self.cmd(cmd="enable", pi=pi))
        return self.get(timer)

    def get(self, command=None, timer=None):
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
        logger.info({"Status": list(sumResp.keys())[0]})

        return {"Status": list(sumResp.keys())[0]}
