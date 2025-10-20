import re

import logging
from pydantic import BaseModel, BaseConfig, ConfigDict
from typing import Optional, List
from pprint import pprint, pformat
from pihole6api import PiHole6Client

# global default_log_level
# logger = logging.getLogger(__name__)
logger: logging.Logger | None = None


class BaseHTTPHandler(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    app_config: dict
    piList: List[str]
    domains: dict
    allow_domains: dict
    block_domains: dict
    password: str
    url: str
    timer: int
    sessions: dict[str, PiHole6Client]
    logged_in: bool = False

    def __init__(self, app_config: dict) -> None:
        super().__init__(
            app_config=app_config,
            piList=app_config["remote_pi_list"],
            domains=dict(),
            allow_domains=app_config["allow_domains"],
            block_domains=app_config["block_domains"],
            password=app_config["remote_pi_password"],
            url="/admin/api.php",
            timer=0,
            sessions=dict(),
        )
        self.password = app_config["remote_pi_password"]
        logger = logging.getLogger(__name__)
        logger.setLevel(app_config["default_log_level"])
        pi_log = logging.getLogger("pihole6api")
        pi_log.setLevel(logging.WARN)

        for type in ["deny", "allow"]:
            self.domains[type] = dict()
        self.domains["deny"] = self.block_domains
        self.domains["allow"] = self.allow_domains
        logger.debug(
            f"Merged domains: {len(self.domains.keys())} vs {len(self.block_domains.keys())} vs {len(self.allow_domains.keys())}"
        )

    def shutdown(self):
        if self.logged_in:
            for _, pi in self.sessions.items():
                pi.close_session()
            self.logged_in = False

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
        self.logged_in = True
        for pi in self.piList:
            furl = "http://" + str(pi)
            try:
                logging.debug(f"Connecting to PiHole at {furl} for {pi}")
                self.sessions[pi] = PiHole6Client(furl, self.password)
                logging.debug(f"Connected to PiHole with {self.sessions[pi]}")
            except Exception as e:
                logger.error(f"Error connecting to PiHole at {furl}: {e}")
                self.logged_in = False
                continue

    def transform(self, cleanDomain):
        fdomain = re.sub(r"\.", "\\.", cleanDomain)
        fdomain = re.sub(r"^", "(\\.|^)", fdomain)
        fdomain = re.sub("$", "$", fdomain)
        return fdomain
