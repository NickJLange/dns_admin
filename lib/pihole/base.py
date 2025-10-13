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
from pydantic import BaseModel, BaseConfig, ConfigDict
from typing import Optional, List
from pprint import pprint, pformat
from pihole6api import PiHole6Client

logger = logging.getLogger()


class BaseHTTPHandler(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    app_config: dict
    piList: List[str]
    domains: dict
    password: str
    url: str
    token: str
    timer: int
    sessions: dict
    logged_in: bool = False

    def __init__(self, app_config: dict) -> None:
        super().__init__(
            app_config=app_config,
            piList=app_config["remote_pi_list"],
            domains=app_config["domains"],
            password=app_config["remote_pi_password"],
            url="/admin/api.php",
            token=app_config["remote_pi_token"],
            timer=0,
            sessions=dict(),
        )

    #        self.token = hashlib.sha256(
    #            hashlib.sha256(str(self.password).encode()).hexdigest().encode()
    #        ).hexdigest()

    def first_connect(self):
        """
        Establishes initial connection to the Pihole  controller.

        This method performs the following tasks:
        1. Creates a new session.
        2. Sends a POST request to the login endpoint.
        3. Updates the object with the new session

        Raises:
            HTTPException: If the login request fails (status code != 200).

        Note:
            This method should be called before making any other API requests.
        """

        if self.logged_in:
            logger.debug("Already logged in. Skipping first_connect() method.")
            return
        pArgs = {"pw": self.password, "persistentlogin": "on"}
        url = "/admin/login.php"
        for pi in self.piList:
            furl = "http://" + str(pi)
            self.sessions[pi] = PiHoleAPI(furl, self.password)
            # self.sessions[pi] = requests.Session()
        #             logger.debug(f"'{furl}' with '{pArgs}'")
        # #            self.sessions[pi].headers.update({'User-Agent': 'curl/8.7.1'})
        # #            self.sessions[pi].headers.update({'Referer': furl})
        # #            self.sessions[pi].headers.update({'Sec-GPC': "1"})
        # #            self.sessions[pi].headers.update({'DNT': "1"})
        # #            self.sessions[pi].headers.update({'Origin': "http://" + str(pi) })
        # #            self.sessions[pi].headers.update({'Content-Type': "application/x-www-form-urlencoded" })
        #             resp = self.sessions[pi].post(furl, data=pArgs, verify=True)
        #             if resp.status_code != 200:
        #                 logger.error("Failed to login to pihole controller with status code %s", resp.status_code)
        #                 self.logged_in = False
        #                 return
        #             logger.debug(self.sessions[pi].cookies)
        self.logged_in = True

    def cmd(self, cmd, phList, method="post", pi=None, domain=None, comment=None):
        if not self.logged_in:
            logger.debug("Not logged in, logging in...")
            self.first_connect()
        gArgs = {"list": phList, "auth": self.token}
        pArgs = {}
        if domain:
            gArgs[cmd] = domain
        if comment:
            pArgs["comment"] = comment
        qs = urlparse.urlencode(gArgs)
        #        print(qs)
        furl = "http://" + str(pi) + self.url + "?" + qs
        #            pprint(furl)
        logger.debug(f"'{furl}' with '{pArgs}'")
        if method == "get":
            temp = self.sessions[pi].get(furl, timeout=(3.05, 5))
            try:
                return temp.json()
            except:
                logger.error(f"Error in get: {temp.text}")
        temp = self.sessions[pi].post(furl, data=pArgs, timeout=(3.05, 5))
        try:
            return temp.json()
        except:
            logger.error(f"Error in get: {temp.text}")

    def transform(self, cleanDomain):
        fdomain = re.sub(r"\.", "\\.", cleanDomain)
        fdomain = re.sub(r"^", "(\\.|^)", fdomain)
        fdomain = re.sub("$", "$", fdomain)
        return fdomain
