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
import logging
import configparser
from pprint import pprint, pformat
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, BaseConfig
from typing import Optional, List


sys.path.append(os.path.join(os.path.dirname(__file__), '../lib/'))



# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#import PiHoleOverlord, MasterEnabler, MasterStatus, StatusCheck, HealthCheck

description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""

app = FastAPI(
    title="Overlord API",
    version="v2",
    openapi_version="3.0.2",
    description=description,
    summary="Deadpool's favorite app. Nuff said.",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "MIT",
    },
)




urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


def init_config(app, config_location:str ="../etc/config.ini"):
    app_config = dict()
    config = configparser.ConfigParser()
    try:
        config.read(config_location)
        # Load DNS blocks into
        logger.info(pformat(config.sections()))
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
    logger.info (app_config)
    return app_config



        # query status of each one and make the call
        # check ipv6 prefix - alert if diff?



config_file = os.path.join(os.path.dirname(__file__), '../etc/', 'config.ini')

app_config = init_config(app,config_file)

#pihole.init()
from ubiquity import ubiquity  # noqa: E402
from pihole import pihole_core# noqa: E402

pihole_core.init(app_config)

logger.info("Adding Endpoints...")

app.include_router(pihole_core.main_router)
app.include_router(pihole_core.alldns_router)
app.include_router(ubiquity.router)


logger.info("starting the app...")

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}



#api.add_resource(PiHoleOverlord, "/<string:domain_block>",resource_class_kwargs={ 'app_config': app_config })
#api.add_resource(UbiquitiOverlord,"/<string:command>",resource_class_kwargs={'app_config': app_config})

# api.add_resource(MasterEnabler, )
# api.add_resource(
#     MasterEnabler,
#     "/master_switch/",
#     "/master_switch/<string:command>",
#     "/master_switch/<string:command>/<int:timer>",
#     resource_class_kwargs={ 'app_config': app_config }
# )
# api.add_resource(MasterStatus, "/master_status/", "/master_status", methods=["GET"],resource_class_kwargs={ 'app_config': app_config })
# api.add_resource(StatusCheck, "/status/", "/status/<string:domain_block>",resource_class_kwargs={ 'app_config': app_config })

# api.add_resource(UbiquitiOverlord, "/ubiquiti/mac_block/block/<string:client_block>")
# api.add_resource(
#     UbiquitiOverlord,
#     "/ubiquiti/mac_block/status/<string:client_block>",
#     methods=["GET"],
# )
# api.add_resource(UbiquitiOverlord, "/ubiquiti/mac_block/unblock/<string:client_block>")

# api.add_resource(HealthCheck, "/health/",resource_class_kwargs={ 'app_config': app_config })
