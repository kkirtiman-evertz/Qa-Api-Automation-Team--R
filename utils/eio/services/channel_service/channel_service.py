"""Importing necessary modules for logging and generating UUIDs."""

import logging
import random
import uuid

from utils.eio.clients.wsclient import EIOWSClient
from utils.eio.services import Service


class ChannelService(Service):
    """Defining channel service functions"""

    def __init__(self, eio_client):
        super().__init__(eio_client)

    @staticmethod
    def insert_sequence(channel_id, start_mode, template, asset_id, ws_client):
        """
        Insert the new sequence to the playlist.
        @param channel_id: ID for the channel.
        @param start_mode: Start mode of the event - variable/fixed/manual
        @param template: Name of the template.
        @param asset_id: AssetId of the sequence
        @param ws_client: Websocket client
        @return: Inserted sequence ID; or the error code.
        """
        insert_sequence_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "route": "channel-service.default",
            "params": {
                "channelId": channel_id,
                "templateForm": {
                    "startMode": start_mode,
                    "template": template,
                    "parameterMap": {
                        "transition-transType": "Cut",
                        "bug-startOffset": "00:00:01:00",
                        "bug-endOffset": "00:00:01:00",
                        "graphics-compoundList": [],
                        "material-matId": asset_id,
                    },
                },
            },
            "method": "insertSequence",
        }
        try:
            return ws_client.ws_call(json_request=insert_sequence_payload, raw=True)
        except Exception as exception:
            raise exception

    @staticmethod
    def clear_playlist(channel_id, ws_client):
        """
        Clear the playlist for the channel.
        @param ws_client: Websocket client
        @param channel_id: A unique identifier for a Channel.
        @return: Cleared playlist ; or the error code.
        """
        clear_playlist = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "route": "channel-service.default",
            "method": "clearPlaylist",
            "params": {"channelId": channel_id},
        }
        try:
            result = ws_client.ws_call(clear_playlist, raw=True)
            result.update({"method": clear_playlist["method"]})
            logging.info(result)
            return result
        except Exception as exception:
            raise exception

    @staticmethod
    def get_playlist(channel_id, event_size, ws_client):
        """
        Get the playlist events for the channel.
        @param channel_id: A unique identifier for a Channel.
        @param event_size: A size of the events
        @param ws_client: Websocket client
        @return: Playlist data ; or the error code.
        """
        get_playlist = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "getPlaylist",
            "route": "channel-service.default",
            "params": {"channelId": channel_id, "page": "1", "size": event_size},
        }
        try:
            result = ws_client.ws_call(get_playlist, raw=True)
            result.update({"method": get_playlist["method"]})
            logging.info(result)
            return result
        except Exception as exception:
            raise exception

    @staticmethod
    def control_playlist(channel_id, ws_client, action):
        """
        Send a control message to perform an action on the playlist for a specific channel.
        Args:
            channel_id (str): A unique identifier for a Channel.
            ws_client: Websocket client
            action (str): The action to be performed on the playlist (e.g., 'take', 'hold').
        Returns:
            dict: The response from the WebSocket call.
        Raises:
            Exception: If an error occurs during the WebSocket call or processing.
        """
        try:
            request_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "route": "channel-service.default",
                "method": "control",
                "params": {"channelId": channel_id, "action": action},
            }
            return ws_client.ws_call(request_message)
        except Exception as exception:
            raise exception

    @staticmethod
    def get_item_details(channel_id, ws_client, sequence_id):
        """
        Retrieve detailed information about a specific item (sequence) in a channel's playlist.
        Args:
            channel_id (str): The unique identifier of the channel.
            ws_client: Websocket client for communication.
            sequence_id (str): The unique identifier of the sequence (item) to retrieve details for.
        Returns:
            dict: A dictionary containing detailed information about the specified item in the playlist.
        Raises:
            Exception: If an error occurs during the retrieval of item details.
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "getItemDetails",
                "route": "channel-service.default",
                "params": {
                    "channelId": channel_id,
                    "item": sequence_id,
                    "uiType": "PLAYLIST",
                },
            }

            return ws_client.ws_call(payload)
        except Exception as exception:
            raise exception

    @staticmethod
    def handle_channel_registration(channel_id, ws_client, register=True):
        """
        Register or deregister for playlist updates for a single channel.
        Args:
            channel_id (str): A unique identifier for a Channel.
            ws_client: Websocket client
            register (bool): If True, register; if False, deregister.

        Returns:
            dict: The registration status or the error message.
        """
        method = "register" if register else "deregister"
        channel_action = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "route": "channel-service.default",
            "params": {"channelId": channel_id},
            "method": method,
        }
        try:
            result = ws_client.ws_call(channel_action, raw=True)
            logging.info(result)
            return result
        except Exception as exception:
            raise exception

    @staticmethod
    def delete_sequence(sequence_id, channel_id, ws_client):
        """
        Delete a sequence with the specified sequence_id in the given channel.
        Args:
            sequence_id (str): The ID of the sequence to be deleted.
            channel_id (str): The ID of the channel where the sequence exists.
            ws_client: The WebSocket client for communication.
        Returns:
            dict: A dictionary containing the response from the WebSocket call.
        Raises:
            Exception: If an error occurs during the WebSocket call or processing.
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "route": "channel-service.default",
                "method": "deleteSequences",
                "params": {
                    "channelId": channel_id,
                    "regions": [{"endId": sequence_id, "startId": sequence_id}],
                },
            }
            return ws_client.ws_call(payload)
        except Exception as exception:
            raise exception
