import json
import logging
import os
import sys
from datetime import datetime
from sys import platform

import pytest
import yaml

from utils.aws_helper import AwsHelper
from utils.eio.channel_controller import (
    create_channel_with_default_config,
    create_receiver_channel,
    create_source_channel,
    delete_channels,
    turn_off_channels,
    turn_on_channels,
)
from utils.eio.clients.httpclient import EIOHttpClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


@pytest.fixture(scope="session")
def config_data():
    try:
        config_file_name = os.environ.get("config")
        logger.info(f"Config file name: {config_file_name}")

        with open(config_file_name, "r") as config_file:
            config_data = yaml.safe_load(config_file)
            logger.info(f"Loaded config file info: {config_data}")
            return config_data
    except Exception as e:
        logger.error(f"Error loading config file: {str(e)}")
        pytest.fail("Unable to load config data. Aborting tests.")


@pytest.fixture(scope="session")
def current_environment(config_data):
    region = config_data.get("region") or "us-east-1"
    env = config_data.get("env") or "dev"

    environment = {
        "server": f"https://{region}.{env}.api.evertz.io/",
        "ws_server": f"{region}.{env}.api.evertz.io",
        "tenant": config_data.get("tenantId") or "63a61456-ead0-4a87-8902-5ab5de617ee3",
        "channel_id": config_data.get("channelId"),
        "config_user": config_data.get("userName"),
        "config_password": config_data.get("password"),
        "aws_profile_eio_dev": f"eio-{env}",
        "aws_profile_mock_cust_access": "EvertzIOMockCustomerAccess",
        "cred_param_path": f"/account/credentials/playout-api-automation-tests/build-test/{env}/root",
    }
    return environment


@pytest.fixture(scope="session")
def aws_helper_eio_dev(current_environment):
    helper = None
    try:
        helper = AwsHelper(current_environment["aws_profile_eio_dev"])
        yield helper
    except Exception as e:
        logger.error(f"Error creating AWS helper utility: {str(e)}")
        pytest.fail("Unable to create AWS helper utility. Aborting tests.")
    finally:
        if helper:
            helper.close()


@pytest.fixture(scope="session")
def aws_helper_mock_cust_access(current_environment):
    helper = None
    try:
        helper = AwsHelper(current_environment["aws_profile_mock_cust_access"])
        yield helper
    except Exception as e:
        logger.error(f"Error creating AWS helper utility: {str(e)}")
        pytest.fail("Unable to create AWS helper utility. Aborting tests.")
    finally:
        if helper:
            helper.close()


def _get_credentials(current_environment, aws_helper_eio_dev):
    """
    Retrieves the credentials for the current environment.

    First, it checks if 'config_user' and 'config_password' are available in the current environment.
    If not, it attempts to retrieve the credentials from AWS SSM using the 'cred_param_path'.

    Args:
        current_environment (dict): The dictionary containing the current environment configuration.
        aws_helper_eio_dev (AwsHelper): An instance of the AWS Helper class for interacting with AWS services for eio-dev profile.

    Returns:
        Tuple[str, str]: A tuple containing the username and password for authentication.

    Raises:
        Exception: If any errors occur during credential retrieval.

    Note:
        This function ensures that valid credentials are obtained for tests to run successfully.
    """
    if current_environment["config_user"] and current_environment["config_password"]:
        return (
            current_environment["config_user"],
            current_environment["config_password"],
        )
    try:
        json_data = aws_helper_eio_dev.get_ssm_parameter(
            current_environment["cred_param_path"]
        )

        credentials = json.loads(json_data)

        cred_user = credentials.get("username")
        cred_password = credentials.get("password")

        return cred_user, cred_password
    except Exception as e:
        logger.error(f"Error retrieving credentials: {e}")
        pytest.fail("Unable to retrieve credentials. Aborting tests.")


def create_and_turn_on_channels(current_environment, client):
    if len(sys.argv) == 1 or sys.argv[2] == "all" or "channel_service" in sys.argv[2]:
        channel_creation_functions = {
            "channel_id_source": create_source_channel,
            "channel_id_receiver": create_receiver_channel,
        }
        if current_environment["channel_id"] is None:
            channel_creation_functions.update(
                {"channel_id": create_channel_with_default_config}
            )
        for channel_type, creation_function in channel_creation_functions.items():
            current_environment[f"{channel_type}"] = creation_function(client)

        # Turn on all channels
        channels_to_turn_on = [
            current_environment["channel_id"],
            current_environment["channel_id_source"],
            current_environment["channel_id_receiver"],
        ]
        turn_on_channels(client, channels_to_turn_on)
    elif "scte_taker" in sys.argv[2]:
        channel_creation_functions = {
            "channel_id_source": create_source_channel,
            "channel_id_receiver": create_receiver_channel,
        }
        for channel_type, creation_function in channel_creation_functions.items():
            current_environment[f"{channel_type}"] = creation_function(client)

        # Turn on all channels
        channels_to_turn_on = [
            current_environment["channel_id_source"],
            current_environment["channel_id_receiver"],
        ]
        turn_on_channels(client, channels_to_turn_on)

    else:
        if current_environment["channel_id"] is None:
            current_environment["channel_id"] = create_channel_with_default_config(
                client
            )
        # Turn on all channels
        channels_to_turn_on = [current_environment["channel_id"]]
        turn_on_channels(client, channels_to_turn_on)


@pytest.fixture(scope="session")
def eio_client(current_environment, aws_helper_eio_dev):
    client = None
    try:
        logging.info(f"Current configured environment info: {current_environment}")

        cred_user, cred_password = _get_credentials(
            current_environment, aws_helper_eio_dev
        )

        client = EIOHttpClient(
            current_environment["server"],
            current_environment["ws_server"],
            current_environment["tenant"],
            cred_user,
            cred_password,
        )

        client.signin()
        create_and_turn_on_channels(current_environment, client)

        yield client
    except Exception as e:
        logging.error(f"Error creating EIO client: {str(e)}")
        pytest.fail("Unable to create EIO client. Aborting tests.")
    finally:
        if client:
            client.close()


@pytest.fixture(scope="session")
def scte_channel_setup(eio_client, current_environment):
    """
    Fixture to set up the SCTE channel for the session.

    Args:
        eio_client: The EIO client instance used to interact with the services.
        current_environment: A dictionary containing the current environment configuration.
    """
    eio_client.channel_service_scte_taker.channel_setup(
        eio_client, current_environment["channel_id_source"]
    )


@pytest.fixture(scope="session", autouse=True)
def teardown_channel(eio_client, current_environment):
    yield

    channel_ids = [
        value
        for key, value in current_environment.items()
        if key.startswith("channel_id") and value is not None
    ]
    eio_client.channel_service_scte_taker.deactivate_source(eio_client)
    turn_off_channels(eio_client, channel_ids)
    delete_channels(eio_client, channel_ids)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    The hook function will determine the system platform and generates HTML report with current timestamp at specified location.
    """
    report_dir = _get_report_directory()
    config.option.htmlpath = os.path.join(
        report_dir, f"EIO_reports_{_get_timestamp()}.html"
    )


def _get_report_directory():
    if platform == "win32":
        return "C:\\EIO_reports"
    else:
        return "/tmp"


def _get_timestamp():
    return datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
