"""
Module Description: This module provides functionality for export of playlists.
It contains configurations and dependencies for testing export functionality.
"""

import logging
import time

import pytest
from defusedxml.ElementTree import fromstring

from tests.tests_playlist_management.config.playlist_export_config import (
    ASSET_ID,
    CLIENT_ID,
    EXPORT_BUCKET,
    FILE_STORE_IDS,
    START_MODE,
    TEMPLATE_NAME,
)
from utils.eio.clients.httpclient import EIOHttpClient


class TestPlaylistExport:
    """
    TestPlaylistExport class for testing the playlist export functionality.

    Methods:
    - file_store_id(tenant_id): Returns the file store id for the given tenant_id.
    - test_playlist_export(eio_client, current_environment, aws_helper):
    Tests the playlist export functionality.

    Attributes:
    None
    """

    @staticmethod
    def insert_event(eio_client, current_environment, ws_client):
        """
        Insert sequence & verify

        Args:
            eio_client (EIOHttpClient): An instance of the EIOHttpClient.
            current_environment: The current environment configuration.
            ws_client: websocket client

        Returns:
            None
        """
        try:
            inserted_sequence = eio_client.channel_service.insert_sequence(
                current_environment["channel_id"],
                START_MODE,
                TEMPLATE_NAME,
                ASSET_ID,
                ws_client,
            )
            capture_sequence_id = inserted_sequence["result"]["result"]
            assert "sequence$" in capture_sequence_id
        except KeyError as key_error:
            logging.info("channel Service has encountered an Internal Error")
            logging.info(
                f"KeyError: {str(key_error)}. Check if the dictionary structure has changed"
            )
            pytest.fail("Test failed due to KeyError")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An error occurred: {str(exception)}")

    def export_playlist(self, eio_client, current_environment):
        """
        playlist export functionality.

        Args:
            eio_client (EIOHttpClient): An instance of the EIOHttpClient.
            current_environment: The current environment configuration.

        Returns:
            None
        """

        try:
            get_channel_config = eio_client.channel_management.get_channel_by_id(
                current_environment["channel_id"]
            )
            channel_name = get_channel_config["output"]["data"]["attributes"][
                "metadata"
            ]["name"]
            export_playlist = eio_client.playlist_management.playlist_export(
                current_environment["channel_id"],
                FILE_STORE_IDS.get(current_environment["tenant"], "Key not found"),
                channel_name,
            )
            assert (
                export_playlist["status"] == 202
            ), f"Unable to export playlist {export_playlist}"
            logging.info("Playlist exported successfully with 1 event")
            time.sleep(3)
        except KeyError as key_error:
            logging.error(
                f"KeyError: {key_error} Check if the dictionary structure has changed"
            )
            pytest.fail("Test failed due to KeyError")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An error occurred: {str(exception)}")

    def test_playlist_export(
        self,
        eio_client: EIOHttpClient,
        current_environment,
        aws_helper_mock_cust_access,
    ):
        """
        Test the playlist export functionality.

        Args:
            eio_client (EIOHttpClient): An instance of the EIOHttpClient.
            current_environment: The current environment configuration.
            aws_helper_mock_cust_access: An instance of the AWS helper
             for mock customer access profile

        Returns:
            None
        """
        # Pre-requisite
        ws_client = eio_client.get_ws_client(CLIENT_ID)

        # clear playlist
        eio_client.channel_service.clear_playlist(
            current_environment["channel_id"], ws_client
        )

        # Insert sequence & export playlist
        self.insert_event(eio_client, current_environment, ws_client)
        self.export_playlist(eio_client, current_environment)

        # Verify xml file added in s3 bucket
        try:
            s3_objects = aws_helper_mock_cust_access.list_objects_in_s3_bucket(
                EXPORT_BUCKET + current_environment["tenant"],
                last_modified_object=True,
            )

            # Find the object with the latest LastModified timestamp
            last_modified_content = aws_helper_mock_cust_access.get_object_from_s3(
                EXPORT_BUCKET + current_environment["tenant"], s3_objects["Key"]
            )

            # Parse the XML content & verify 1 event is added in xml file
            root = fromstring(last_modified_content)
            # Count the occurrences of PlaylistItem elements
            playlist_item_count = len(root.findall(".//PlaylistItem"))
            assert (
                playlist_item_count == 1
            ), f"Playlist Item count does not matches with expected {playlist_item_count}"
            logging.info("Exported xml file with 1 event validated form s3 bucket")
            # Delete the file after verification
            aws_helper_mock_cust_access.delete_object_in_s3_bucket(
                EXPORT_BUCKET + current_environment["tenant"], s3_objects["Key"]
            )
            logging.info("Uploaded file deleted from S3 bucket after verification")
        except Exception as exception:  # pylint: disable=broad-except
            logging.error(f"An error occurred: {str(exception)}")
