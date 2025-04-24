"""
Module Docstring: E2E for Schedule asset external api.
"""

import pytest

from conftest import logger
from tests.tests_scheduled_assets.config.schedule_asset_configuration import (
    ASSET_ID,
    CLIENT_ID,
    EVENT_SIZE,
    MAX_WAIT_TIME,
)
from tests.tests_scheduled_assets.config.schedule_asset_configuration import (
    PAGE as config_page,
)
from tests.tests_scheduled_assets.config.schedule_asset_configuration import (
    PAGE_SIZE,
    REGEX_PATTERN_FOR_START_DATE_TIME,
    SCHEDULE_EXTERNAL_FILE_NAME_PXF,
    SCHEDULE_FILE_PATH,
)
from utils.aws_helper import AwsHelper
from utils.eio.clients.httpclient import EIOHttpClient


class TestScheduleAssetExternalAPI:
    """
    Class Docstring: E2E for Schedule asset external API.
    """

    # pylint: disable=duplicate-code
    def test_get_channels_where_asset_scheduled_on(
        self, eio_client, current_environment
    ):
        """
        Test to Get the list of channels that an asset is scheduled on.
        Args:
           eio_client: Remote server to establish HTTP connection.
           current_environment: Environment to get channel id
        """
        try:
            channel_id = current_environment["channel_id"]
            ws_client = eio_client.get_ws_client(CLIENT_ID)

            # Upload playlist and wait for import
            AwsHelper.upload_with_presigned_url(
                eio_client,
                channel_id,
                ws_client,
                SCHEDULE_EXTERNAL_FILE_NAME_PXF,
                SCHEDULE_FILE_PATH,
            )

            # wait_for_playlist_import method
            eio_client.playlist_management.wait_for_playlist_import(
                eio_client,
                channel_id,
                ws_client,
                EVENT_SIZE,
                MAX_WAIT_TIME,
            )  # pylint: disable=duplicate-code

            output = eio_client.schedule_asset_external.get_channels_where_asset_scheduled_on(
                ASSET_ID
            )

            total_channels_scheduled_on_asset = output["output"]["meta"]["totalCount"]
            channel_ids = [item["id"] for item in output["output"]["data"]]

            for index in range(total_channels_scheduled_on_asset):
                assert (
                    output["output"]["data"][index]["relationships"][
                        "scheduledInstance"
                    ]["meta"]["count"]
                    > 0
                ), "Count for number of time asset is scheduled on is not greater than 0"
                assert (
                    output["output"]["data"][index]["type"] == "channels"
                ), "Custom error message: Unexpected type"
                channel = output["output"]["data"][index]["attributes"]["displayName"]
                _id = output["output"]["data"][index]["id"]
                logger.info("Asset is scheduled on-%s: %s", channel, _id)

            # Checking if given channel id which we are using to
            # upload assets is present in the channel id list
            assert (
                channel_id in channel_ids
            ), f"Provided channel ID {channel_id} not found in channel IDs"

        except (FileNotFoundError, KeyError, IndexError, ValueError) as error:
            logger.error(f"An error occurred: {error}.")
            pytest.fail(f"Error occurred: {error}")
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"An unexpected error occurred: {error}.")
            pytest.fail(f"An unexpected error occurred: {error}")

    def test_get_timings_when_asset_scheduled_on(
        self, eio_client: EIOHttpClient, current_environment
    ):
        """This tests gets the times that an asset is scheduled on a channel"""
        try:
            channel_id = current_environment["channel_id"]
            page = config_page
            output = (
                eio_client.schedule_asset_external.get_timings_when_asset_scheduled_on(
                    ASSET_ID, channel_id, page=page
                )
            )

            assert (
                output["status"] == 200
            ), "Custom error message: Unexpected status code in output"
            assert (
                output["output"]["meta"]["totalCount"] > 0
            ), "Custom error message: No data found"

            data = output["output"]["data"]
            total_count_schedule_on = output["output"]["meta"]["totalCount"]

            assert (
                total_count_schedule_on == 5
            ), "The total count doesn't match the expected number of scheduled items"

            # Checking if there is a next link in the response.
            if "links" in output["output"]:
                while "next" in output["output"]["links"]:
                    page += 1
                    output = eio_client.schedule_asset_external.get_timings_when_asset_scheduled_on(
                        ASSET_ID, channel_id, page=page
                    )
                    data += output["output"]["data"]

            assert (
                len(data) == total_count_schedule_on
            ), "Custom error message: Data length does not match the total count"

            for index in range(total_count_schedule_on):
                # Asserting sequenceId from output
                assert data[index]["id"].startswith(
                    "sequence$"
                ), "Custom error message: Invalid sequenceId"

                # Check startDateTime pattern is valid or not from output
                start_date_time = str(data[index]["attributes"]["startDateTime"])
                assert REGEX_PATTERN_FOR_START_DATE_TIME.match(
                    start_date_time
                ), "Custom error message: Invalid startDateTime pattern"

                assert (
                    output["output"]["data"][index]["type"] == "scheduled-instances"
                ), "Custom error message: Unexpected type"

        except (KeyError, IndexError) as error:
            logger.error(f"An error occurred: {error}.")
            pytest.fail(f"Error occurred: {error}")
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"An unexpected error occurred: {error}.")
            pytest.fail(f"An unexpected error occurred: {error}")

    @pytest.mark.parametrize(
        "asset_id, page, page_size, expected_result",
        [
            ("", config_page, PAGE_SIZE, "BAD_REQUEST_PARAMETERS"),
            (ASSET_ID, config_page, 24, "InvalidInput"),
            (ASSET_ID, "&&&***", PAGE_SIZE, "InvalidInput"),
        ],
    )
    # pylint: disable=too-many-arguments
    def test_scheduled_asset_with_invalid_values(
        self, eio_client: EIOHttpClient, asset_id, page, page_size, expected_result
    ):
        """
        This Test covers negative scenarios for Api call-Get to Get the list of channels,
        that an asset is scheduled on a channel using invalid values
        @param asset_id, page, page_size: List of parameters that we will be using in the test.
        """
        # Make the API call
        output = (
            eio_client.schedule_asset_external.get_channels_where_asset_scheduled_on(
                asset_id, page, page_size
            )
        )

        # error message or relevant part of the response for comparison
        error_message = output["output"]["errors"][0]["code"]

        assert (
            error_message == expected_result
        ), f"Expected: {expected_result}, Actual: {error_message}"

    @pytest.mark.parametrize(
        "asset_id, channel_id, page, pagesize, expected_result",
        [
            ("", "default", config_page, PAGE_SIZE, "BAD_REQUEST_PARAMETERS"),
            (ASSET_ID, 83985, config_page, PAGE_SIZE, "ChannelNotFound"),
            (ASSET_ID, "default", config_page, 41, "InvalidInput"),
            (ASSET_ID, "default", "&&&***", PAGE_SIZE, "InvalidInput"),
        ],
    )
    # pylint: disable=too-many-arguments
    def test_scheduled_asset_timings_with_invalid_values(
        self,
        eio_client: EIOHttpClient,
        asset_id,
        channel_id,
        page,
        pagesize,
        expected_result,
        current_environment,
    ):
        """
        This Test covers negative scenarios for Api-Get the timings,
        that an asset is scheduled on a channel
        @param asset_id, channel_id, page, pagesize, and
        expected_result : List of parameters that we will be using in the test.
        """
        if channel_id == "default":
            channel_id = current_environment["channel_id"]

        # Make the API call
        output = eio_client.schedule_asset_external.get_timings_when_asset_scheduled_on(
            asset_id, channel_id, page, pagesize
        )

        # error message or relevant part of the response for comparison
        error_message = output["output"]["errors"][0]["code"]

        assert (
            error_message == expected_result
        ), f"Expected: {expected_result}, Actual: {error_message}"
