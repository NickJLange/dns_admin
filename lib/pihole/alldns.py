import json
import logging
from typing import List
from pprint import pformat

from .base import BaseHTTPHandler


class MasterEnabler(BaseHTTPHandler):
    app_config: dict
    piList: List[str]
    domains: dict
    timer: int
    sessions: dict

    #        self.reqparse = reqparse.RequestParser()
    ### FIXME
    def __init__(self, app_config: dict) -> None:
        super().__init__(app_config=app_config)
        global logger
        logger = app_config["logger"]
        logger.debug("Started up all_dns")

    def flip_mode(self, status: bool | None = None):
        logger.debug(f"Flipping DNS blocking to {'enabled' if status else 'disabled'}")
        stateMap = {"enabled": "true", "disabled": "false"}
        if not self.logged_in:
            logger.debug("Not logged in, logging in...")
            self.first_connect()
        retv = list()
        for _, pi in self.sessions.items():
            pi.dns_control.set_blocking_status(status, self.timer)
            retp = pi.dns_control.get_blocking_status()
            #            logger.debug(f"DNS status on {type(pi)}: {pformat(status)}")
            retv.append(
                json.dumps({k: retp[k] for k in ["blocking"]})
            )  # timer is ticking, so whill not converge
        if len(set(retv)) > 1:
            logger.warning(
                f"Inconsistent states detected among devices {pformat(retv)}"
            )
            return {"status": "unknown"}  #        self.cmd("disable, None, pi)
        rets = json.loads(retv[0])
        return {"status": stateMap[rets["blocking"]]}

    def disable_dns_blocking(self, timer=None):
        if timer:
            self.timer = timer
        return self.flip_mode(status=False)
        # {'blocking': 'disabled', 'timer': 60 ...}

    def enable_dns_blocking(self, timer=30):
        if timer:
            self.timer = timer
        return self.flip_mode(status=True)

    def get(self):
        stateMap = {"enabled": "true", "disabled": "false"}
        logger.debug("Getting DNS blocking status")
        if not self.logged_in:
            logger.debug("Not logged in, logging in...")
            self.first_connect()
        retv = list()
        for _, pi in self.sessions.items():
            logger.debug(f"Getting DNS status on {type(pi)}")
            status = pi.dns_control.get_blocking_status()
            retv.append(
                json.dumps({k: status[k] for k in ["blocking"]})
            )  # timer is ticking, so whill not converge
        if len(set(retv)) > 1:
            logger.warning("Inconsistent states detected among devices")
            logger.warning(f"States: {pformat(retv)}")
            return {"status": "unknown"}  #        self.cmd("disable, None, pi)
        rets = json.loads(retv[0])
        return {"status": stateMap[rets["blocking"]]}
