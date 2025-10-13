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
        super().__init__(app_config = app_config,
            piList = app_config["remote_pi_list"],
            domains = app_config["domains"],
            password = app_config["remote_pi_password"],
            url = "/admin/api.php",
            token = app_config["remote_pi_token"],
            timer = 0,
            sessions = dict()
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
        pArgs = {
            "pw": self.password,
            "persistentlogin":"on"
        }
        url = "/admin/login.php"
        for pi in self.piList:
            try:
                self.sessions[pi] = requests.Session()
                furl = "https://" + str(pi) + url
                logger.debug(f"'{furl}' with '{pArgs}'")
                resp = self.sessions[pi].post(furl, data=pArgs, verify=True)
                resp.raise_for_status()
                logger.debug(self.sessions[pi].cookies)
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to login to pihole controller {pi}: {e}")
                self.logged_in = False
                return
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
        furl = "https://" + str(pi) + self.url + "?" + qs
        logger.debug(f"'{furl}' with '{pArgs}'")

        try:
            if method == "get":
                response = self.sessions[pi].get(furl, timeout=(3.05, 5), verify=True)
            else:
                response = self.sessions[pi].post(furl, data=pArgs, timeout=(3.05, 5), verify=True)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            raise HTTPException(status_code=500, detail="Pi-hole API communication error")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from response: {response.text}")
            raise HTTPException(status_code=500, detail="Invalid JSON response from Pi-hole API")


    def transform(self, cleanDomain):
        fdomain = re.sub(r"\.", "\\.", cleanDomain)
        fdomain = re.sub(r"^", "(\\.|^)", fdomain)
        fdomain = re.sub("$", "$", fdomain)
        return fdomain
