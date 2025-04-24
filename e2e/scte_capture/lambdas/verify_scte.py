"""verify scte run"""

import json
import logging
import time

import boto3

from e2e.scte_capture.exception.ScteCaptureException import ScteCaptureException
from utils.aws_helper import AwsHelper

SPLICE_INFORMATION_TABLE = "splice_information_table"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, _):
    """
    Lambda function for verifying an SCTE capture run.
    """
    aws_helper = AwsHelper()
    file_content = retrieve_scte_result(
        aws_helper, event["current_date"], event["instance_id"]
    )
    if not file_content:
        raise ScteCaptureException("Failed to generate scte_capture json data")

    verify_scte_run(
        aws_helper, event["current_date"], event["instance_id"], file_content
    )

    aws_helper.close()
    loop_counter = event["loop_counter"]
    loop_counter += 1
    event["loop_counter"] = loop_counter
    return event


def verify_scte_run(
    aws_helper: AwsHelper, current_date: str, instance_id: str, command_output: str
):
    """
    Verifies the SCTE capture run.
    """
    try:
        data, event_count, splice_info_table_count = get_event_and_splice_count(
            command_output
        )
        logger.info(
            f"event_count: {event_count}, splice_info_table_count: {splice_info_table_count}"
        )

        if event_count != 2:
            raise ScteCaptureException(f"Invalid Event count {event_count}")
        if splice_info_table_count != 2:
            raise ScteCaptureException(f"Invalid splice info {splice_info_table_count}")

        log_pending_occurrence(data)
        logger.info("All tests pass.")
    except Exception as error:
        copy_from_ec2_to_s3(aws_helper, current_date, instance_id)
        # copy is taking bit of time
        time.sleep(1)
        file_content = aws_helper.read_file_from_s3(
            "qa-testing-output", f"scte-output/scte_capture_{current_date}.json"
        )
        if file_content:
            logger.info(file_content)
        else:
            logger.info("No file content...")
        raise error


def get_event_and_splice_count(command_output: str):
    """
    Extracts event and splice information table counts from the SCTE capture output.
    """
    event_count = 0
    splice_info_table_count = 0
    data = json.loads(command_output)
    logger.info(f"data: {data}")
    for item in data:
        name = item.get("#name")
        splice_pid = item.get("splice-pid")
        if name == "event":
            event_count += 1
            if splice_pid == 500:
                logger.info(f"Event with splice_pid 500: {item}")
        elif name == SPLICE_INFORMATION_TABLE:
            splice_info_table_count += 1
    return data, event_count, splice_info_table_count


def log_pending_occurrence(data):
    """
    Logs details about the first occurrence with 'progress: pending' in the SCTE capture data.
    """
    first_pending_occurrence = next(
        (item for item in data if item.get("progress") == "pending"), None
    )
    if first_pending_occurrence:
        logger.info("First occurrence with 'progress: pending':")
    else:
        logger.info("No occurrence with 'progress: pending' found.")


def retrieve_scte_result(aws_helper: AwsHelper, current_date: str, instance_id: str):
    """
    Retrieves SCTE capture result from the specified instance.
    """
    try:
        display_content_cmd = f"cat scte_capture_{current_date}.json"
        file_content = aws_helper.run_ssm_command(instance_id, display_content_cmd)
        logger.info(f"file content: {file_content}")
    except Exception as error:
        raise ScteCaptureException("Unable to get the scte file contents.") from error
    time.sleep(1)

    # Get command invocation details
    command_id = file_content["Command"]["CommandId"]
    invocation_details = boto3.client("ssm").get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id,
    )
    if "StandardOutputContent" in invocation_details:
        logger.info(
            f'StandardOutputContent {invocation_details["StandardOutputContent"]}'
        )
        return invocation_details["StandardOutputContent"]
    raise ScteCaptureException("No Scte Output Found")


def copy_from_ec2_to_s3(aws_helper: AwsHelper, current_date: str, instance_id: str):
    """
    Copies the SCTE capture result from the EC2 instance to an S3 bucket.
    """
    try:
        return aws_helper.run_ssm_command(
            instance_id,
            f"sudo aws s3 cp scte_capture_{current_date}.json s3://qa-testing-output/scte-output/",
        )
    except Exception as error:
        raise ScteCaptureException("Unable to copy file.") from error
