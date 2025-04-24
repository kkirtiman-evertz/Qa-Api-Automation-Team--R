"""Importing necessary modules for logging."""

import logging

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class Service:
    """
    This class is to be implemented by each subsystem
    No methods to implement
    @type ws_client: utils.eio.clients.httpclient.EIOHttpClient
    """

    def __init__(self, eio_client):
        self.eio_client = eio_client

    def rest_call(
        self,
        method,
        uri=None,
        end_point="",
        payload=None,
        params=None,
        auth=None,
        custom_headers=None,
    ):
        """Setting up the creds for making a rest call"""
        return self.eio_client.rest_call(
            method,
            uri=uri,
            end_point=end_point,
            payload=payload,
            params=params,
            auth=auth,
            custom_headers=custom_headers,
        )
