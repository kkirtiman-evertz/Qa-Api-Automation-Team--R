"""
Module Docstring: Utilities for Testing Event Row Alerts in Playlists.
"""

import logging
import xml

import pytest
from defusedxml.minidom import parseString

from tests.tests_channel_service.config.event_row_alert_config import (
    CLIENT_ID,
    EVENT_SIZE,
    FILE_ALERTS_PLAYLIST,
    LIVE_ALERTS_PLAYLIST,
    MAX_WAIT_TIME,
    PLAYOUT_ALERTS_PLAYLIST,
    SCHEDULE_FILE_PATH,
    SCTE_ALERTS_PLAYLIST,
    TestParameters,
)
from tests.tests_channel_service.config.event_row_alert_parameters import (
    ParameterSetsFileAlerts,
    ParameterSetsLiveAlerts,
    ParameterSetsPlayoutAlerts,
    ParameterSetsScteAlerts,
)
from utils.aws_helper import AwsHelper
from utils.eio.clients.httpclient import EIOHttpClient


class TestRowAlert:
    """
    Test class for handling event row alerts in a playlist.
    """

    @staticmethod
    def xml_events(file_path, schedule_file_name):
        """
        Retrieves the total number of events in a given XML file.

        Args:
            file_path (str): The path to the directory containing the XML file.
            schedule_file_name (str): The name of the XML file.

        Returns:
            int: The total number of events in the XML file.

        Raises:
            FileNotFoundError: If the specified XML file is not found.
            xml.parsers.expat.ExpatError: If there is an error parsing the XML file.
        """

        with open(f"{file_path}{schedule_file_name}", "r", encoding="utf-8") as file:
            data = file.read()
            dom = parseString(data)
            playlist_items = dom.getElementsByTagName("PlaylistItem")
            bookmark_block = dom.getElementsByTagName("Bookmark")
            return len(playlist_items) + len(bookmark_block)

    @staticmethod
    def clear_playlist(eio_client: EIOHttpClient, channel_id, ws_client):
        """
        Clears the playlist for a specific channel and verifies the playlist is empty.

        Args:
            eio_client (EIOHttpClient): Remote server to establish an HTTP connection.
            channel_id (str): The ID of the channel for which the playlist should be cleared.
            ws_client: The WebSocket client for communication.

        """

        eio_client.channel_service.clear_playlist(channel_id, ws_client)
        get_playlist_before = eio_client.channel_service.get_playlist(
            channel_id, EVENT_SIZE, ws_client
        )
        assert (
            get_playlist_before["result"]["result"]["totalItems"] == 0
        ), "Error: Total items in playlist are not as expected (should be 0)."
        logging.info("Playlist cleared Successfully")

    def verify_playlist_count(
        self, eio_client: EIOHttpClient, current_environment, ws_client, file_name
    ):
        """
        Verifies the playlist count in a channel against the expected count from an XML file.

        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient for making HTTP requests.
            current_environment: The current environment details, including the channel ID.
            ws_client: The WebSocket client used for communication.
            file_name (str): The name of the XML file containing the expected playlist events.

        Returns:
            list: A filtered list of events from the actual playlist in the channel.
        """
        # verify playlist status
        get_playlist_after = eio_client.channel_service.get_playlist(
            current_environment["channel_id"], EVENT_SIZE, ws_client
        )
        filtered_events = [
            event
            for event in get_playlist_after["result"]["result"]["items"]
            if "dayheader" not in event["id"]
        ]
        assert len(filtered_events) == self.xml_events(SCHEDULE_FILE_PATH, file_name), (
            f"Number of events mismatch. Expected: {len(filtered_events)}, "
            f"Actual: {self.xml_events(SCHEDULE_FILE_PATH, file_name)}"
        )
        logging.info("Verified playlist in channel with actual events in xml")
        return filtered_events

    @staticmethod
    def filter_alerts(filtered_events, test_params):
        """
        Filters and retrieves a specific alert from the list of events.

        Args:
            filtered_events (list): A list of events filtered from the actual playlist.
            test_params (TestParameters): An instance of TestParameters containing
                                          parameters for the alert verification.
        Returns:
            dict: Information about the filtered alert.
        """
        alert_in_response = next(
            (
                alert_info
                for alert_info in filtered_events[int(test_params.test_number) - 1][
                    "alerts"
                ]
                if alert_info["code"] == test_params.alert_code
            ),
            None,
        )
        if alert_in_response is None:
            raise ValueError(
                f"Alert with code {test_params.alert_code} not found in the event list."
            )
        return alert_in_response

    @staticmethod
    def verify_alert_details(alert, test_params):
        """
        Verifies the details of an alert against the expected parameters.

        Args:
            alert (dict): Information about the alert to be verified.
            test_params (TestParameters): An instance of TestParameters containing
                                            parameters for the alert verification.
        """
        assert alert["code"] == test_params.alert_code, (
            f"Error: Alert code mismatch. Expected: {test_params.alert_code}, "
            f"Actual: {alert['code']}"
        )
        logging.info(f"Verified : Alert - {alert['code']}")
        assert alert["severity"] == test_params.severity, (
            f"Error: Severity mismatch. Expected: {test_params.severity}, "
            f"Actual: {alert['severity']}"
        )
        logging.info(f"Verified : Severity - {alert['severity']}")
        assert alert["eventTypes"] == test_params.event_types, (
            f"Error: EventTypes mismatch. Expected: {test_params.event_types}, "
            f"Actual: {alert['eventTypes']}"
        )
        logging.info(f"Verified : EventTypes - {alert['eventTypes']}")
        assert alert["streamName"] == test_params.streamName, (
            f"Error: StreamName mismatch. Expected: {test_params.streamName}, "
            f"Actual: {alert['streamName']}"
        )
        logging.info(f"Verified : streamName - {alert['streamName']}")
        assert set(alert["data"].keys()) == test_params.data, (
            f"Error: data attributes(keys) mismatch. Expected: {test_params.data}, "
            f"Actual: {set(alert['data'].keys())}"
        )
        logging.info(f"Verified : data attributes - {set(alert['data'].keys())}")

    @pytest.mark.parametrize("test_params", ParameterSetsFileAlerts)
    def test_event_row_file_alerts(
        self,
        eio_client: EIOHttpClient,
        aws_helper_eio_dev,
        current_environment,
        test_params: TestParameters,
    ):
        """
        Test for the handling of event row file alerts in a playlist.

        Args:
            eio_client (EIOHttpClient): HTTP client for requests.
            current_environment: The current test environment.
            test_params (TestParameters): Test-specific parameters.
        """
        ws_client = eio_client.get_ws_client(CLIENT_ID)
        try:

            if test_params.test_number == 1:
                # Clear playlist for very 1st iteration
                self.clear_playlist(
                    eio_client, current_environment["channel_id"], ws_client
                )

                # Upload playlist and wait for import
                AwsHelper.upload_with_presigned_url(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    FILE_ALERTS_PLAYLIST,
                    SCHEDULE_FILE_PATH,
                    aws_helper_eio_dev,
                )
                eio_client.playlist_management.wait_for_playlist_import(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    EVENT_SIZE,
                    MAX_WAIT_TIME,
                )
            # validates the number of playlists in an actual channel against the count
            # specified in an XML file
            filtered_events = self.verify_playlist_count(
                eio_client, current_environment, ws_client, FILE_ALERTS_PLAYLIST
            )
            alert = self.filter_alerts(filtered_events, test_params)
            self.verify_alert_details(alert, test_params)
        except KeyError as key_error:
            logging.error(f"KeyError during test execution: {str(key_error)}")
            pytest.fail(f"Test failed due to a KeyError: {str(key_error)}")
        except IndexError as index_error:
            logging.error(f"IndexError during test execution: {str(index_error)}")
            pytest.fail(f"Test failed due to an IndexError: {str(index_error)}")
        except ValueError as value_error:
            logging.error(f"ValueError during test execution: {str(value_error)}")
            pytest.fail(f"Test failed due to a ValueError: {str(value_error)}")
        except FileNotFoundError as file_not_found_error:
            logging.error(
                f"FileNotFoundError during test execution: {str(file_not_found_error)}"
            )
            pytest.fail(
                f"Test failed due to a FileNotFoundError: {str(file_not_found_error)}"
            )
        except xml.parsers.expat.ExpatError as expat_error:
            logging.error(f"ExpatError during test execution: {str(expat_error)}")
            pytest.fail(f"Test failed due to an ExpatError: {str(expat_error)}")
        except Exception as exception:  # pylint: disable=broad-except
            logging.error(
                f"Unexpected exception during test execution: {str(exception)}"
            )
            pytest.fail(f"Test failed due to an unexpected exception: {str(exception)}")

    @pytest.mark.parametrize("test_params", ParameterSetsLiveAlerts)
    def test_event_row_live_alerts(
        self,
        eio_client: EIOHttpClient,
        aws_helper_eio_dev,
        current_environment,
        test_params: TestParameters,
    ):
        """
        Test for the handling of event row live alerts in a playlist.

        Args:
            eio_client (EIOHttpClient): HTTP client for requests.
            current_environment: The current test environment.
            test_params (TestParameters): Test-specific parameters.
        """
        ws_client = eio_client.get_ws_client(CLIENT_ID)
        try:
            if test_params.test_number == 1:
                # Clear playlist for very 1st iteration
                self.clear_playlist(
                    eio_client, current_environment["channel_id"], ws_client
                )

                # Upload playlist and wait for import
                AwsHelper.upload_with_presigned_url(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    LIVE_ALERTS_PLAYLIST,
                    SCHEDULE_FILE_PATH,
                    aws_helper_eio_dev,
                )
                eio_client.playlist_management.wait_for_playlist_import(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    EVENT_SIZE,
                    MAX_WAIT_TIME,
                )

            # validates the number of playlists in an actual channel against the
            # count specified in an XML file
            filtered_events = self.verify_playlist_count(
                eio_client, current_environment, ws_client, LIVE_ALERTS_PLAYLIST
            )
            alert = self.filter_alerts(filtered_events, test_params)
            self.verify_alert_details(alert, test_params)
        except KeyError as key_error:
            logging.error(f"KeyError during test execution: {str(key_error)}")
            pytest.fail(f"Test failed due to a KeyError: {str(key_error)}")
        except IndexError as index_error:
            logging.error(f"IndexError during test execution: {str(index_error)}")
            pytest.fail(f"Test failed due to an IndexError: {str(index_error)}")
        except ValueError as value_error:
            logging.error(f"ValueError during test execution: {str(value_error)}")
            pytest.fail(f"Test failed due to a ValueError: {str(value_error)}")
        except FileNotFoundError as file_not_found_error:
            logging.error(
                f"FileNotFoundError during test execution: {str(file_not_found_error)}"
            )
            pytest.fail(
                f"Test failed due to a FileNotFoundError: {str(file_not_found_error)}"
            )
        except xml.parsers.expat.ExpatError as expat_error:
            logging.error(f"ExpatError during test execution: {str(expat_error)}")
            pytest.fail(f"Test failed due to an ExpatError: {str(expat_error)}")
        except Exception as exception:  # pylint: disable=broad-except
            logging.error(
                f"Unexpected exception during test execution: {str(exception)}"
            )
            pytest.fail(f"Test failed due to an unexpected exception: {str(exception)}")

    @pytest.mark.parametrize("test_params", ParameterSetsPlayoutAlerts)
    @pytest.mark.skip(
        reason="Skipping this test as per we are not able to find that alert in our tenant"
    )
    def test_event_row_playout_alerts(
        self,
        eio_client: EIOHttpClient,
        aws_helper_eio_dev,
        current_environment,
        test_params: TestParameters,
    ):
        """
        Test for the handling of event row schedule alerts in a playlist.

        Args:
            eio_client (EIOHttpClient): HTTP client for requests.
            current_environment: The current test environment.
            test_params (TestParameters): Test-specific parameters.
        """
        ws_client = eio_client.get_ws_client(CLIENT_ID)
        try:
            if test_params.test_number == 1:
                # Clear playlist for very 1st iteration
                self.clear_playlist(
                    eio_client, current_environment["channel_id"], ws_client
                )

                # Upload playlist and wait for import
                AwsHelper.upload_with_presigned_url(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    PLAYOUT_ALERTS_PLAYLIST,
                    SCHEDULE_FILE_PATH,
                    aws_helper_eio_dev,
                )
                eio_client.playlist_management.wait_for_playlist_import(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    EVENT_SIZE,
                    MAX_WAIT_TIME,
                )

            # validates the number of playlists in an actual channel against the
            # count specified in an XML file
            filtered_events = self.verify_playlist_count(
                eio_client, current_environment, ws_client, PLAYOUT_ALERTS_PLAYLIST
            )
            alert = self.filter_alerts(filtered_events, test_params)
            self.verify_alert_details(alert, test_params)
        except KeyError as key_error:
            logging.error(f"KeyError during test execution: {str(key_error)}")
            pytest.fail(f"Test failed due to a KeyError: {str(key_error)}")
        except IndexError as index_error:
            logging.error(f"IndexError during test execution: {str(index_error)}")
            pytest.fail(f"Test failed due to an IndexError: {str(index_error)}")
        except ValueError as value_error:
            logging.error(f"ValueError during test execution: {str(value_error)}")
            pytest.fail(f"Test failed due to a ValueError: {str(value_error)}")
        except FileNotFoundError as file_not_found_error:
            logging.error(
                f"FileNotFoundError during test execution: {str(file_not_found_error)}"
            )
            pytest.fail(
                f"Test failed due to a FileNotFoundError: {str(file_not_found_error)}"
            )
        except xml.parsers.expat.ExpatError as expat_error:
            logging.error(f"ExpatError during test execution: {str(expat_error)}")
            pytest.fail(f"Test failed due to an ExpatError: {str(expat_error)}")
        except Exception as exception:  # pylint: disable=broad-except
            logging.error(
                f"Unexpected exception during test execution: {str(exception)}"
            )
            pytest.fail(f"Test failed due to an unexpected exception: {str(exception)}")

    @pytest.mark.parametrize("test_params", ParameterSetsScteAlerts)
    def test_event_row_scte_alerts(
        self,
        eio_client: EIOHttpClient,
        aws_helper_eio_dev,
        current_environment,
        test_params: TestParameters,
    ):
        """
        Test for the handling of event row scte alerts in a playlist.

        Args:
            eio_client (EIOHttpClient): HTTP client for requests.
            current_environment: The current test environment.
            test_params (TestParameters): Test-specific parameters.
        """
        ws_client = eio_client.get_ws_client(CLIENT_ID)
        try:
            if test_params.test_number == 1:
                # Clear playlist for very 1st iteration
                self.clear_playlist(
                    eio_client, current_environment["channel_id"], ws_client
                )

                # Upload playlist and wait for import
                AwsHelper.upload_with_presigned_url(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    SCTE_ALERTS_PLAYLIST,
                    SCHEDULE_FILE_PATH,
                    aws_helper_eio_dev,
                )
                eio_client.playlist_management.wait_for_playlist_import(
                    eio_client,
                    current_environment["channel_id"],
                    ws_client,
                    EVENT_SIZE,
                    MAX_WAIT_TIME,
                )

            # validates the number of playlists in an actual channel against the
            # count specified in an XML file
            filtered_events = self.verify_playlist_count(
                eio_client, current_environment, ws_client, SCTE_ALERTS_PLAYLIST
            )
            alert = self.filter_alerts(filtered_events, test_params)
            self.verify_alert_details(alert, test_params)
        except KeyError as key_error:
            logging.error(f"KeyError during test execution: {str(key_error)}")
            pytest.fail(f"Test failed due to a KeyError: {str(key_error)}")
        except IndexError as index_error:
            logging.error(f"IndexError during test execution: {str(index_error)}")
            pytest.fail(f"Test failed due to an IndexError: {str(index_error)}")
        except ValueError as value_error:
            logging.error(f"ValueError during test execution: {str(value_error)}")
            pytest.fail(f"Test failed due to a ValueError: {str(value_error)}")
        except FileNotFoundError as file_not_found_error:
            logging.error(
                f"FileNotFoundError during test execution: {str(file_not_found_error)}"
            )
            pytest.fail(
                f"Test failed due to a FileNotFoundError: {str(file_not_found_error)}"
            )
        except xml.parsers.expat.ExpatError as expat_error:
            logging.error(f"ExpatError during test execution: {str(expat_error)}")
            pytest.fail(f"Test failed due to an ExpatError: {str(expat_error)}")
        except Exception as exception:  # pylint: disable=broad-except
            logging.error(
                f"Unexpected exception during test execution: {str(exception)}"
            )
            pytest.fail(f"Test failed due to an unexpected exception: {str(exception)}")
