"""
Lambda Function for Creating Destination and Establishing Connection.
"""

import logging

from botocore.exceptions import ClientError

from e2e.scte_capture import scte_utils
from e2e.scte_capture.constants import (
    CHANNEL_ID,
    DESTINATION_NAME,
    HOST,
    PORT,
    PROTOCOL,
    SCTE_TEST_EC2_IP_ADDRESS,
    SECURITY_GROUP_ID,
    TENANT,
    WS_HOST,
)
from e2e.scte_capture.exception.ScteCaptureException import ScteCaptureException
from utils.eio.clients.httpclient import EIOHttpClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, _):
    """
    Lambda function for creating a destination and establishing a connection.
    """
    logger.info("Creating destination...")
    aws_helper, credentials = scte_utils.fetch_credentials()

    eio_client = EIOHttpClient(
        server=HOST,
        ws_server_host=WS_HOST,
        tenant=TENANT,
        user=credentials["username"],
        password=credentials["password"],
    )
    eio_client.signin()
    channel_configuration = eio_client.flow_manager.get_channel_configurations(
        CHANNEL_ID
    )
    if channel_configuration.get("status") == 200:
        logger.info(f"channel_configurations: {channel_configuration}")
    else:
        raise ScteCaptureException(
            f"Error fetching the channel configurations: {channel_configuration}"
        )

    destinations = channel_configuration["output"]["data"]["attributes"][
        "outbound_destinations"
    ]
    channel_outputs = channel_configuration["output"]["data"]["attributes"][
        "channel_outputs"
    ]

    connected_destination = None
    if len(destinations) > 0:
        logger.info(
            f"Destination is already available for the channel {destinations[0]}"
        )
        if has_source(destinations[0], channel_outputs):
            logger.info("Connection is already established for the given destination.")
        else:
            connected_destination = create_connection(
                eio_client, destinations[0], channel_outputs[0]
            )
    else:
        destination = eio_client.flow_manager.add_destination(
            CHANNEL_ID, PROTOCOL, DESTINATION_NAME, SCTE_TEST_EC2_IP_ADDRESS, PORT
        )
        if destination.get("status") == 201:
            logger.info(f"Added destination successfully: {destination}")
        else:
            raise ScteCaptureException(f"Unable to add destination : {destination}")
        connected_destination = create_connection(
            eio_client, destination["output"]["data"], channel_outputs[0]
        )

    if connected_destination:
        source_ip = connected_destination["output"]["data"]["attributes"]["source"][
            "ip"
        ]
        logger.info(f"source_ip: {source_ip}")
        try:
            aws_helper.add_inbound_rule(SECURITY_GROUP_ID, source_ip)
        except ClientError as error:
            logger.warning(
                f"Inbound rule already exists for the given source ip {error}"
            )

    aws_helper.close()
    event["loop_counter"] = 1
    event["channel_configuration"] = channel_configuration
    return event


def create_connection(eio_client, destination: dict, channel_output: dict):
    """
    Creates a connection between a destination and a channel output.
    """
    if not (source_id := channel_output and channel_output.get("id")):
        raise ScteCaptureException("Invalid channel output.")

    if not (destination_id := destination and destination.get("id")):
        raise ScteCaptureException("Invalid channel destination.")

    connected_destination = eio_client.flow_manager.create_connection(
        CHANNEL_ID, source_id, destination_id
    )
    if connected_destination.get("status") == 201:
        logger.info(f"Connection created successfully {connected_destination}")
        return connected_destination
    raise ScteCaptureException(f"Error creating connection: {connected_destination}")


def has_source(destination: dict, outputs: list):
    """
    Checks if a destination has a connected source.
    """
    if not destination.get("connected_source") or len(outputs) == 0:
        return False

    return destination["connected_source"]["id"] == outputs[0]["id"]
