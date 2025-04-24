"""Importing necessary modules for logging, time, and generating UUIDs."""

import logging
import time
import uuid

from utils.eio.channel_config_helper import (
    construct_anc_data_config,
    construct_audio_config,
    construct_metadata_config,
    construct_miscellaneous_config,
    construct_video_config,
)
from utils.eio.clients.httpclient import EIOHttpClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def create_channel_and_fetch_id(
    eio_client: EIOHttpClient,
    metadata_config,
    video_config,
    miscellaneous_config,
    anc_data_config,
    audio_config,
):
    response = eio_client.channel_management.create_and_save_channel_config(
        metadata_config,
        video_config,
        miscellaneous_config,
        anc_data_config,
        audio_config,
    )

    if response["status"] != 202:
        logger.error(f"Channel creation failed. Response: {str(response)}")
        raise Exception(f"Channel creation failed. Response: {str(response)}")

    channel_id = response["output"]["data"]["id"]
    logging.info(f"Channel created successfully with channel id as: {channel_id}")
    return channel_id


def create_channel_with_default_config(client):
    try:
        metadata_config = construct_metadata_config()
        video_config = construct_video_config()
        audio_config = construct_audio_config()

        channel_id = create_channel_and_fetch_id(
            client,
            metadata_config,
            video_config,
            None,
            None,
            audio_config,
        )

        return channel_id

    except Exception as e:
        logging.error(f"An error occurred while creating a channel id: {str(e)}")
        raise


def create_source_channel(client):
    metadata_config = construct_metadata_config(
        name=f"scte-taker-external-source{str(uuid.uuid4())}",
        display_name="SCTE Taker External Source",
        service_tier="standard",
    )
    video_config = construct_video_config()
    audio_config = construct_audio_config(locale="en_US")
    default_anc_data = construct_anc_data_config(encoder_types=["S2038 Encoder"])
    anc_data = {
        key: value
        for key, value in default_anc_data.items()
        if key not in {"openCaption", "styling"}
    }
    anc_data.update(
        {
            "s2038": {
                "pid": 104,
                "propertyTypes": ["SCTE-104"],
                "scte104": {"field": 1, "line": 8},
            }
        }
    )
    channel_id = create_channel_and_fetch_id(
        client,
        metadata_config,
        video_config,
        None,
        anc_data,
        audio_config,
    )

    return channel_id


def create_receiver_channel(client):
    metadata_config = construct_metadata_config(
        name=f"scte-taker-external-receiver{str(uuid.uuid4())}",
        display_name="SCTE Taker External Receivers",
        service_tier="standard",
    )
    video_config = construct_video_config()
    miscellaneous_config = construct_miscellaneous_config()

    existing_incoming_scte_triggers = miscellaneous_config.get(
        "incomingScteTriggers", []
    )

    existing_incoming_scte_triggers = [
        trigger
        for trigger in existing_incoming_scte_triggers
        if trigger.get("dpi") != 300
    ]

    channel_scte_triggers = [
        {"dpi": 2, "command": "take"},
        {"dpi": 3, "command": "hold"},
    ]

    for trigger in channel_scte_triggers:
        if trigger not in existing_incoming_scte_triggers:
            existing_incoming_scte_triggers.append(trigger)

    miscellaneous_config["incomingScteTriggers"] = existing_incoming_scte_triggers
    audio_config = construct_audio_config(locale="en_US")
    anc_data = construct_anc_data_config(locale="en_US")

    channel_id = create_channel_and_fetch_id(
        client,
        metadata_config,
        video_config,
        miscellaneous_config,
        anc_data,
        audio_config,
    )

    return channel_id


def turn_on_channels(eio_client: EIOHttpClient, channel_ids: []):
    """
    This function is used to turn on one or multiple channels.
    It will check for 12 minutes to get channels online, then wait for an extra 5 minutes if needed.
    If channels don't come online after 17 minutes, it will throw an error.
    """
    list_of_channel_ids_require_turning_on = []

    # Turn on channels and add them to the list for tracking
    for channel_id in channel_ids:
        if channel_id:
            logger.info(f"Turning on channel {channel_id}...")
            try:
                channel_config = eio_client.channel_management.get_channel_by_id(
                    channel_id
                )
                if _is_channel_idle(channel_config):
                    eio_client.channel_management.update_channel_deployment(
                        channel_id=channel_id, required_state="ON"
                    )
                    list_of_channel_ids_require_turning_on.append(channel_id)
                else:
                    logger.info(f"Channel {channel_id} is already live.")
            except Exception as exception:
                logger.error(
                    f"An exception occurred while turning on channel {channel_id}: {exception}"
                )
                raise

    initial_timeout_minutes = 12
    extended_timeout_minutes = 5
    total_timeout_minutes = initial_timeout_minutes + extended_timeout_minutes
    start_time = time.time()

    while list_of_channel_ids_require_turning_on:
        elapsed_time = time.time() - start_time

        if elapsed_time > total_timeout_minutes * 60:
            logger.error(
                f"Timeout: Channels did not become 'ON' within {total_timeout_minutes} minutes."
            )
            raise Exception(
                f"Timeout: Channels did not become 'ON' within {total_timeout_minutes} minutes."
            )

        if (
            initial_timeout_minutes * 60
            < elapsed_time
            <= (initial_timeout_minutes + 1) * 60
        ):
            logger.warning(
                f"Channels not online after {initial_timeout_minutes} minutes. Waiting for additional {extended_timeout_minutes} minutes."
            )

        time.sleep(60)

        channel_ids = list_of_channel_ids_require_turning_on[:]
        for channel_id in channel_ids:
            try:
                channel_config = eio_client.channel_management.get_channel_by_id(
                    channel_id
                )
                if _is_channel_live(channel_config):
                    logger.info(f"Channel {channel_id} is now live.")
                    list_of_channel_ids_require_turning_on.remove(channel_id)
            except Exception as exception:
                logger.error(
                    f"An exception occurred while checking channel {channel_id} status: {exception}"
                )
                raise

    logger.info("All channels are now online.")


def turn_off_channels(eio_client: EIOHttpClient, channel_ids: []):
    """
    This function is used to turn off one or multiple channels.
    """
    list_of_channel_ids_require_turning_off = []

    # Turn on channels and add them to the list for tracking
    for channel_id in channel_ids:
        if channel_id:
            logger.info(f"Turning off channel {channel_id}...")

            try:
                channel_config = eio_client.channel_management.get_channel_by_id(
                    channel_id
                )
                if _is_channel_live(channel_config):
                    eio_client.channel_management.update_channel_deployment(
                        channel_id=channel_id, required_state="OFF"
                    )
                    list_of_channel_ids_require_turning_off.append(channel_id)
                else:
                    logger.info(f"Channel {channel_id} is already OFF.")

            except Exception as exception:
                logger.error(
                    f"An exception occurred while turning off channel {channel_id}: {exception}"
                )
                raise

    timeout_minutes = 12  # threshold channel turn on time
    start_time = time.time()
    while list_of_channel_ids_require_turning_off:
        if time.time() - start_time > timeout_minutes * 60:
            logger.error(
                f"Timeout: Channels did not become 'OFF' within the specified time."
            )
            raise Exception(
                f"Timeout: Channels did not become 'OFF' within the specified time."
            )

        time.sleep(60)
        channels_to_check = list_of_channel_ids_require_turning_off[:]
        for channel_id in channels_to_check:
            try:
                channel_config = eio_client.channel_management.get_channel_by_id(
                    channel_id
                )
                if _is_channel_idle(channel_config):
                    logger.info(f"Channel {channel_id} is now idle.")
                    list_of_channel_ids_require_turning_off.remove(channel_id)
            except Exception as exception:
                logger.error(
                    f"An exception occurred while checking channel {channel_id} status: {exception}"
                )
                raise


def delete_channels(eio_client: EIOHttpClient, channel_ids: []):
    """
    This function is used to delete one or multiple channels.
    """
    for channel_id in channel_ids:
        try:
            response = eio_client.channel_management.delete_channel_config(channel_id)
            if response["status"] != 204:
                logger.error(
                    f"Channel deletion failed for ID {channel_id}. Response: {str(response)}"
                )
                raise Exception(f"Channel deletion failed for ID {channel_id}.")
            else:
                logging.info(
                    f"Channel with ID {channel_id} has been successfully deleted."
                )
        except Exception as exception:
            logger.error(
                f"An exception occurred while deleting channel {channel_id}: {exception}"
            )
            raise


def _is_channel_live(channel_config):
    try:
        status = channel_config["output"]["data"]["attributes"]["metadata"]["status"]
        return status == "LIVE"
    except KeyError as e:
        logger.error(f"KeyError: {e} is missing in channel_config")
        raise


def _is_channel_idle(channel_config):
    try:
        status = channel_config["output"]["data"]["attributes"]["metadata"]["status"]
        return status == "IDLE"
    except KeyError as e:
        logger.error(f"KeyError: {e} is missing in channel_config")
        raise
