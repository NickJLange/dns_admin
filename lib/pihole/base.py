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
from pydantic import BaseModel, BaseConfig
from typing import Optional, List
from pprint import pprint, pformat

logger = logging.getLogger()

class BaseHTTPHandler(BaseModel):
    app_config: dict
    piList: List[str]
    domains: dict
    password: str
    url: str
    token: str

    def __init__(self, app_config: dict) -> None:
        super().__init__(app_config = app_config,
            piList = app_config["remote_pi_list"],
            domains = app_config["domains"],
            password = app_config["remote_pi_password"],
            url = "/admin/api.php",
            token = ""
        )
        self.token = hashlib.sha256(
            hashlib.sha256(str(self.password).encode()).hexdigest().encode()
        ).hexdigest()

    def cmd(self, cmd, phList, method="post", pi=None, domain=None, comment=None):
        gArgs = {"list": phList, "auth": self.token}
        pArgs = {}
        if domain:
            gArgs[cmd] = domain
        if comment:
            pArgs["comment"] = comment
        qs = urlparse.urlencode(gArgs)
        #        print(qs)
        with requests.session() as s:
            furl = "http://" + str(pi) + self.url + "?" + qs
            #            pprint(furl)
            logger.debug(f"{furl} with {pArgs}")
            if method == "get":
                return s.get(furl).json()
            return s.post(furl, data=pArgs).json()

    def transform(self, cleanDomain):
        fdomain = re.sub(r"\.", "\\.", cleanDomain)
        fdomain = re.sub(r"^", "(\\.|^)", fdomain)
        fdomain = re.sub("$", "$", fdomain)
        return fdomain
