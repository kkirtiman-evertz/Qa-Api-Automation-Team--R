"""
Module Description: This module provides functionality for external import of playlists.
It contains configurations and dependencies for testing external import functionality.
"""

import logging
import logging.config
import time

import pytest
from defusedxml import ElementTree as DefusedETree
from defusedxml.minidom import parseString

from tests.tests_playlist_management.config.playlist_external_import_config import (
    BUCKET_NAME,
    CLIENT_ID,
    EVENT_SIZE,
    FILE_NAME,
    FILE_PATH,
)
from utils.eio.clients.httpclient import EIOHttpClient


class TestPlaylistExternalImport:
    """
    Test class for external import functionality.
    Methods:
        - update_channel_name_in_xml(xml_file_path, new_channel_name)
        - test_external_import(eio_client, current_environment, aws_helper)
    """

    @staticmethod
    def update_channel_name_in_xml(xml_file_path, new_channel_name):
        """
        Update the ChannelName element in an XML file with the provided new channel name.

        Args:
            xml_file_path (str): The path to the XML file.
            new_channel_name (str): The new channel name to set in the XML.

        Returns:
            None
        """

        # Parse the XML file with lxml
        try:
            tree = DefusedETree.parse(xml_file_path)

            # Find the ChannelName element and update its text
            channel_name_element = tree.find(".//Playlist/ChannelName")
            if channel_name_element is not None:
                channel_name_element.text = new_channel_name
            else:
                pytest.fail("ChannelName element not found.")

            # Save the updated XML back to the file
            tree.write(xml_file_path, encoding="utf-8", xml_declaration=True)

            logging.info(f"Updated XML in {xml_file_path} with the new channel name")
        except DefusedETree.ParseError as parse:
            pytest.fail(f"Error parsing XML file: {str(parse)}")
        except ValueError as value_err:
            pytest.fail(f"ValueError: {str(value_err)}")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An unexpected error occurred: {str(exception)}")

    # pylint: disable=too-many-locals
    def test_external_import(
        self,
        eio_client: EIOHttpClient,
        current_environment,
        aws_helper_mock_cust_access,
    ):
        """
        Test the external import functionality.

        Args:
            eio_client (EIOHttpClient): An instance of the EIOHttpClient.
            current_environment: The current environment configuration.
            aws_helper_mock_cust_access: An instance of the AWS helper
             for mock customer access profile

        Returns:
            None
        """
        # Total number of events in.pxf file
        with open(FILE_PATH, "r", encoding="utf-8") as file:
            data = file.read()
            dom = parseString(data)
            total_events_in_xml = len(dom.getElementsByTagName("PlaylistItem"))

        channel_id = current_environment["channel_id"]
        tenant_id = current_environment["tenant"]
        ws_client = eio_client.get_ws_client(CLIENT_ID)

        try:
            get_channel_config = eio_client.channel_management.get_channel_by_id(
                channel_id
            )
            channel_technical_name = get_channel_config["output"]["data"]["attributes"][
                "metadata"
            ]["name"]
            # dynamically updating xml file channel name to avoid problems
            # in various tenants due to xml file channel name
            self.update_channel_name_in_xml(FILE_PATH, channel_technical_name)

            # clear playlist & verify
            eio_client.channel_service.clear_playlist(channel_id, ws_client)
            output_get_playlist = eio_client.channel_service.get_playlist(
                channel_id, EVENT_SIZE, ws_client
            )
            assert output_get_playlist["result"]["result"]["items"] == []

            # upload playlist to s3 bucket
            aws_helper_mock_cust_access.import_playlist_on_s3(
                BUCKET_NAME + tenant_id, FILE_NAME, FILE_PATH
            )

            # verify playlist is imported
            # TODO: Ashish - Minimize this timeout once EIO-12327 bug ticket is fixed (fixme) pylint: disable=W0511
            time.sleep(40)
            get_playlist = eio_client.channel_service.get_playlist(
                channel_id, EVENT_SIZE, ws_client
            )
            assert (
                len(get_playlist["result"]["result"]["items"])
                == total_events_in_xml + 1
            )
            # +1 for added day-header in items
            logging.info(
                "External import Successful & Verified total event added to playlist"
            )
        except KeyError as key_error:
            pytest.fail(
                f"KeyError: {key_error}. Check if the dictionary structure has changed"
            )
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An error occurred: {str(exception)}")
