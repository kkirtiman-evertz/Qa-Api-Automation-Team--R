"""Importing necessary modules for logging and time."""

import logging
import time

import requests
from requests.auth import HTTPBasicAuth

from utils.eio.clients.wsclient import EIOWSClient
from utils.eio.services.channel_management import ChannelManagement
from utils.eio.services.channel_service.channel_service import ChannelService
from utils.eio.services.channel_service.scte_taker import ScteTaker
from utils.eio.services.flow_manager import FlowManager
from utils.eio.services.playlist_management import PlaylistManagement
from utils.eio.services.playlist_search_replace import PlaylistSearchAndReplace
from utils.eio.services.schedule_asset_external import ScheduleAssetExternal
from utils.eio.services.schedule_asset_internal_service import (
    ScheduledAssetsInternalHelper,
)

logging.basicConfig(
    filename="tests.log",
    level=logging.WARNING,
    format="%(asctime)s [%(name)s:%(lineno)s] [%(levelname)-5.5s]"
    " %(message)s [%(threadName)-10.10s]",
)
logger = logging.getLogger(__name__)


class EIOHttpClient:
    """JSON Object in, JSON Object out, HTTP connection to Evertz.io"""

    def __init__(self, server, ws_server_host, tenant, user, password, auth_token=None):
        self.basic_auth = HTTPBasicAuth(user, password)
        self.server = server
        self.ws_server_host = ws_server_host
        self.tenant = tenant
        self.auth_token = auth_token
        self.refresh_token = None
        self.ws_client = None
        self.token_timeout = time.time() + 60 * 55  # 55 minutes from now
        self._headers = {
            "Authorization": auth_token,
            "Content-type": "application/json",
        }
        self.channel_management: ChannelManagement = ChannelManagement(self)
        self.channel_service: ChannelService = ChannelService(self)
        self.playlist_management: PlaylistManagement = PlaylistManagement(self)
        self.flow_manager: FlowManager = FlowManager(self)
        self.schedule_asset_external: ScheduleAssetExternal = ScheduleAssetExternal(
            self
        )
        self.playlist_search_replace: PlaylistSearchAndReplace = (
            PlaylistSearchAndReplace(self)
        )
        self.schedule_asset_internal_service: ScheduledAssetsInternalHelper = (
            ScheduledAssetsInternalHelper(self)
        )
        self.channel_service_scte_taker: ScteTaker = ScteTaker(self)

    def _set_auth_token(self, auth_token):
        self.auth_token = auth_token
        if self.ws_client is not None:
            self.ws_client.auth_token = self.auth_token
        self._headers = {
            "Authorization": self.auth_token,
            "Content-type": "application/json",
        }

    def signin(self):
        """Setting up env for sign in"""
        params = {"tenant": self.tenant}
        logger.info("Signing in to Evertz.io...")
        output = self._make_request(
            "POST", end_point="authenticate/signin", params=params, auth=self.basic_auth
        )
        self.refresh_token = output["output"]["RefreshToken"]
        self._set_auth_token(output["output"]["IdToken"])

    def refresh(self):
        """To refresh"""
        if not self.refresh_token:
            return
        params = {"tenant": self.tenant, "refresh_token": self.refresh_token}
        logger.info("Refreshing in to Evertz.io...")
        output = self._make_request(
            "POST", end_point="authenticate/refresh", params=params
        )
        self._set_auth_token(output["output"]["IdToken"])

    def get_ws_client(self, client_id) -> EIOWSClient:
        """To get WS client"""
        if self.ws_client is None:
            self.ws_client = EIOWSClient(
                self.ws_server_host, self.auth_token, client_id
            )
        return self.ws_client

    def close(self):
        """To close the WS connection"""
        if self.ws_client:
            self.ws_client.close()
            self.ws_client = None

    def _make_request(
        self,
        method,
        end_point="",
        payload=None,
        params=None,
        auth=None,
        custom_headers=None,
    ):

        try:
            if not params:
                params = {}
            uri = self.server
            headers = self._headers.copy()
            if custom_headers:
                headers.update(custom_headers)
            logger.debug(
                "REST Request - Type: %s Url: %s%s Headers: %s Request: %s",
                method,
                uri,
                end_point,
                headers,
                payload,
            )

            response = requests.request(
                method,
                f"{uri}{end_point}",
                json=payload,
                params=params,
                auth=auth,
                headers=headers,
            )
            status_code = response.status_code
            logger.debug("REST Response: %s", response.text)
            if status_code != 200:
                logger.debug(
                    "REST Response - Status: %s Reason: %s",
                    status_code,
                    response.reason,
                )
            output = response.json() if response.content else None
            size = len(response.content)
            exec_time = response.elapsed.microseconds / 1000  # in milliseconds
        except Exception as exception:
            logger.exception(
                "REST Request failed: [%s--%s]", type(exception), str(exception)
            )
            return {"status": 500, "size": 0, "exec": 0, "output": None, "url": uri}
        else:
            return {
                "status": status_code,
                "size": size,
                "exec": exec_time,
                "output": output,
                "url": response.request.url,
            }

    def rest_call(
        self,
        method,
        end_point="",
        payload=None,
        params=None,
        auth=None,
        custom_headers=None,
    ):
        """Defining a function to perform a rest call"""

        if time.time() > self.token_timeout:
            self.signin()
        return self._make_request(
            method,
            end_point=end_point,
            payload=payload,
            params=params,
            auth=auth,
            custom_headers=custom_headers,
        )
