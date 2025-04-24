"""
Lambda function to deploy channel.
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
    Lambda function for deploying a channel using EIOHttpClient.
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
    if channel_details.get("status") == 200:
        logger.info(f"channel details: {channel_details}")
    else:
        raise ScteCaptureException(
            f"Error finding details of channel {channel_details}"
        )

    if (
        channel_status := channel_details["output"]["data"]["attributes"]["metadata"][
            "status"
        ]
    ) != "IDLE":
        logger.info(
            "The channel is not in an idle state for deployment; please try again later."
        )
        return {
            "statusCode": 200,
            "message": f"The channel is in {channel_status} state, please try again later.",
        }

    response = eio_client.channel_management.trigger_deployment(CHANNEL_ID, "ON")
    if response.get("status") == 202:
        logger.info(f"Deployment triggered successfully: {response}.")
    else:
        logger.error(f"Unable to deploy channel {response}")
        raise ScteCaptureException(
            f"Unable to deploy channel, channel status: {channel_status}"
        )

    aws_helper.close()
    return {"status": 200, "message": "Channel Deployment requested successfully"}
