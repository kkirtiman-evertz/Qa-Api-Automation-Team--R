from utils.aws_helper import AwsHelper
from utils.eio.services import Service

# pylint: disable=too-many-lines, pylint: disable=too-many-locals
"""Importing necessary modules for SCTE test."""

import json
import logging
import threading
import time
import uuid

from websocket import WebSocketTimeoutException

from tests.tests_channel_service.config.scte_taker_config import (
    DESTINATION_NAME,
    EVENT_SIZE,
    FILE_DEFINITION_PROFILE,
    ID,
    IP,
    MAX_WAIT_TIME,
    PORT,
    PROTOCOL,
    SCHEDULE_FILE_PATH,
    SOURCE_NAME,
    SOURCE_RECEIVER_NAME,
    START_ID,
    STOP_ID,
)


class ScteTaker(Service):
    playlist_event = []
    state = []
    subscriber_flag = False

    def __init__(self, eio_client):
        super().__init__(eio_client)

    def subscriber(self, web_socket):
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
        try:
            while getattr(current_thread, "do_run", True):
                event = web_socket.ws_receive(5)
                heartbeat_request = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "route": "heartbeat",
                    "method": "ping",
                }
                web_socket.WS.send(json.dumps(heartbeat_request))

                if (
                    "result" in event
                    and "method" in event["result"]
                    and event["result"]["method"] == "incomingSCTETrigger"
                ):
                    self.playlist_event.append(event)
                    logging.info(event)
                if (
                    "result" in event
                    and "result" in event["result"]
                    and "notification" in event["result"]["result"]
                    and "playlistStatus" in event["result"]["result"]["notification"]
                    and "holdState"
                    in event["result"]["result"]["notification"]["playlistStatus"]
                    and event["result"]["result"]["notification"]["playlistStatus"][
                        "holdState"
                    ]
                    == "holding"
                ):
                    self.state.append("HoldState:Holding Found")
                    logging.info(event)

                if (
                    "SCTE Trigger Found" in self.state
                    or "HoldState:Holding Found" in self.state
                ):
                    break

                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > 30:
                    logging.info(
                        "Disabled Subscriber as max time limit reached to receive SCTE trigger"
                    )
                    self.subscriber_flag = False
                    break
            logging.info("Disabled thread ID %s", current_thread.ident)
        except WebSocketTimeoutException as exception:
            logging.error(f"WebSocket read operation timed out: {exception}")

    def enable_notification_subscriber(self, ws_client):
        """
        Enable a notification subscriber thread and start listening
        for WebSocket events.
        This method creates a new notification subscriber thread
        using the `subscriber` method and starts it to
        continuously receive and process WebSocket events.
        After starting the thread, it provides a brief delay
        to allow the subscriber to initialize before returning the thread object.
        Args:
           ws_client: The WebSocket client used for communication.
        Returns:
           threading.Thread: A thread object representing the notification subscriber.
        """
        playlist_subs = threading.Thread(target=self.subscriber, args=(ws_client,))
        playlist_subs.start()
        time.sleep(5)
        return playlist_subs

    @staticmethod
    def disable_notification_subscriber(playlist_subscriber):
        """
        Safely disable a notification subscriber
        thread and wait for it to finish.
        This static method allows you to stop a
        notification subscriber thread by setting
        the do_run attribute to False,
        and it ensures that the thread is not active before returning.
        Args:
            playlist_subscriber (Thread): The notification subscriber thread to disable.
        """
        playlist_subscriber.do_run = False
        time.sleep(2)
        assert playlist_subscriber.is_alive() is False
        # Wait for the thread to finish
        playlist_subscriber.join()

    @staticmethod
    def create_source(eio_client):
        """
        Check if a source exists in the flow manager. If not, create a new source.
        Wait until the source status becomes active after creation or activation.
        Args:
            eio_client: An instance of the EIOClient.
        Returns:
            str: The IP address of the created or existing source.
        """
        all_sources = eio_client.flow_manager.get_all_sources()
        source_ip = ""
        source_details = (
            list(
                filter(
                    lambda x: x.get("attributes", {}).get("displayName") == SOURCE_NAME,
                    all_sources.get("output", {}).get("data", []),
                )
            ),
            list(
                filter(
                    lambda x: x.get("attributes", {}).get("name")
                    == SOURCE_RECEIVER_NAME,
                    all_sources.get("output", {}).get("data", []),
                )
            ),
        )
        source_exists = any(
            entry.get("attributes", {}).get("displayName") == SOURCE_NAME
            for entry in source_details[0]
        )
        source_id = None  # Initialize source_id

        if not source_exists:
            # create source
            source = eio_client.flow_manager.create_source(
                PROTOCOL, SOURCE_NAME, IP, PORT, FILE_DEFINITION_PROFILE, ID
            )
            source_id = source["output"]["data"]["id"]
            source_ip += source["output"]["data"]["attributes"]["config"]["flow"][
                "publicIp"
            ]
            activate_source = eio_client.flow_manager.manage_source(START_ID, source_id)
            assert (
                activate_source["status"] == 200
            ), f"Error activating source status: {activate_source['status']}."
            logging.info("Source is created & activated")

        elif source_exists and source_details[0][0]["attributes"]["status"] != "ACTIVE":
            source_id = source_details[0][0]["id"]
            source_ip += source_details[0][0]["attributes"]["config"]["flow"][
                "publicIp"
            ]
            # make source active
            activate_existing_source = eio_client.flow_manager.manage_source(
                START_ID, source_id
            )
            assert activate_existing_source["status"] == 200, (
                f"Error activating existing source status: "
                f"{activate_existing_source['status']}."
            )
            logging.info("Existing source activation initiated")

        else:
            source_ip += source_details[0][0]["attributes"]["config"]["flow"][
                "publicIp"
            ]
            if source_details[0][0]["attributes"]["status"] == "ACTIVE":
                logging.info("Source already exists and is active.")
                return source_ip

        # Wait until the source status becomes ACTIVE (max wait time: 80 seconds)
        if source_id:  # only wait if source was created or activated.
            start_time = time.time()
            timeout = 80  # Maximum wait time in seconds
            max_retries = 3  # Maximum retries for source not found or unexpected status
            retry_count = 0  # Counter for failed attempts

            try:
                while True:
                    verify_all_sources = eio_client.flow_manager.get_all_sources()

                    source_data = list(
                        filter(
                            lambda x: x.get("attributes", {}).get("name")
                            == SOURCE_RECEIVER_NAME,
                            verify_all_sources.get("output", {}).get("data", []),
                        )
                    )

                    if not source_data:
                        retry_count += 1
                        logging.warning(
                            f"Source not found in the response. Retrying... ({retry_count}/{max_retries})"
                        )
                        if retry_count >= max_retries:
                            logging.error("Max retries reached. Exiting early.")
                            raise RuntimeError(
                                "Source not found after multiple retries."
                            )
                    else:
                        source_status = source_data[0]["attributes"]["config"]["flow"][
                            "status"
                        ]

                        if source_status == "ACTIVE":
                            logging.info(
                                "Source verification success: source exists and is in ACTIVE state."
                            )
                            break
                        elif source_status == "STARTING":
                            logging.info(
                                "Source is in STARTING state, waiting for it to become ACTIVE..."
                            )
                        else:
                            logging.error(f"Unexpected source status: {source_status}")
                            raise RuntimeError(
                                f"Unexpected source status: {source_status}"
                            )

                    # Check if timeout has been reached
                    if time.time() - start_time > timeout:
                        logging.error("Timeout reached after 80 seconds.")
                        raise TimeoutError(
                            "Maximum time limit reached. Exiting the loop."
                        )

                    time.sleep(10)  # Wait before checking again

            except Exception as e:
                logging.exception(f"An error occurred: {e}")
                raise

        return source_ip

    @staticmethod
    def verify_source_status(eio_client):
        """
        Verify the status of a source in the flow manager to ensure it is active and running.
        Args:
            eio_client: An instance of the EIOClient.
        Raises:
            Warning: If the maximum time limit is reached before the source becomes active.
        """
        max_time_limit = 10
        start_time = time.time()
        while True:
            # Verify source is in active state
            verify_all_sources = eio_client.flow_manager.get_all_sources()

            source_data = list(
                filter(
                    lambda x: x.get("attributes", {}).get("name")
                    == SOURCE_RECEIVER_NAME,
                    verify_all_sources.get("output", {}).get("data", []),
                )
            )
            if source_data[0]["attributes"]["config"]["flow"]["status"] == "ACTIVE":
                logging.info(
                    "Source Verification Success source exist & it's in active state"
                )
                break
            time.sleep(5)
            if time.time() - start_time > max_time_limit:
                raise TimeoutError("Maximum time limit reached. Exiting the loop.")

    @staticmethod
    def verify_event_status(
        channel_id,
        eio_client,
        ws_client,
        sequence_id,
        state,
        channel_name=None,
        event_desc=None,
    ):  # pylint: disable=R0913
        """
        Verify the status of a Live event on the specified channel after receiving a take trigger.
        Args:
            channel_id (str): The ID of the channel containing the event.
            eio_client: An instance of the EIOClient.
            ws_client: The WebSocket client used for communication.
            state (str): The expected state of the event.
            sequence_id (str): The ID of the sequence associated with the event.
            channel_name (str): The name of the channel.
            event_desc (str): A description of the event being verified.
        Raises:
            Warning: If the maximum time limit is reached before the event status can be determined.
        """
        time.sleep(2)
        event_playing_start_time = time.time()
        max_time_limit = 20
        while True:
            sequence_details = eio_client.channel_service.get_item_details(
                channel_id, ws_client, sequence_id
            )
            logging.info(sequence_details)
            if state == "now":
                assert (
                    sequence_details.get("output", {})
                    .get("item", {})
                    .get("timing", {})
                    .get("state")
                    == state
                )
                logging.info(f"{channel_name} - {event_desc}")
                break
            if state == "done":
                assert sequence_details["output"]["item"]["timing"]["state"] == state
                logging.info(
                    f"{channel_name} {event_desc} event moved to " f"done state"
                )
                break
            if state == "next":
                assert sequence_details["output"]["item"]["timing"]["state"] == state
                logging.info(
                    f"{channel_name} {event_desc} state is next event to be played out "
                )
                break
            if time.time() - event_playing_start_time > max_time_limit:
                raise TimeoutError(
                    "Maximum time restriction achieved to determine if the "
                    "event played or not. Exiting the loop."
                )

    def scte_trigger_acknowledgement(self, receiver_channel_id, trigger_name):
        """
        Verify the acknowledgment of an SCTE trigger in the receiver channel.
        Args:
            receiver_channel_id (str): The ID of the receiver channel.
            trigger_name (str | ParameterSet): The name of the SCTE trigger to be acknowledged.
        """
        scte_trigger_found = any(
            trigger.get("result", {}).get("result") == trigger_name
            and trigger.get("result", {}).get("params", {}).get("channelId")
            == receiver_channel_id
            for trigger in self.playlist_event
        )
        return scte_trigger_found

    def channel_setup(self, eio_client, source_channel_id):
        """
        Set up a channel by creating a source, adding a destination in the source channel,
        creating a destination connection, and verifying the source status.
        Args:
            eio_client: An instance of the EIOClient class for interacting with the EIO API.
            source_channel_id (str): The ID of the source channel.
        """
        # create source
        source_ip = self.create_source(eio_client)

        # create destination in source channel
        destination = eio_client.flow_manager.add_destination(
            source_channel_id, PROTOCOL, DESTINATION_NAME, source_ip, PORT
        )
        assert (
            destination["status"] == 201
        ), f"Error creating destination. Response status: {destination['status']}."
        destination_id = destination["output"]["data"]["id"]

        # Capturing the source_id
        source = eio_client.flow_manager.get_channel_configurations(source_channel_id)
        source_identification = source["output"]["data"][0]["attributes"]["outputs"][0][
            "id"
        ]

        # create destination connection
        connection = eio_client.flow_manager.create_connection(
            source_identification, destination_id
        )
        assert (
            connection["status"] == 201
        ), f"Error creating connection. Response status: {connection['status']}."

        # verify source IP in destination connection
        assert (
            connection["output"]["data"]["attributes"]["destination"]["ip"] == source_ip
        ), "Source IP in destination connection does not match the expected source IP."

        # verify source is active & running
        self.verify_source_status(eio_client)

    @staticmethod
    def clear_and_upload_playlist(
        eio_client,
        ws_client,
        current_environment,
        aws_helper_eio_dev,
        source_file,
        receiver_file,
    ):  # pylint: disable=R0913
        """
        Clear and upload playlist for the specified source and receiver channels.
        Args:
            eio_client (EioClient): An instance of the EioClient class for communication.
            ws_client (WsClient): An instance of the WsClient class for WebSocket communication.
            current_environment (dict): A dictionary containing information about the current env.
            aws_helper_eio_dev (AwsHelper): An instance of the AwsHelper class for AWS operations.
            source_file (str | ParameterSet): The file path of the playlist to be uploaded to the channel.
            receiver_file (str | ParameterSet): The file path of the playlist to be uploaded to the channel.
        Returns:
            None
        """
        eio_client.channel_service.clear_playlist(
            current_environment["channel_id_source"], ws_client
        )
        eio_client.channel_service.clear_playlist(
            current_environment["channel_id_receiver"], ws_client
        )

        # upload playlist to source & destination channel
        AwsHelper.upload_with_presigned_url(
            eio_client,
            current_environment["channel_id_source"],
            ws_client,
            source_file,
            SCHEDULE_FILE_PATH,
            aws_helper_eio_dev,
        )
        AwsHelper.upload_with_presigned_url(
            eio_client,
            current_environment["channel_id_receiver"],
            ws_client,
            receiver_file,
            SCHEDULE_FILE_PATH,
            aws_helper_eio_dev,
        )

        eio_client.playlist_management.wait_for_playlist_import(
            eio_client,
            current_environment["channel_id_receiver"],
            ws_client,
            EVENT_SIZE,
            MAX_WAIT_TIME,
        )

    @staticmethod
    def get_sequence_ids(eio_client, ws_client, current_environment, source_index):
        """
        Retrieve sequence IDs for receiver and source channel events.

        Args:
            eio_client: The EIO client instance used to interact with the services.
            ws_client: The WebSocket client instance used for communication.
            current_environment: A dictionary containing the current environment configuration,
                                 including channel IDs for receiver and source.
            source_index: An integer representing the index of the event in the source channel's playlist
                          for which the sequence ID is to be captured.

        Returns:
            tuple: A tuple containing the following sequence IDs:
                - receiver_live_event_sequence_id: The sequence ID of the receiver channel's live event.
                - receiver_program_event_sequence_id: The sequence ID of the receiver channel's program event.
                - source_take_event_sequence_id: The sequence ID of the source channel event at the specified index.

        """
        # find receiver channel & live event sequence id
        get_receiver_playlist = eio_client.channel_service.get_playlist(
            current_environment["channel_id_receiver"], EVENT_SIZE, ws_client
        )
        receiver_live_event_sequence_id = get_receiver_playlist["result"]["result"][
            "items"
        ][1]["id"]
        receiver_program_event_sequence_id = get_receiver_playlist["result"]["result"][
            "items"
        ][2]["id"]

        # capture the sequence ID for source channel event
        get_source_playlist = eio_client.channel_service.get_playlist(
            current_environment["channel_id_source"], EVENT_SIZE, ws_client
        )
        source_take_event_sequence_id = get_source_playlist["result"]["result"][
            "items"
        ][source_index]["id"]

        return (
            receiver_live_event_sequence_id,
            receiver_program_event_sequence_id,
            source_take_event_sequence_id,
        )

    @staticmethod
    def tear_down_process(eio_client, enable_socket):
        """
        Clean up and close the EIO client process.

        Args:
            eio_client: The EIO client instance to be cleaned up.
            enable_socket: A flag indicating whether to disable the notification subscriber.

        """
        if eio_client.channel_service_scte_taker.subscriber_flag:
            eio_client.channel_service_scte_taker.disable_notification_subscriber(
                enable_socket
            )
        eio_client.channel_service_scte_taker.playlist_event.clear()
        eio_client.close()

    @staticmethod
    def deactivate_source(eio_client):
        """
        Deactivate the source in the flow manager.
        Args:
            eio_client: An instance of the EIOClient.
        """
        verify_all_sources = eio_client.flow_manager.get_all_sources()
        source_data = list(
            filter(
                lambda x: x.get("attributes", {}).get("name") == SOURCE_RECEIVER_NAME,
                verify_all_sources.get("output", {}).get("data", []),
            )
        )
        source_id = source_data[0]["id"]

        # make the source inactive
        deactivate_existing_source = eio_client.flow_manager.manage_source(
            STOP_ID, source_id
        )
        assert deactivate_existing_source["status"] == 200, (
            f"Error deactivating existing source status: "
            f"{deactivate_existing_source['status']}."
        )
        logging.info("Existing source deactivated")
