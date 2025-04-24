"""
Lambda function to take channel off air.
"""

import logging

from e2e.scte_capture import scte_utils
from e2e.scte_capture.constants import CHANNEL_ID, HOST, TENANT, WS_HOST
from e2e.scte_capture.exception.ScteCaptureException import ScteCaptureException
from utils.eio.clients.httpclient import EIOHttpClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, _):  # pylint: disable=unused-argument
    """
    Lambda function for taking a channel off the air.
    """
    # pylint: disable=R0801
    aws_helper, credentials = scte_utils.fetch_credentials()

    eio_client = EIOHttpClient(
        server=HOST,
        ws_server_host=WS_HOST,
        tenant=TENANT,
        user=credentials["username"],
        password=credentials["password"],
    )
    eio_client.signin()

    channel_details = eio_client.channel_management.get_channel_by_id(CHANNEL_ID)
    logger.info(f"channel details: {channel_details}")
    channel_status = channel_details["output"]["data"]["attributes"]["metadata"][
        "status"
    ]

    if channel_status == "IDLE":
        logger.info("Channel is already in IDLE state.")
        return

    if channel_status != "LIVE":
        raise ScteCaptureException(
            "The channel is not in an LIVE state to take-off air; please try again later."
        )

    aws_helper.close()
    response = eio_client.channel_management.trigger_deployment(CHANNEL_ID, "OFF")
    if response.get("status") == 202:
        logger.info(f"Channel taken off from air successfully: {response}.")
    else:
        logger.error(f"Unable to take channel off air {response}")
        raise ScteCaptureException("Unable to deploy channel")
