"""Importing necessary modules for logging, time, and generating UUIDs."""

import logging
import time
import uuid

from utils.eio.clients.httpclient import EIOHttpClient
from utils.eio.clients.wsclient import EIOWSClient

TEMPLATE_NAME = "Program"
START_MODE = "manual"
CLIENT_ID = str(uuid.uuid4())
DEFAULT_ROUTE = "channel-service.default"
INVALID_ROUTE_SETUP = "channel-service"
ASSET_ID = "TEST-ASSET"
EVENT_SIZE = 100


def test_insert_sequence(eio_client: EIOHttpClient, current_environment):
    """This is function to insert sequence in playlist"""
    channel_id = current_environment["channel_id"]
    ws_client = EIOWSClient(eio_client.ws_server_host, eio_client.auth_token, CLIENT_ID)
    inserted_sequence = eio_client.channel_service.insert_sequence(
        channel_id, START_MODE, TEMPLATE_NAME, ASSET_ID, ws_client
    )
    assert (
        inserted_sequence["result"]["params"]["templateForm"]["startMode"] == START_MODE
    )
    assert (
        inserted_sequence["result"]["params"]["templateForm"]["template"]
        == TEMPLATE_NAME
    )
    assert (
        inserted_sequence["result"]["params"]["templateForm"]["parameterMap"][
            "material-matId"
        ]
        == ASSET_ID
    )
    capture_sequence_id = inserted_sequence["result"]["result"]
    assert "sequence$" in capture_sequence_id
    logging.info("Sequence inserted - %s", capture_sequence_id)


def test_clear_playlist(eio_client: EIOHttpClient, current_environment):
    """This is function to clear all the events from playlist"""
    channel_id = current_environment["channel_id"]
    # Clear playlist for the channel
    ws_client = EIOWSClient(eio_client.ws_server_host, eio_client.auth_token, CLIENT_ID)
    eio_client.channel_service.clear_playlist(channel_id, ws_client)
    time.sleep(5)  # awaiting to clear the actual playlist on the channel
    # Validating events are cleared or not
    output_get_playlist = eio_client.channel_service.get_playlist(
        channel_id, EVENT_SIZE, ws_client
    )
    assert output_get_playlist["result"]["result"]["items"] == []
