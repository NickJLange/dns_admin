import logging
from fastapi import HTTPException
from typing import List
from pprint import pformat

from .base import BaseHTTPHandler

from pihole6api import PiHole6Client

logger: logging.Logger | None = None


class PiHoleOverlord(BaseHTTPHandler):
    app_config: dict
    piList: List[str]
    domains: dict
    block_domains: dict
    allow_domains: dict
    sessions: dict[str, PiHole6Client]

    def __init__(self, app_config: dict) -> None:
        super().__init__(
            app_config=app_config,
        )
        global logger
        logger = app_config["logger"]

    def get(self, domain_block=None):
        if domain_block is None or domain_block not in self.block_domains:
            return {"status": "Unknown"}
        if not self.logged_in:
            logger.debug("Not logged in, logging in...")
            self.first_connect()
        state = "true"
        control_type: str = "deny"
        logger.debug(f"Checking status {domain_block}")
        if domain_block in self.allow_domains:
            control_type = "allow"
            logger.debug(f"Using allow control for {domain_block}")
        for domain in self.domains[control_type][domain_block]:
            logger.debug("%s -> %s" % (domain, self.transform(domain)))
            #            pprint(self.transform(domain))
            for _, pi in self.sessions.items():
                resp = pi.domain_management.get_domain(domain, control_type, "regex")
                if len(resp["domains"]) == 0 or (
                    resp["domains"][0]["domain"] == domain
                    and not resp["domains"][0]["enabled"]
                ):
                    logger.debug(
                        f"Got domain response: {pformat(resp)} -> Marking Off for {domain_block}"
                    )
                    return {"status": "false"}
                # Does it exist and is enabled?
        logger.info(f"Result Status {state} for {domain_block}")
        return {"status": state}

    def post(
        self,
        direction: str,
        domain_block: str | None = None,
    ):
        if not domain_block:
            logger.error("No domain block specified")
            raise HTTPException(status_code=404, detail="Domain Block not configured")
        if not self.logged_in:
            logger.debug("Not logged in, logging in...")
            self.first_connect()
        control_type: str = "deny"
        logger.debug(f"Checking status {domain_block}")
        if domain_block in self.allow_domains:
            control_type = "allow"
            logger.debug(f"Using allow control for {domain_block}")

        logger.info(f"Request to {direction} {control_type} {domain_block}")
        for _, pi in self.sessions.items():
            retc = list()
            for domain in self.domains[control_type][domain_block]:
                rez = None
                if direction == "disable":
                    rez = pi.domain_management.delete_domain(
                        domain,
                        control_type,
                        "regex",
                    )
                elif direction == "enable":
                    rez = pi.domain_management.add_domain(
                        domain, control_type, "regex", groups=[0]
                    )
                else:
                    logger.error(f"Unknown direction: {direction}")
                    raise HTTPException(status_code=404, detail="Unknown direction")
                logger.debug(
                    f"{control_type}/{direction}/{domain} domain response: \n {rez['domains'][0]['enabled'] if rez and 'domains' in rez else 'Unknown'}"
                )
                retc.append(rez)
        return {"status": "ok"}
