"""
Lambda Function for Performing PRIME Take Related to SCTE Capture
"""

import datetime
import uuid

from e2e.scte_capture import scte_utils
from e2e.scte_capture.constants import (
    CHANNEL_ID,
    FILE_DATE_FORMAT,
    HOST,
    TENANT,
    WS_HOST,
)
from e2e.scte_capture.exception.ScteCaptureException import ScteCaptureException
from utils.aws_helper import AwsHelper
from utils.eio.clients.httpclient import EIOHttpClient
from utils.eio.clients.wsclient import EIOWSClient


def lambda_handler(event, _):
    """
    Lambda function for performing PRIME take related to SCTE capture.
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
    ws_client = EIOWSClient(WS_HOST, eio_client.auth_token, str(uuid.uuid4()))
    try:
        instance_id = aws_helper.get_instance_id()
    except Exception as error:
        raise ScteCaptureException(str(error)) from error
    current_date = datetime.datetime.now().strftime(FILE_DATE_FORMAT)
    pre_processing(aws_helper, current_date, instance_id)
    eio_client.channel_service.control_playlist(CHANNEL_ID, ws_client, action="take")
    post_processing(
        aws_helper, current_date, instance_id, event["channel_configuration"]
    )

    aws_helper.close()
    event["current_date"] = current_date
    event["instance_id"] = instance_id
    return event


def post_processing(
    aws_helper: AwsHelper,
    current_date: str,
    instance_id: str,
    channel_configuration: dict,
):
    """
    Performs running a TSDuck analyzer.
    """
    try:
        try:
            source_ip = channel_configuration["output"]["data"]["attributes"][
                "channel_outputs"
            ][0]["ip"]
        except KeyError as error:
            raise ScteCaptureException("Invalid source IP.") from error

        tsduck_analyzer_cmd = (
            f"sudo tsp -I ip 0.0.0.0:1024 --source {source_ip} --receive-timeout "
            f"5000 -P splicemonitor -a -j -d -o scte_capture_{current_date}.json "
            f"-P until --seconds 80 -O drop"
        )
        aws_helper.run_ssm_command(instance_id, tsduck_analyzer_cmd)
    except Exception as error:
        raise ScteCaptureException(
            f"Unable to execute ts duck command {str(error)}"
        ) from error


def pre_processing(aws_helper: AwsHelper, current_date: str, instance_id: str):
    """
    Performs removing previous capture files.
    """
    try:
        remove_scte_capture_cmd = f"sudo rm scte_capture_{current_date}.json"
        aws_helper.run_ssm_command(instance_id, remove_scte_capture_cmd)
    except Exception as error:
        raise ScteCaptureException("Unable to remove scte capture file.") from error
