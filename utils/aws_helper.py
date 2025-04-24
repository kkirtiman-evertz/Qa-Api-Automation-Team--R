"""Importing necessary modules for logging and boto."""

import json
import logging
import os

import boto3
import pytest
import requests
from botocore.exceptions import ClientError

from e2e.scte_capture.constants import SCTE_TEST_INSTANCE_NAME

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()


class AwsHelper:
    """Defining AWS functions"""

    def __init__(self, profile_name=None):
        self.playlist_management = None
        self.channel_service = None
        self.aws_session = boto3.Session(profile_name=profile_name)
        self.ssm_client = self.aws_session.client("ssm")
        self.s3_client = self.aws_session.client("s3")
        self.ec2_client = self.aws_session.client("ec2")

    def get_ssm_parameter(self, parameter_name):
        """
        Retrieve a parameter from AWS Systems Manager (SSM).

        Args:
            parameter_name (str): The name of the parameter.

        Returns:
            str: The value of the parameter.
        """
        try:
            response = self.ssm_client.get_parameter(Name=parameter_name)
            return response["Parameter"]["Value"]
        except self.ssm_client.exceptions.ParameterNotFound as exception:
            logger.error(
                "Parameter '%s' not found in SSM: %s", parameter_name, exception
            )
            return None
        except Exception as exception:
            logger.error(
                "Error retrieving parameter '%s' from SSM: %s",
                parameter_name,
                exception,
            )
            return None

    def list_objects_in_s3_bucket(self, s3_bucket_name, last_modified_object=None):
        """
        List objects in an S3 bucket and return their keys.

        Args:
            s3_bucket_name (str): The name of the S3 bucket.
            last_modified_object: Filter for content in s3 bucket

        Returns:
            list: List of keys for the contents inside the S3 bucket.
        """
        try:
            contents_keys = []
            list_data = self.aws_session.client("s3").list_objects(
                Bucket=s3_bucket_name
            )
            if "Contents" in list_data and last_modified_object is None:
                contents_keys += [obj["Key"] for obj in list_data["Contents"]]
                if contents_keys is None:
                    raise Exception("Unable to fetch content keys from s3 objects")
                else:
                    return contents_keys

            elif last_modified_object:
                last_modified_object = max(
                    list_data.get("Contents", []),
                    key=lambda x: x.get("LastModified", ""),
                )
                if last_modified_object is None:
                    raise Exception("Unable to fetch last modified object from s3")
                else:
                    return last_modified_object

        except Exception as exception:
            raise exception

    def get_object_from_s3(self, s3_bucket_name, object_key):
        """
        Retrieves the contents of an object from an S3 bucket.

        Args:
            s3_bucket_name (str): The name of the S3 bucket.
            object_key (str): The key of the object within the S3 bucket.

        Returns:
            str: The contents of the object decoded as UTF-8.
        """
        try:
            s3 = self.aws_session.client("s3")
            response = s3.get_object(Bucket=s3_bucket_name, Key=object_key)
            last_modified_object_contents = response["Body"].read().decode("utf-8")
            if last_modified_object_contents is None:
                raise Exception("Unable to fetch last modified content from s3")
            else:
                return last_modified_object_contents
        except ClientError as exception:
            raise exception

    def delete_object_in_s3_bucket(self, s3_bucket_name, object_key):
        """
        Delete an object from an S3 bucket.

        Args:
            s3_bucket_name (str): The name of the S3 bucket.
            object_key (str): The key of the object to delete.

        """
        try:
            self.aws_session.client("s3").delete_object(
                Bucket=s3_bucket_name, Key=object_key
            )
        except Exception as exception:
            pytest.fail(
                "Error deleting object '%s' from S3 bucket '%s': %s",
                object_key,
                s3_bucket_name,
                exception,
            )

    @staticmethod
    def upload_to_s3(url, payload, file_path):
        """
        Uploads a file to an Amazon S3 bucket using a pre-signed URL.
        """
        files = [("file", ("file", open(file_path, "rb"), "application/octet-stream"))]
        response = requests.request("POST", url, data=payload, files=files)
        return response

    def add_inbound_rule(self, security_group_id: str, source_ip: str):
        """
        Adds an inbound rule to a security group to allow incoming traffic from a specific source IP.
        """
        response = self.ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "-1",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": f"{source_ip}/32"}],
                }
            ],
        )

        if (
            "ResponseMetadata" in response
            and response["ResponseMetadata"]["HTTPStatusCode"] == 200
        ):
            logger.info("Ingress rule authorized successfully.")
        else:
            raise Exception("Failed to authorize ingress rule.")

    def run_ssm_command(self, instance_id: str, command: str):
        """
        Executes an SSM command on a specified EC2 instance.
        """
        try:
            response = self.ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [command]},
            )
            logging.info(f"{command} executed successfully.")
            return response
        except Exception as e:
            raise Exception(
                f"An error {e} occurred while executing the command: {command}"
            )

    def get_instance_id(self):
        """
        Retrieves the AWS EC2 instance ID based on a specific tag value.
        """
        try:
            response = self.ec2_client.describe_instances(
                Filters=[{"Name": "tag:Name", "Values": [SCTE_TEST_INSTANCE_NAME]}]
            )
            if (
                (reservations := response.get("Reservations", []))
                and (instances := reservations[0].get("Instances", []))
                and (instance := instances[0].get("InstanceId"))
            ):
                return instance
            raise Exception("Instance not found")
        except Exception as e:
            raise Exception(f"Error getting the instance details {str(e)}")

    def read_file_from_s3(self, bucket_name: str, file_path: str):
        """
        Reads a JSON file from an Amazon S3 bucket.
        """
        response = self.s3_client.get_object(Bucket=bucket_name, Key=file_path)
        return json.loads(response["Body"].read().decode("utf-8"))

    def fetch_credentials(self, cred_param_path: str):
        credentials = json.loads(self.get_ssm_parameter(cred_param_path))
        if not credentials:
            raise Exception("Unable to fetch credentials.")
        return credentials

    def import_playlist_on_s3(self, s3_bucket_name, file_name, file_path):
        """
        Uploads a file to an Amazon S3 bucket.
        Args:
            s3_bucket_name (str): The name of the S3 bucket where the file will be uploaded.
            file_name (str): The name of the file in the S3 bucket.
            file_path (str): The local file path of the file to be uploaded.
        Returns:
            None
        """

        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    xml = file.read()
            else:
                raise Exception("InvalidFile")
            response = self.aws_session.client("s3").put_object(
                Bucket=s3_bucket_name, Key=file_name, Body=xml
            )
            return response
        except Exception as exception:
            raise exception

    def upload_with_presigned_url(
        self,
        channel_id,
        ws_client,
        FILE_NAME,
        FILE_PATH,
        ENVIRONMENT=None,
    ):
        """
        Upload a playlist file to a remote server using a presigned URL.
         Args:
            self: Remote server to establish HTTP connection.
            channel_id (str): The ID of the channel to which the playlist belongs.
            ws_client: The WebSocket client for communication.
            FILE_NAME: The name of the playlist file.
            FILE_PATH: The local file path of the playlist file.
            ENVIRONMENT: The environment in which the file should be uploaded.
        Returns:
            None
        """
        # Clearing playlist before uploading assets in the playlist
        self.channel_service.clear_playlist(channel_id, ws_client)

        try:
            presigned_response = self.playlist_management.generate_presigned_url(
                FILE_NAME, channel_id
            )
            # Validation on Url generation
            assert (
                presigned_response["status"] == 200
            ), f"Error generating presigned URL. Response status: {presigned_response['status']}."

            # Upload playlist to S3 bucket
            s3_url = presigned_response["output"]["data"]["attributes"]["url"]
            payload = presigned_response["output"]["data"]["attributes"]["fields"]
            if ENVIRONMENT is not None:
                # Use the ENVIRONMENT variable's upload_to_s3 method if it exists
                playlist_upload = ENVIRONMENT.upload_to_s3(
                    s3_url,
                    payload,
                    f"{FILE_PATH}{FILE_NAME}",
                )
            else:
                # Fall back to AwsHelper's upload_to_s3 method
                playlist_upload = AwsHelper.upload_to_s3(
                    s3_url,
                    payload,
                    f"{FILE_PATH}{FILE_NAME}",
                )
            assert (
                playlist_upload.status_code == 204
            ), f"Error uploading playlist to S3. Response status: {playlist_upload.status_code}."

        except Exception as error:  # pylint: disable=broad-except
            logging.info(f"An error occurred during playlist upload: {str(error)}")
            pytest.fail(f"An error occurred during playlist upload: {str(error)}")

    def close(self):
        """
        Close resources and perform cleanup actions.

        This method should be called when done using the AwsHelper instance.
        """
        self.s3_client.close()
        self.ssm_client.close()
