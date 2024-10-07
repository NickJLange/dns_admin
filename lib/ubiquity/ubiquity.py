import configparser
import hashlib
import json
import logging
import os
import re
import sys
from collections import defaultdict
from pprint import pformat, pprint
from typing import List, Optional
from urllib import parse as urlparse

import requests
import urllib3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, BaseConfig

BaseConfig.arbitrary_types_allowed = True  # change #1


logger = logging.getLogger()

# https://192.168.100.1/--data-raw '{"username":"overlord","password":"0verlorD","token":"","rememberMe":false}' -X POST -H 'Referer: https://192.168.100.1/login?redirect=%2F' -H 'Content-Type: application/json'
#


router = APIRouter(
    prefix="/ubiquiti",
    tags=["ubiquiti"],
#    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

class UbiquitiOverlord(BaseModel):
    app_config: dict
    controller: str
    macs: list
    auth_token: str | None
    csrf_token: str
    base_api_url: str
    base_api_v2_url: str
    mac_block_url: str
    client_list_url: str
#    session: requests.Session
    def __init__(self, app_config: dict):
        self.controller = app_config["ubiquiti_device"]
        self.macs = app_config["ubiquiti_targets"]
        self.username = app_config["ubiquiti_username"]
        self.password = app_config["ubiquiti_password"]
        self.base_api_url = f"https://{ self.controller }/proxy/network/api"
        self.base_api_v2_url = f"https://{ self.controller }/proxy/network/v2/api"
        self.mac_block_url = f"{self.base_api_url}/s/default/cmd/stamgr"
        self.client_list_url = f"{self.base_api_v2_url}/site/default/clients/active?includeTrafficUsage=false"
        self.session = None

    def first_connect(self):
        """
        Establishes initial connection to the Ubiquiti controller.

        This method performs the following tasks:
        1. Creates a new session.
        2. Sends a POST request to the login endpoint.
        3. Extracts and stores the CSRF token and authentication token from the response.
        4. Updates the app_config with the new session and tokens.

        Raises:
            HTTPException: If the login request fails (status code != 200).

        Note:
            This method should be called before making any other API requests.
        """
        pArgs = {
            "username": self.username,
            "password": self.password,
            "rememberMe": False,
            "token": "",
        }
        url = "/api/auth/login"
        self.session = requests.session()
        furl = "https://" + str(self.controller) + url
        # pprint(furl)
        logger.debug(f"{furl} with {pArgs}")
        resp = self.session.post(furl, json=pArgs, verify=False)
        self.auth_token = (
            resp.cookies["TOKEN"] if "TOKEN" in resp.cookies else None
        )
        self.csrf_token = resp.headers["X-CSRF-Token"]
        if resp.status_code != 200:
            print("Uh oh")

    def cmd(self, url, data, qs=None, method="post"):
        if self.session is None:
            self.first_connect()
        qs = urlparse.urlencode(qs)
        #        print(qs)
        furl = url + "?" + qs
        logger.debug(f"{furl} with {data}")
        if method == "get":
            return self.session.get(furl).json()
        return self.session.post(furl, json=data).json()

    def get(self, domain_block=None):
        x = None
