#!/usr/bin/env python3
# import pihole as ph

import requests
import hashlib
import urllib
import re
import sys
import os

from flask import Flask
from flask_restful import Resource, Api, reqparse, abort
from pprint import pprint, pformat
from collections import defaultdict

import logging
import configparser


# FIXME: Move to GUNICORN Logging object
logger = logging.getLogger()
logger.setLevel(logging.INFO)
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
        logger.info("Succesfully read configs from: %s " % config_location)
    except configparser.Error as a:
        logger.error("Couldn't read configs from: %s %s" % (config_location, a))
    pprint(app_config)
    return app_config


app = Flask(__name__)
api = Api(app)
app_config = init_config(app)


class Overlord(Resource):
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

    def cmd(self, cmd, phList, pi=None, domain=None, comment=None):
        url = "/admin/api.php"
        gArgs = {"list": phList, "auth": self.token}
        pArgs = {}
        if domain:
            gArgs[cmd] = domain
        if comment:
            pArgs["comment"] = comment
        qs = urllib.parse.urlencode(gArgs)
        #        print(qs)
        with requests.session() as s:
            furl = "http://" + str(pi) + url + "?" + qs
            #            pprint(furl)
            return s.post(furl, data=pArgs).json()

    def transform(self, cleanDomain):
        fdomain = re.sub(r"\.", "\\.", cleanDomain)
        fdomain = re.sub(r"^", "(\.|^)", fdomain)
        fdomain = re.sub("$", "$", fdomain)
        return fdomain

    def sGet(self, domain_block=None, pi="localhost"):
        response = self.cmd(cmd="list", phList="regex_black", pi=pi)
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


class MasterEnabler(Overlord):
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
        qs = urllib.parse.urlencode(gArgs)
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
            a = Overlord()
            return a.get(domain_block)


class HealthCheck(MasterEnabler):
    def get(self, domain_block=None):
        if not domain_block:
            a = Overlord()
            b = MasterEnabler()
            x = a.get()
            y = b.get()
            return {"Status1": x, "Status2": y}
        return {"Boo": "Doo2"}


api.add_resource(Overlord, "/<string:domain_block>")
# api.add_resource(MasterEnabler, )
api.add_resource(
    MasterEnabler, "/master_switch/", "/master_switch/<string:command>/<int:timer>"
)
api.add_resource(StatusCheck, "/status/", "/status/<string:domain_block>")
api.add_resource(HealthCheck, "/health/")

logger.info("starting the app...")
