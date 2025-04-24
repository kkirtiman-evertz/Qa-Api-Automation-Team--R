"""Importing necessary modules for logging, time,pytest,requests and generating UUIDs."""

import json
import logging
import logging.config
import threading
import time
import uuid

import pytest

from tests.tests_playlist_management.config.playlist_import_notification_config import (
    DURATION_LESS_THAN_ZERO_XML,
    EMPTY_SCHEDULE_FILE_PXF,
    EMPTY_SCHEDULE_FILE_XML,
    FIXED_ITEM_IN_PAST_SCHEDULE_PXF,
    INVALID_BOOKMARK_XML,
    INVALID_TEST_CHANNEL_ID,
    NEGATIVE_TIMECODE_OFFSET_XML,
    NESTED_STRUCTURAL_BLOCK_XML,
    NO_STRUCTURAL_BLOCK_CONFIG_XML,
    PLAYLIST_CONSTRAIN_VIOLATION_XML,
    SCHEDULE_FILE_NAME_PXF,
    SCHEDULE_FILE_NAME_XML,
    SCHEDULE_FILE_PATH,
    START_DATE_NULL_XML,
    TEMPLATE_EXECUTION_FAILED_PXF,
)
from utils.aws_helper import AwsHelper

playlist_events = []


class TestPlaylistImportNotification:
    """These functions are used to check for different scenarios for import notifications"""

    notification_types = ""
    notification_status_dict = {
        "failed": ["upload-pending", "initiating", "validating", "failed"],
        "successful": [
            "upload-pending",
            "initiating",
            "validating",
            "processing",
            "successful",
        ],
        "validation-failed": [
            "upload-pending",
            "initiating",
            "validating",
            "validation-failed",
        ],
        "channel-not-found": ["upload-pending", "initiating", "channel-not-found"],
    }

    @staticmethod
    def perform_notification_setup(ws_client, eio_client, channel_id, client_id):
        """
        Clear previous registration & create new & verify
        Args:
            ws_client (WebSocket): The WebSocket connection to monitor and interact with.
            client_id: Websocket client id
            eio_client: EIO client to make HTTP connection
            channel_id: I'd for the channel where the playlist belongs
        """
        # clear previous registrations
        deregister_response = eio_client.playlist_management.handle_request(
            ws_client, client_id, channel_id, request="deregister"
        )
        # register for notification
        assert deregister_response["result"]["method"] == "deregister"
        register_response = eio_client.playlist_management.handle_request(
            ws_client, client_id, channel_id, request="register"
        )
        # Check if the "method" matches "register"
        assert register_response["result"]["method"] == "register"
        assert register_response["result"]["id"] == client_id
        assert register_response["result"]["result"]["success"]

    @staticmethod
    def subscriber(web_socket):
        """
        Continuously receives and processes WebSocket messages from the provided
        WebSocket connection.
        This function listens to WebSocket events and performs the following actions:
        1. Sends a periodic 'ping' message to the WebSocket connection to maintain the connection.
        2. Logs received events, excluding 'ping' events.
        3. Stops execution after 5 minutes of continuous operation.
        Args:
           web_socket (WebSocket): The WebSocket connection to monitor and interact with.
        Note:
           The function can be stopped externally by setting the `do_run`
            attribute of the thread to `False`.
        """
        current_thread = threading.current_thread()
        start_time = time.time()  # Record the start time
        while getattr(current_thread, "do_run", True):
            captured_event = web_socket.ws_receive(5)
            json_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "route": "heartbeat",
                "method": "ping",
            }
            web_socket.WS.send(json.dumps(json_request))
            if (
                "result" in captured_event
                and "method" in captured_event["result"]
                and captured_event["result"]["method"] == "reportStatus"
            ):
                playlist_events.append(captured_event)
                logging.info(captured_event)
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time >= 80:
                current_thread.do_run = False  # Set the flag to exit the loop
        logging.info("Disabled thread ID %s", current_thread.ident)

    def get_notification_statuses(self):
        """
        Get a dictionary of notification types and their corresponding expected statuses.
        This static method defines a dictionary where each notification type is associated
         with a list of expected statuses. It's used to determine the expected
        workflow statuses for various notification types.
        Returns:
        dict: A dictionary where keys are notification types,
        and values are lists of expected statuses
        for each type.
        """

        return self.notification_status_dict.get(
            self.notification_types,
            [
                "upload-pending",
                "initiating",
                "validating",
                "processing",
                "failed",
            ],
        )

    @staticmethod
    def disable_notification_subscriber(playlist_subscriber):
        """
        Safely disable a notification subscriber thread and wait for it to finish.
        This static method allows you to stop a notification subscriber
         thread by setting the do_run attribute to False,
        and it ensures that the thread is not active before returning.
        Args:
            playlist_subscriber (Thread): The notification subscriber thread to disable.
        """
        playlist_subscriber.do_run = False
        time.sleep(5)
        assert playlist_subscriber.is_alive() is False
        # Wait for the thread to finish
        playlist_subscriber.join()

    def awaiting_websocket_notifications(self):
        """waiting for websocket notification max limit = 180 sec"""
        receive_ws_notification = True
        notification_start_time = time.time()  # Record the start time
        while receive_ws_notification:
            expected_statuses = self.get_notification_statuses()
            if len(playlist_events) == len(expected_statuses):
                receive_ws_notification = False
            else:
                notification_current_time = time.time()
                notification_elapsed_time = (
                    notification_current_time - notification_start_time
                )
                if notification_elapsed_time >= 120:  # 2 minutes
                    receive_ws_notification = False  # Set the flag to exit the loop

    def enable_notification_subscriber(self, ws_client):
        """
        Enable a notification subscriber thread and start listening for WebSocket events.
        This method creates a new notification subscriber thread using the `subscriber` method
        and starts it to continuously receive and process WebSocket events.
        After starting the thread, it provides a brief delay to allow the subscriber to
        initialize before returning the thread object.
        Args:
           ws_client: The WebSocket client used for communication.
        Returns:
           threading.Thread: A thread object representing the notification subscriber.
        """
        playlist_subscriber = threading.Thread(
            target=self.subscriber, args=(ws_client,)
        )
        playlist_subscriber.start()
        time.sleep(5)
        return playlist_subscriber

    ParameterSets = [
        pytest.param(
            SCHEDULE_FILE_NAME_PXF, "successful", id="notification_success_pxf"
        ),
        pytest.param(
            SCHEDULE_FILE_NAME_XML, "successful", id="notification_success_xml"
        ),
        pytest.param(
            FIXED_ITEM_IN_PAST_SCHEDULE_PXF,
            "fixed-item-failed",
            id="notification_fixed_item_in_past_pxf",
        ),
        pytest.param(
            EMPTY_SCHEDULE_FILE_PXF,
            "validation-failed",
            id="notification_validation_failure_pxf",
        ),
        pytest.param(
            EMPTY_SCHEDULE_FILE_XML,
            "validation-failed",
            id="notification_validation_failure_xml",
        ),
        pytest.param(
            SCHEDULE_FILE_NAME_PXF,
            "channel-not-found",
            id="notification_channel_not_found_pxf",
        ),
        pytest.param(
            SCHEDULE_FILE_NAME_XML,
            "channel-not-found",
            id="notification_channel_not_found_xml",
        ),
        pytest.param(
            START_DATE_NULL_XML,
            "start-date-time-null",
            id="notification_start_date_null_xml",
        ),
        pytest.param(
            INVALID_BOOKMARK_XML,
            "invalid-bookmark-position",
            id="notification_invalid_bookmark_xml",
        ),
        pytest.param(
            NO_STRUCTURAL_BLOCK_CONFIG_XML,
            "no-structural-config",
            id="notification_no_structural_block_config_xml",
        ),
        pytest.param(
            TEMPLATE_EXECUTION_FAILED_PXF,
            "template-execution-failed",
            id="notification_template_execution_failed_pxf",
        ),
        pytest.param(
            DURATION_LESS_THAN_ZERO_XML,
            "successful",
            id="successful_notification_for_duration_less_than_zero_xml",
        ),
        pytest.param(
            NEGATIVE_TIMECODE_OFFSET_XML,
            "negative-timecode-offset-not-supported",
            id="notification_negative_timecode_offset_xml",
        ),
        pytest.param(
            NESTED_STRUCTURAL_BLOCK_XML,
            "nested-structural-block-exist",
            id="notification_nested-structural-block-exist_xml",
        ),
        pytest.param(
            PLAYLIST_CONSTRAIN_VIOLATION_XML,
            "playlist-constraint-violation",
            id="notification_playlist_constrain_violation_xml",
        ),
    ]

    @pytest.mark.parametrize("file_name, notification_type", ParameterSets)
    def test_notification(
        self,
        eio_client,
        current_environment,
        notification_type,
        file_name,
    ):
        """Checking with different scenarios"""
        client_id = str(uuid.uuid4())
        self.notification_types = notification_type
        channel_id = current_environment["channel_id"]
        enable_socket = None
        if notification_type == "channel-not-found":
            channel_id = INVALID_TEST_CHANNEL_ID
        playlist_events.clear()
        ws_client = eio_client.get_ws_client(client_id)

        # deregister & register operation for notification
        self.perform_notification_setup(ws_client, eio_client, channel_id, client_id)

        # Clear playlist for the channel
        if notification_type == "successful":
            eio_client.channel_service.clear_playlist(channel_id, ws_client)

        try:
            # Enable the Subscriber to receive notifications
            enable_socket = self.enable_notification_subscriber(ws_client)
            # Generates S3 presigned URL to upload object into s3 Bucket
            # Upload playlist
            AwsHelper.upload_with_presigned_url(
                eio_client,
                channel_id,
                ws_client,
                file_name,
                SCHEDULE_FILE_PATH,
            )

            self.awaiting_websocket_notifications()
            # Verify the notifications
            expected_statuses = self.get_notification_statuses()
            assert len(playlist_events) == len(expected_statuses)

            for notification_index, expected_status in enumerate(expected_statuses):
                notification = playlist_events[notification_index]
                assert (
                    notification["result"]["result"]["reportStatus"] == expected_status
                )
                logging.info("Notification Trigger: %s", expected_status)
        finally:
            # disable subscriber
            self.disable_notification_subscriber(enable_socket)
            eio_client.close()
