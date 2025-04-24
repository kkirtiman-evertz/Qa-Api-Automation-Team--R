"""Importing necessary modules for SCTE test."""

import logging
import time
import uuid
from threading import ThreadError

import pytest

from tests.tests_channel_service.config.scte_taker_config import (
    ASSET_ID,
    DISABLED_FLAG_HOLD_RECEIVER_FILE,
    DISABLED_FLAG_RECEIVER_FILE,
    RECEIVER_FILE,
    RECEIVER_HOLD_TRIGGER_FILE,
    SOURCE_FILE,
    SOURCE_HOLD_TRIGGER_FILE,
    START_MODE,
    TEMPLATE_NAME,
)
from utils.eio.clients.httpclient import EIOHttpClient


@pytest.mark.usefixtures("scte_channel_setup")
class TestScteTaker:
    """
    Tests the SCTE external taker and SCTE external hold.
    """

    def test_scte_take_trigger(
        self, eio_client: EIOHttpClient, aws_helper_eio_dev, current_environment
    ):
        """
        Tests the SCTE external taker
        and SCTE external hold.
        @param eio_client: EIOHttpClient: HTTP client for EIO operations.
        @param current_environment: A dictionary
        representing the current environment configuration.
        @return: The SCTE incoming triggers are captured.
        """

        try:
            # channel configuration
            eio_client.channel_service_scte_taker.subscriber_flag = False
            ws_client = eio_client.get_ws_client(str(uuid.uuid4()))

            eio_client.channel_service_scte_taker.clear_and_upload_playlist(
                eio_client,
                ws_client,
                current_environment,
                aws_helper_eio_dev,
                SOURCE_FILE,
                RECEIVER_FILE,
            )
            # TODO: Remove below few lines once this tests are consistent # noqa pylint: disable=W0511
            sequence_details = eio_client.channel_service.insert_sequence(
                current_environment["channel_id_source"],
                START_MODE,
                TEMPLATE_NAME,
                ASSET_ID,
                ws_client,
            )
            time.sleep(2)

            (
                receiver_live_event_sequence_id,
                receiver_program_event_sequence_id,
                source_take_event_sequence_id,
            ) = eio_client.channel_service_scte_taker.get_sequence_ids(
                eio_client, ws_client, current_environment, 2
            )

            # Registration to receiver SCTE trigger in websocket
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=True
            )
            time.sleep(2)

            # prime & take on receiver channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_receiver"], ws_client, action="take"
            )
            time.sleep(130)

            # make sure receiver LIVE event started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Live event started playing",
            )

            # TODO: Remove below few lines once this tests are consistent # noqa pylint: disable=W0511
            eio_client.channel_service.delete_sequence(
                sequence_details["result"]["result"],
                current_environment["channel_id_source"],
                ws_client,
            )

            # Enable the Subscriber to receive notifications
            enable_socket = (
                eio_client.channel_service_scte_taker.enable_notification_subscriber(
                    ws_client
                )
            )
            eio_client.channel_service_scte_taker.subscriber_flag = True
            time.sleep(2)
            # Prime & take on the source channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_source"], ws_client, action="take"
            )
            start_time = time.time()
            while time.time() - start_time < 13:
                if len(eio_client.channel_service_scte_taker.playlist_event) == 1:
                    eio_client.channel_service_scte_taker.state.append(
                        "SCTE Trigger Found"
                    )
                    break

            # verify SCTE trigger
            trigger_status = (
                eio_client.channel_service_scte_taker.scte_trigger_acknowledgement(
                    current_environment["channel_id_receiver"], trigger_name="take"
                )
            )
            assert (
                trigger_status is True
            ), "SCTE Trigger acknowledgment for take not found in receiver channel."
            logging.info("External SCTE take Trigger received in receiver channel")

            # deregister to receive notifications & close the thread
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=False
            )
            eio_client.channel_service_scte_taker.disable_notification_subscriber(
                enable_socket
            )

            # verify source channel event started playing

            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_source"],
                eio_client,
                ws_client,
                source_take_event_sequence_id,
                state="now",
                channel_name="Source Channel",
                event_desc="Program event is on AIR",
            )

            # verify the receiver channel Live event stopped playing after take trigger received
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="done",
                channel_name="Receiver Channel",
                event_desc="Live",
            )

            # Verify next event started playing immediately
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_program_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Program event next to Live event is on AIR",
            )

        except (
            KeyError,
            ValueError,
            ThreadError,
            IndexError,
            TypeError,
        ) as error:
            pytest.fail(f"An exception occurred: {error}")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An exception occurred: {exception}")
        finally:
            eio_client.channel_service_scte_taker.tear_down_process(
                eio_client, enable_socket
            )

    def test_disabled_take_trigger(
        self, eio_client: EIOHttpClient, aws_helper_eio_dev, current_environment
    ):
        """
        Tests the SCTE external take trigger will not be received when external flag is disabled
        @param eio_client: EIOHttpClient: HTTP client for EIO operations.
        @param current_environment: A dictionary
        representing the current environment configuration.
        @return: The SCTE incoming trigger should not receive.
        """
        try:

            eio_client.channel_service_scte_taker.subscriber_flag = False
            ws_client = eio_client.get_ws_client(str(uuid.uuid4()))

            eio_client.channel_service_scte_taker.clear_and_upload_playlist(
                eio_client,
                ws_client,
                current_environment,
                aws_helper_eio_dev,
                SOURCE_FILE,
                DISABLED_FLAG_RECEIVER_FILE,
            )

            # TODO: Remove below few lines once dev fix - EIO-12904 # noqa pylint: disable=W0511
            sequence_details = eio_client.channel_service.insert_sequence(
                current_environment["channel_id_source"],
                START_MODE,
                TEMPLATE_NAME,
                ASSET_ID,
                ws_client,
            )
            time.sleep(1)
            eio_client.channel_service.delete_sequence(
                sequence_details["result"]["result"],
                current_environment["channel_id_source"],
                ws_client,
            )

            # find receiver channel & live event sequence id
            (
                receiver_live_event_sequence_id,
                receiver_program_event_sequence_id,
                source_take_event_sequence_id,
            ) = eio_client.channel_service_scte_taker.get_sequence_ids(
                eio_client, ws_client, current_environment, 2
            )

            # Registration to receiver SCTE trigger in websocket
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=True
            )
            time.sleep(2)

            # prime & take on receiver channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_receiver"], ws_client, action="take"
            )

            # make sure receiver LIVE event started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Live event started playing",
            )

            # Enable the Subscriber to receive notifications
            enable_socket = (
                eio_client.channel_service_scte_taker.enable_notification_subscriber(
                    ws_client
                )
            )
            eio_client.channel_service_scte_taker.subscriber_flag = True

            # Prime & take on the source channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_source"], ws_client, action="take"
            )

            time.sleep(20)
            eio_client.channel_service_scte_taker.disable_notification_subscriber(
                enable_socket
            )

            # deregister to receive notifications & close the thread
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=False
            )
            time.sleep(5)

            # verify source channel event started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_source"],
                eio_client,
                ws_client,
                source_take_event_sequence_id,
                state="now",
                channel_name="Source Channel",
                event_desc="Program event is on AIR",
            )

            # verify SCTE trigger
            trigger_status = (
                eio_client.channel_service_scte_taker.scte_trigger_acknowledgement(
                    current_environment["channel_id_receiver"], trigger_name="take"
                )
            )
            assert trigger_status is False, (
                "SCTE Trigger acknowledgment for take found in receiver channel which "
                "is unexpected due to flag is disabled"
            )
            logging.info(
                "External SCTE take Trigger not received in receiver channel when flag is disabled"
            )

            # verify the receiver channel Live event is keep playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Live event is on AIR",
            )

            # Verify next event is in next state - not started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_program_event_sequence_id,
                state="next",
                channel_name="Receiver Channel",
                event_desc="Program event",
            )

        except (
            KeyError,
            ValueError,
            ThreadError,
            IndexError,
            TypeError,
        ) as error:
            pytest.fail(f"An exception occurred: {error}")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An exception occurred: {exception}")
        finally:
            eio_client.channel_service_scte_taker.tear_down_process(
                eio_client, enable_socket
            )

    def test_scte_hold_trigger(
        self, eio_client: EIOHttpClient, aws_helper_eio_dev, current_environment
    ):
        """
        Test the SCTE Hold Trigger functionality.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for interacting
            with the channel service and WebSocket client.
            aws_helper_eio_dev: An AWS helper object.
            current_environment: The current environment settings.
        """
        try:

            eio_client.channel_service_scte_taker.subscriber_flag = False
            eio_client.channel_service_scte_taker.state.clear()
            ws_client = eio_client.get_ws_client(str(uuid.uuid4()))

            eio_client.channel_service_scte_taker.clear_and_upload_playlist(
                eio_client,
                ws_client,
                current_environment,
                aws_helper_eio_dev,
                SOURCE_HOLD_TRIGGER_FILE,
                RECEIVER_HOLD_TRIGGER_FILE,
            )

            (
                receiver_live_event_sequence_id,
                receiver_program_event_sequence_id,
                source_take_event_sequence_id,
            ) = eio_client.channel_service_scte_taker.get_sequence_ids(
                eio_client, ws_client, current_environment, 3
            )

            # Registration to receiver SCTE trigger in websocket
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=True
            )

            time.sleep(2)

            # prime & take on receiver channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_receiver"], ws_client, action="take"
            )

            # make sure receiver LIVE event started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Live event started playing",
            )

            # Prime & take on the source channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_source"], ws_client, action="take"
            )

            time.sleep(7)
            # Enable the Subscriber to receive notifications
            enable_socket = (
                eio_client.channel_service_scte_taker.enable_notification_subscriber(
                    ws_client
                )
            )
            eio_client.channel_service_scte_taker.subscriber_flag = True

            time.sleep(20)

            # deregister to receive notifications & close the thread
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=False
            )
            # verify source channel event started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_source"],
                eio_client,
                ws_client,
                source_take_event_sequence_id,
                state="now",
                channel_name="Source Channel",
                event_desc="Program event is on AIR",
            )

            # verify SCTE trigger
            trigger_status = (
                eio_client.channel_service_scte_taker.scte_trigger_acknowledgement(
                    current_environment["channel_id_receiver"], trigger_name="hold"
                )
            )
            eio_client.channel_service_scte_taker.disable_notification_subscriber(
                enable_socket
            )
            assert (
                trigger_status is True
            ), "SCTE Trigger acknowledgment for Hold found in receiver channel"
            logging.info("External SCTE Hold Trigger received in receiver channel")

            assert (
                len(eio_client.channel_service_scte_taker.state) == 1
            ), "Hold state - Holding not found even after Receiving the HOLD trigger"
            logging.info("Playlist is moved to hold state ")

            # verify the receiver channel Live event is keep playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Live event is on AIR",
            )

            # Verify next event is in next state - not started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_program_event_sequence_id,
                state="next",
                channel_name="Receiver Channel",
                event_desc="Program event",
            )

        except (
            KeyError,
            ValueError,
            ThreadError,
            IndexError,
            TypeError,
        ) as error:
            pytest.fail(f"An exception occurred: {error}")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An exception occurred: {exception}")
        finally:
            eio_client.channel_service_scte_taker.tear_down_process(
                eio_client, enable_socket
            )

    def test_disabled_hold_trigger(
        self, eio_client: EIOHttpClient, aws_helper_eio_dev, current_environment
    ):
        """
        Test the behavior when SCTE Hold Trigger is disabled.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for
            interacting with the channel service and WebSocket client.
            aws_helper_eio_dev: An AWS helper object.
            current_environment: The current environment settings.
        """

        try:

            eio_client.channel_service_scte_taker.subscriber_flag = False
            eio_client.channel_service_scte_taker.state.clear()
            ws_client = eio_client.get_ws_client(str(uuid.uuid4()))

            eio_client.channel_service_scte_taker.clear_and_upload_playlist(
                eio_client,
                ws_client,
                current_environment,
                aws_helper_eio_dev,
                SOURCE_HOLD_TRIGGER_FILE,
                DISABLED_FLAG_HOLD_RECEIVER_FILE,
            )

            # find receiver channel & live event sequence id
            (
                receiver_live_event_sequence_id,
                receiver_program_event_sequence_id,
                source_take_event_sequence_id,
            ) = eio_client.channel_service_scte_taker.get_sequence_ids(
                eio_client, ws_client, current_environment, 3
            )

            # Registration to receiver SCTE trigger in websocket
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=True
            )

            time.sleep(2)

            # prime & take on receiver channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_receiver"], ws_client, action="take"
            )

            # make sure receiver LIVE event started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Live event started playing",
            )

            # Prime & take on the source channel
            eio_client.channel_service.control_playlist(
                current_environment["channel_id_source"], ws_client, action="take"
            )

            time.sleep(10)
            # Enable the Subscriber to receive notifications
            enable_socket = (
                eio_client.channel_service_scte_taker.enable_notification_subscriber(
                    ws_client
                )
            )
            eio_client.channel_service_scte_taker.subscriber_flag = True

            time.sleep(12)
            eio_client.channel_service_scte_taker.disable_notification_subscriber(
                enable_socket
            )

            # deregister to receive notifications & close the thread
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=False
            )
            time.sleep(5)

            # verify source channel event started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_source"],
                eio_client,
                ws_client,
                source_take_event_sequence_id,
                state="now",
                channel_name="Source Channel",
                event_desc="Program event is on AIR",
            )

            # verify SCTE trigger
            trigger_status = (
                eio_client.channel_service_scte_taker.scte_trigger_acknowledgement(
                    current_environment["channel_id_receiver"], trigger_name="hold"
                )
            )
            assert (
                trigger_status is False
            ), "SCTE Trigger acknowledgment for Hold not found in receiver channel"
            logging.info(
                "External SCTE Hold Trigger not received in receiver channel "
                "which is expected as flag is disabled"
            )

            assert (
                len(eio_client.channel_service_scte_taker.state) == 0
            ), "Playlist is in holding state = state changed holding found"
            logging.info("Playlist is not moved to Hold state")

            # verify the receiver channel Live event is moved to done
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="done",
                channel_name="Receiver Channel",
                event_desc="Live",
            )

            # Verify next event which was is in next state - now started playing
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_program_event_sequence_id,
                state="now",
                channel_name="Receiver Channel",
                event_desc="Program event started playing",
            )
        except (
            KeyError,
            ValueError,
            ThreadError,
            IndexError,
            TypeError,
        ) as error:
            pytest.fail(f"An exception occurred: {error}")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An exception occurred: {exception}")
        finally:
            eio_client.channel_service_scte_taker.tear_down_process(
                eio_client, enable_socket
            )

    ParameterSets = [
        pytest.param(
            "hold",
            3,
            SOURCE_HOLD_TRIGGER_FILE,
            RECEIVER_HOLD_TRIGGER_FILE,
            id="omitting_hold_trigger_if_live_event_off_air",
        ),
        pytest.param(
            "take",
            2,
            SOURCE_FILE,
            RECEIVER_FILE,
            id="omitting_take_trigger_if_live_event_off_air",
        ),
    ]

    @pytest.mark.parametrize(
        "trigger, scte_block_event_index, source_file, receiver_file", ParameterSets
    )
    def test_omitting_trigger_if_live_event_off_air(
        self,
        eio_client: EIOHttpClient,
        aws_helper_eio_dev,
        current_environment,
        trigger,
        scte_block_event_index,
        source_file,
        receiver_file,
    ):  # pylint: disable=R0913
        # pylint: disable=C0301

        """
        Test the behavior of the system when omitting SCTE triggers if the live event is not on air.

        Params:

            eio_client (EIOHttpClient): An instance of the EIOHttpClient used for making API calls.
            aws_helper_eio_dev (object): A helper object for AWS-related tasks.
            current_environment (dict): Dictionary containing environment-specific configuration.
            trigger (str): The type of SCTE trigger ("hold" or "take").
            scte_block_event_index (int): The index of the SCTE block event.
            source_file (str): The source file for the SCTE trigger.
            receiver_file (str): The receiver file for the SCTE trigger.
        """
        try:
            eio_client.channel_service_scte_taker.subscriber_flag = False
            eio_client.channel_service_scte_taker.state.clear()
            ws_client = eio_client.get_ws_client(str(uuid.uuid4()))

            eio_client.channel_service_scte_taker.clear_and_upload_playlist(
                eio_client,
                ws_client,
                current_environment,
                aws_helper_eio_dev,
                source_file,
                receiver_file,
            )

            # find sequence id's
            (
                receiver_live_event_sequence_id,
                _,
                source_take_event_sequence_id,
            ) = eio_client.channel_service_scte_taker.get_sequence_ids(
                eio_client, ws_client, current_environment, scte_block_event_index
            )

            # Registration to receiver SCTE trigger in websocket
            eio_client.channel_service.handle_channel_registration(
                current_environment["channel_id_receiver"], ws_client, register=True
            )

            time.sleep(2)

            if trigger == "hold":

                # Prime & take on the source channel
                eio_client.channel_service.control_playlist(
                    current_environment["channel_id_source"], ws_client, action="take"
                )

                time.sleep(10)
                # Enable the Subscriber to receive notifications
                enable_socket = eio_client.channel_service_scte_taker.enable_notification_subscriber(
                    ws_client
                )
                eio_client.channel_service_scte_taker.subscriber_flag = True

                time.sleep(12)
                eio_client.channel_service_scte_taker.disable_notification_subscriber(
                    enable_socket
                )

                # deregister to receive notifications & close the thread
                eio_client.channel_service.handle_channel_registration(
                    current_environment["channel_id_receiver"],
                    ws_client,
                    register=False,
                )
                time.sleep(5)

                # verify source channel event started playing
                eio_client.channel_service_scte_taker.verify_event_status(
                    current_environment["channel_id_source"],
                    eio_client,
                    ws_client,
                    source_take_event_sequence_id,
                    state="now",
                    channel_name="Source Channel",
                    event_desc="Program event is on AIR",
                )
            else:
                # Enable the Subscriber to receive notifications
                enable_socket = eio_client.channel_service_scte_taker.enable_notification_subscriber(
                    ws_client
                )
                eio_client.channel_service_scte_taker.subscriber_flag = True
                time.sleep(5)

                # Prime & take on the source channel
                eio_client.channel_service.control_playlist(
                    current_environment["channel_id_source"], ws_client, action="take"
                )
                time.sleep(12)
                eio_client.channel_service_scte_taker.disable_notification_subscriber(
                    enable_socket
                )

                # deregister to receive notifications & close the thread
                eio_client.channel_service.handle_channel_registration(
                    current_environment["channel_id_receiver"],
                    ws_client,
                    register=False,
                )

                # verify source channel event started playing
                eio_client.channel_service_scte_taker.verify_event_status(
                    current_environment["channel_id_source"],
                    eio_client,
                    ws_client,
                    source_take_event_sequence_id,
                    state="now",
                    channel_name="Source Channel",
                    event_desc="Program event is on AIR",
                )

            # verify SCTE trigger
            trigger_status = (
                eio_client.channel_service_scte_taker.scte_trigger_acknowledgement(
                    current_environment["channel_id_receiver"], trigger_name=trigger
                )
            )
            assert (
                trigger_status is False
            ), f"SCTE Trigger acknowledgment for {trigger} found in receiver channel"
            logging.info(
                f"External SCTE {trigger} Trigger not received in receiver channel "
                "which is expected as receiver channel live event is not on AIR"
            )

            if trigger == "hold":
                assert (
                    len(eio_client.channel_service_scte_taker.state) == 0
                ), "Playlist is in holding state = state changed holding found"
                logging.info("Playlist is not moved to Hold state")

            # verify the receiver channel Live event is not moved to done
            eio_client.channel_service_scte_taker.verify_event_status(
                current_environment["channel_id_receiver"],
                eio_client,
                ws_client,
                receiver_live_event_sequence_id,
                state="next",
                channel_name="Receiver Channel",
                event_desc="Live",
            )

        except (
            KeyError,
            ValueError,
            ThreadError,
            IndexError,
            TypeError,
        ) as error:
            pytest.fail(f"An exception occurred: {error}")
        except Exception as exception:  # pylint: disable=broad-except
            pytest.fail(f"An exception occurred: {exception}")
        finally:
            eio_client.channel_service_scte_taker.tear_down_process(
                eio_client, enable_socket
            )
