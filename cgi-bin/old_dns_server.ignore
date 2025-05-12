#!/usr/bin/env python3
# import pihole as ph

import requests
import hashlib
from urllib import parse as urlparse
import urllib3
import re
import sys
import os
import json

from flask.views import MethodView
import marshmallow as ma
from flask_smorest import Api, Blueprint, abort

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from flask import Flask
from flask_restful import Resource, Api, reqparse, abort
from pprint import pprint, pformat
from collections import defaultdict

import logging
import configparser

# ~njl/dev/src/overlord/dns_admin/venv/bin/python3

# FIXME: Move to GUNICORN Logging object
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s"
)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


def init_config(app, config_location="../etc/config.ini"):
    app_config = dict()
    config = configparser.ConfigParser()
    try:
        config.read(config_location)
        # Load DNS blocks into
        app_config["domains"] = dict()
        for provider in config.options("domains"):
            app_config["domains"][provider] = config.get(
                "domains", provider
            ).splitlines()
            print(provider)
        app_config["remote_pi_list"] = config.get(
            "general",
            "remote_pi_list",
            fallback=os.environ.get("REMOTE_PI_LIST"),
        ).split(sep=" ")
        app_config["remote_pi_password"] = config.get(
            "general",
            "remote_pi_password",
            fallback=os.environ.get("REMOTE_PI_PASSWORD"),
        )
        for i in ["DEVICE", "USERNAME", "PASSWORD"]:
            key = "ubiquiti_%s" % (i.lower())
            app_config[key] = config.get(
                "ubiquti",
                f"remote_{key}",
                fallback=os.environ.get(f"REMOTE_UBIQUITI_{i}"),
            )
        app_config["ubiquiti_targets"] = dict()
        for provider in config.options("ubiquiti_targets"):
            app_config["ubiquiti_targets"][provider] = config.get(
                "ubiquiti_targets", provider
            ).splitlines()
            print(provider)

    except configparser.Error as a:
        logger.error("Couldn't read configs from: %s %s" % (config_location, a))
    pprint(app_config)
    return app_config


# https://192.168.100.1/--data-raw '{"username":"overlord","password":"0verlorD","token":"","rememberMe":false}' -X POST -H 'Referer: https://192.168.100.1/login?redirect=%2F' -H 'Content-Type: application/json'
#
def init_ubiquiti(app_config):
    ## Gameplan - login and get token
    ## Store Token
    url = "/api/auth/login"
    device = app_config["ubiquiti_device"]
    pArgs = {
        "username": app_config["ubiquiti_username"],
        "password": app_config["ubiquiti_password"],
        "rememberMe": False,
        "token": "",
    }
    s = requests.session()
    furl = "https://" + str(device) + url
    # pprint(furl)
    logger.debug(f"{furl} with {pArgs}")
    resp = s.post(furl, json=pArgs, verify=False)
    app_config["ub_csrf_token"] = resp.headers["X-CSRF-Token"]
    app_config["ub_auth_token"] = (
        resp.cookies["TOKEN"] if "TOKEN" in resp.cookies else None
    )
    app_config["ub_session"] = s
    if resp.status_code != 200:
        print("Uh oh")
    pprint(app_config)


class UbiquitiOverlord(MethodView):
    def __init__(self):
        global app_config
        self.controller = app_config["ubiquiti_device"]
        self.macs = app_config["ubiquiti_targets"]
        self.auth_token = app_config["ub_auth_token"]
        self.csrf_token = app_config["ub_csrf_token"]
        self.base_api_url = f"https://{ self.controller }/proxy/network/api"
        self.base_api_v2_url = f"https://{ self.controller }/proxy/network/v2/api"
        self.mac_block_url = f"{self.base_api_url}/s/default/cmd/stamgr"
        self.client_list_url = f"{self.base_api_v2_url}/site/default/clients/active?includeTrafficUsage=false"
        self.session = app_config["ub_session"]

    def cmd(self, url, data, qs=None, method="post"):
        qs = urlparse.urlencode(qs)
        #        print(qs)
        furl = url + "?" + qs
        logger.debug(f"{furl} with {data}")
        if method == "get":
            return self.session.get(furl).json()
        return self.session.post(furl, json=data).json()

    def get(self, domain_block=None):
        x = None
        # query status of each one and make the call
        # check ipv6 prefix - alert if diff?


class PiHoleOverlord(Resource):
    def __init__(self):
        global app_config
        self.piList = app_config["remote_pi_list"]
        self.domains = app_config["domains"]
        self.password = app_config["remote_pi_password"]

        self.token = hashlib.sha256(
            hashlib.sha256(str(self.password).encode()).hexdigest().encode()
        ).hexdigest()

    def add(self, phList, domain, comment=None, pi="localpi"):
        return self.cmd("add", phList=phList, domain=domain, comment=comment, pi=pi)

    def sub(self, phList, domain, comment=None, pi="localpi"):
        return self.cmd("sub", phList=phList, domain=domain, comment=comment, pi=pi)

    def cmd(self, cmd, phList, method="post", pi=None, domain=None, comment=None):
        url = "/admin/api.php"
        gArgs = {"list": phList, "auth": self.token}
        pArgs = {}
        if domain:
            gArgs[cmd] = domain
        if comment:
            pArgs["comment"] = comment
        qs = urlparse.urlencode(gArgs)
        #        print(qs)
        with requests.session() as s:
            furl = "http://" + str(pi) + url + "?" + qs
            #            pprint(furl)
            logger.debug(f"{furl} with {pArgs}")
            if method == "get":
                return s.get(furl).json()
            return s.post(furl, data=pArgs).json()

    def transform(self, cleanDomain):
        fdomain = re.sub(r"\.", "\\.", cleanDomain)
        fdomain = re.sub(r"^", "(\.|^)", fdomain)
        fdomain = re.sub("$", "$", fdomain)
        return fdomain

    def sGet(self, domain_block=None, pi="localhost"):
        response = self.cmd(method="get", cmd="list", phList="regex_black", pi=pi)
        return response

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


class MasterEnabler(PiHoleOverlord):
    def __init__(self):
        super(MasterEnabler, self).__init__()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("disable_timer", type=int, default=None)
        self.timer = 0

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


class MasterStatus(MasterEnabler):
    def __init__(self):
        super().__init__()


class HealthCheck(MasterEnabler):
    def get(self, domain_block=None):
        if not domain_block:
            a = PiHoleOverlord()
            b = MasterEnabler()
            x = a.get()
            y = b.get()
            return {"Status1": x, "Status2": y}
        return {"Boo": "Doo2"}


app = Flask(__name__)
app.config["API_TITLE"] = "Overlord API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"
app_config = init_config(app)

if "ubiquiti_device" in app_config:
    init_ubiquiti(app_config)

api = Api(app)


# api.add_resource(Overlord, "/<string:domain_block>")
# # api.add_resource(MasterEnabler, )
# api.add_resource(
#     MasterEnabler,
#     "/master_switch/",
#     "/master_switch/<string:command>",
#     "/master_switch/<string:command>/<int:timer>",
# )
# api.add_resource(MasterStatus, "/master_status/", "/master_status", methods=["GET"])
api.add_resource(StatusCheck, "/status/", "/status/<string:domain_block>")

# api.add_resource(UbiquitiOverlord, "/ubiquiti/mac_block/block/<string:client_block>")
# api.add_resource(
#     UbiquitiOverlord,
#     "/ubiquiti/mac_block/status/<string:client_block>",
#     methods=["GET"],
# )
# api.add_resource(UbiquitiOverlord, "/ubiquiti/mac_block/unblock/<string:client_block>")

api.add_resource(HealthCheck, "/health/")


logger.info("starting the app...")
