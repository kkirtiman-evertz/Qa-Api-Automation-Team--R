"""Importing necessary modules for logging."""

import logging
import time

import pytest

from tests.tests_playlist_management.config.playlist_external_import_config import (
    SERVICE_NAME,
)
from utils.eio.services import Service


class PlaylistManagement(Service):
    """Defining Playlist Management services"""

    def __init__(self, eio_client):
        super().__init__(eio_client)

    @staticmethod
    def handle_request(ws_client, request_id, channel_id, request):
        """
        Register/deregister for Scheduler updates.
        @param ws_client: Websocket client.
        @param request_id: A unique identifier for each request.
        @param channel_id: A unique identifier for a Channel.
        @param request: Websocket request register/deregister.
        @return: The registration status; or the error message.
        """
        request_msg = {
            "jsonrpc": "2.0",
            "route": f"{SERVICE_NAME}.default",
            "method": request,
            "id": request_id,
            "params": {"channelId": channel_id},
        }
        try:
            result = ws_client.ws_call(request_msg, raw=True)
            result.update({"method": request_msg["method"]})
            logging.info(result)
            return result
        except Exception as exception:
            raise Exception("InvalidParams") from exception

    def generate_presigned_url(self, schedule_file_name, channel_id):
        """
        Generates S3 presigned URL
        @param schedule_file_name : File name which is need to upload
        @param channel_id: id for the channel
        @return: presigned URL
        """
        payload = {
            "data": {
                "type": "presignedUrlRequest",
                "attributes": {"fileName": schedule_file_name, "channelId": channel_id},
            }
        }
        response = self.eio_client.rest_call(
            "POST",
            end_point=f"{SERVICE_NAME}/import/presigned-url",
            payload=payload,
        )
        return response

    def playlist_export(self, channel_id, file_store_id, channel_name):
        """
        Exports the playlist to s3 bucket
        @param channel_id : channel id for playlist which is need to upload
        @param file_store_id: id for the file store
        @param channel_name: Save playlist under channel name
        @return: Playlist export ;or error code.
        """
        payload = {
            "data": {
                "type": "exportRequest",
                "attributes": {
                    "channelId": channel_id,
                    "fileStoreId": file_store_id,
                    "saveAsChannelName": channel_name,
                },
            }
        }
        try:
            return self.eio_client.rest_call(
                "POST",
                end_point="playlist-management/export",
                payload=payload,
            )
        except Exception as exception:
            logging.info(f"Unable to do export {str(exception)}")
            raise exception

    @staticmethod
    def wait_for_playlist_import(
        eio_client, channel_id, ws_client, event_size, max_wait_time
    ):
        """
        Waits until the playlist is imported for a specific channel within a specified time limit.

        Args:
            eio_client: An instance of the EIOClient.
            channel_id (str): The ID of the channel for which playlist import is awaited.
            ws_client: The WebSocket client for communication.
            event_size: The number of events in the playlist.
            max_wait_time: The maximum time to wait for playlist import in seconds.
        """
        # Constants
        sleep_duration = 8

        start_time = time.time()
        while True:
            time.sleep(sleep_duration)
            elapsed_time = time.time() - start_time

            get_playlist = eio_client.channel_service.get_playlist(
                channel_id, event_size, ws_client
            )

            # Check if the total items in the playlist are not zero or if the maximum time limit is reached
            if (
                get_playlist["result"]["result"]["totalItems"] != 0
                or elapsed_time > max_wait_time
            ):
                # Log information about the imported events
                logging.error(
                    f"Imported total events including bookmarks blocks and day header: {get_playlist['result']['result']['totalItems']}"
                )
                break

            # Check if the playlist is not imported within the time limit
            elif (
                elapsed_time > max_wait_time
                and get_playlist["result"]["result"]["totalItems"] == 0
            ):
                # Loggers for maximum time limit reached
                logging.warning(
                    "Maximum time limit reached while waiting for playlist import."
                )

                # Fail the test with an appropriate message
                pytest.fail("Playlist import failed within the time limit.")
