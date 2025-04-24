"""Importing necessary modules for logging,time and pytest"""

import logging
import time
import uuid

import pytest

from tests.tests_scheduled_assets.config.schedule_asset_internal_config import (
    ASSET_ID,
    CLIENT_ID,
    EVENT_SIZE,
    MAX_WAIT_TIME,
    SCHEDULE_FILE_NAME_PXF,
    SCHEDULE_FILE_PATH,
    TestParameters,
    TestParametersForChannels,
    regex_pattern_for_start_date_time,
)
from tests.tests_scheduled_assets.config.schedule_asset_internal_test_parameters import (
    ParameterSets,
    ParameterSets_for_channels,
)
from utils.aws_helper import AwsHelper
from utils.eio.clients.httpclient import EIOHttpClient


class TestInternalScheduleAssetsPanel:
    """Defining test cases to check schedule asset feature under different conditions"""

    # pylint: disable=too-many-locals
    def test_get_asset_detail(self, eio_client: EIOHttpClient, current_environment):
        """
        Test case for searching assets in a playlist using asset id.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
            current_environment (dict): The currently used regions.

        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        client_id = str(uuid.uuid4())
        channel_id = current_environment["channel_id"]
        ws_client = eio_client.get_ws_client(client_id)

        # Upload playlist and wait for import
        AwsHelper.upload_with_presigned_url(
            eio_client,
            channel_id,
            ws_client,
            SCHEDULE_FILE_NAME_PXF,
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
        channel_data = eio_client.channel_management.get_channel_by_id(channel_id)
        try:
            output = eio_client.schedule_asset_internal_service.get_asset_detail(
                ASSET_ID
            )

            # Storing the total count of the channel on which asset is scheduled.
            total_count_schedule_on = output["output"]["meta"]["totalCount"]
            # Creating a dictionary to store channel name and channel id.
            my_dict = {}
            for length in range(total_count_schedule_on):
                assert output["output"]["data"][length]["attributes"]["isHolding"] in [
                    True,
                    False,
                ], (
                    f"Attributes should be either 'True' or 'False'."
                    f"but got: {output['output']['data'][length]['attributes']['isHolding']}"
                )
                assert (
                    output["output"]["data"][length]["attributes"]["count"] > 0
                ), "Count should be more than zero."
                assert (
                    output["output"]["data"][length]["type"]
                    == "scheduled-asset-summary"
                ), (
                    f"Expected type '{'scheduled-asset-summary'}' "
                    f"but got: {output['output']['data'][length]['type']}"
                )
                sequence_id = output["output"]["data"][length]["attributes"][
                    "firstSequence"
                ]["sequenceId"]
                assert sequence_id.startswith(
                    "sequence$"
                ), f"Asset at index {length} does not have an 'id' starting with 'sequence$'."
                start_date_time = output["output"]["data"][length]["attributes"][
                    "firstSequence"
                ]["startDateTime"]
                if not isinstance(start_date_time, str):
                    start_date_time = str(start_date_time)
                assert regex_pattern_for_start_date_time.match(
                    start_date_time
                ), "start_date_time doesn't match the pattern."
                channel = output["output"]["data"][length]["attributes"][
                    "channelDisplayName"
                ]
                _id = output["output"]["data"][length]["id"]
                my_dict[channel] = _id
            assert channel_id in my_dict.values()
            assert (
                channel_data["output"]["data"]["attributes"]["metadata"]["displayName"]
                in my_dict
            ), "DisplayName not found in the dictionary keys."
            assert (
                channel_data["output"]["data"]["attributes"]["metadata"]["id"]
                in my_dict.values()
            ), "ID not found in the dictionary values."

            logging.info("List of channels on which asset %s is scheduled", ASSET_ID)

            for key, value in my_dict.items():
                logging.info(f"{key}: {value}")
        except (
            KeyError,
            IndexError,
            ValueError,
        ) as error:
            logging.error(f"{type(error).__name__} during test execution: {str(error)}")
            pytest.fail(f"Test failed due to a {type(error).__name__}: {str(error)}")

        except Exception as exception:  # pylint: disable=broad-except
            logging.error(
                f"Unexpected exception during test execution: {str(exception)}"
            )
            pytest.fail(f"Test failed due to an unexpected exception: {str(exception)}")
        finally:
            eio_client.close()

    def test_get_channel_and_asset_detail(
        self, eio_client: EIOHttpClient, current_environment
    ):
        """
        Test case for Checking for asset in a playlist using asset id.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
            current_environment (dict): The currently used regions.

        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        channel_id = current_environment["channel_id"]
        page = 1
        try:
            # finding the asset detail on a particular channel.
            output = eio_client.schedule_asset_internal_service.get_asset_with_channel_detail(
                channel_id, ASSET_ID, page=page
            )
            data = output["output"]["data"]
            title = data[0]["attributes"]["title"]
            total_count_schedule_on = output["output"]["meta"]["totalCount"]
            # Checking if there is next link in the response.
            assert (
                output["output"]["links"] is not None
            ), "Link is not present in the response."
            while "next" in output["output"]["links"]:
                page += 1
                output = eio_client.schedule_asset_internal_service.get_asset_with_channel_detail(
                    channel_id, ASSET_ID, page=page
                )
                data += output["output"]["data"]
            assert (
                len(data) == total_count_schedule_on
            ), f"Expected {len(data)}, but got: {total_count_schedule_on}"
            for length in range(total_count_schedule_on):
                assert (
                    data[length]["attributes"]["title"] == title
                ), f"Expected {title}, but got: {data[length]['attributes']['title']}"
                assert data[length]["id"].startswith(
                    "sequence$"
                ), f"Asset at index {length} does not have an 'id' starting with 'sequence$'."
                start_date_time = data[length]["attributes"]["startDateTime"]
                if not isinstance(start_date_time, str):
                    start_date_time = str(start_date_time)
                assert regex_pattern_for_start_date_time.match(
                    start_date_time
                ), "start_date_time doesn't match the pattern."
        except (
            KeyError,
            IndexError,
            ValueError,
        ) as error:
            logging.error(f"{type(error).__name__} during test execution: {str(error)}")
            pytest.fail(f"Test failed due to a {type(error).__name__}: {str(error)}")

        except Exception as exception:  # pylint: disable=broad-except
            logging.error(
                f"Unexpected exception during test execution: {str(exception)}"
            )
            pytest.fail(f"Test failed due to an unexpected exception: {str(exception)}")
        finally:
            eio_client.close()

    @pytest.mark.parametrize("test_params", ParameterSets)
    def test_invalid_schedule_asset_search_with_asset_id(
        self, eio_client: EIOHttpClient, test_params: TestParameters
    ):
        """
        Test case for Checking for invalid asset and invalid page parameter.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
            test_params (TestParameters): Parameter set for the test.

        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """

        output = eio_client.schedule_asset_internal_service.get_asset_detail(
            test_params.asset_id, test_params.page, test_params.pageSize
        )
        if test_params.test_number == 1:
            assert (
                output["status"] == test_params.status
            ), f"Expected {test_params.status}, but got: {output['status']}"
            assert output["output"]["errors"][0]["detail"] == test_params.details, (
                f"Expected {test_params.details},"
                f" but got: {output['output']['errors'][0]['detail']}"
            )
        elif test_params.test_number == 2:
            assert (
                output["status"] == test_params.status
            ), f"Expected {test_params.status}, but got: {output['status']}"
            assert output["output"]["meta"]["totalCount"] == test_params.details, (
                f"Expected total count as {test_params.details},"
                f" but got: {output['output']['meta']['totalCount']}"
            )
        elif test_params.test_number == 3:
            assert (
                output["status"] == test_params.status
            ), f"Expected {test_params.status}, but got: {output['status']}"
            assert (
                output["output"]["errors"][0]["code"] == test_params.details
            ), f"Expected {test_params.details}, but got: {output['output']['errors'][0]['code']}"

    @pytest.mark.parametrize("test_params", ParameterSets_for_channels)
    def test_invalid_schedule_asset_search_with_channel_id(
        self,
        eio_client: EIOHttpClient,
        current_environment,
        test_params: TestParametersForChannels,
    ):
        """
        Test case for Checking for invalid channel_id,asset_id and parameters.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
            current_environment (dict): The currently used regions.

        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        channel_id = current_environment["channel_id"]
        output = (
            eio_client.schedule_asset_internal_service.get_asset_with_channel_detail(
                channel_id, test_params.asset_id, test_params.page, test_params.pageSize
            )
        )
        if test_params.test_number == 1:
            assert (
                output["status"] == test_params.status
            ), f"Expected {test_params.status}, but got: {output['status']}"
            assert (
                output["output"]["errors"][0]["code"] == test_params.details
            ), f"Expected {test_params.details}, but got: {output['output']['errors'][0]['code']}"
        elif test_params.test_number == 2:
            assert (
                output["status"] == test_params.status
            ), f"Expected {test_params.status}, but got: {output['status']}"
            assert output["output"]["meta"]["totalCount"] == test_params.details, (
                f"Expected total count as {test_params.details},"
                f"but got: {output['output']['meta']['totalCount']}"
            )
        elif test_params.test_number == 3:
            assert (
                output["status"] == test_params.status
            ), f"Expected {test_params.status}, but got: {output['status']}"
            assert output["output"]["errors"][0]["detail"] == test_params.details, (
                f"Expected {test_params.details},"
                f" but got: {output['output']['errors'][0]['detail']}"
            )

    def test_invalid_channel_id(self, eio_client: EIOHttpClient):
        """
        Test case for Checking for invalid channel_id,asset_id and parameters.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        output = (
            eio_client.schedule_asset_internal_service.get_asset_with_channel_detail(
                channel_id=12312312, asset_id=ASSET_ID, page=1, pageSize=10
            )
        )
        assert output["status"] == 404, f"Expected {404}, but got: {output['status']}"
        assert (
            output["output"]["errors"][0]["code"] == "ChannelNotFound"
        ), f"Expected {'ChannelNotFound'}, but got: {output['output']['errors'][0]['code']}"

    def test_after_clearing_the_playlist(
        self, eio_client: EIOHttpClient, current_environment
    ):
        """
        Test case for Checking after clearing the playlist.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
            current_environment (dict): The currently used regions.

        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        channel_id = current_environment["channel_id"]
        ws_client = eio_client.get_ws_client(CLIENT_ID)
        eio_client.channel_service.clear_playlist(channel_id, ws_client)
        time.sleep(2)
        output = (
            eio_client.schedule_asset_internal_service.get_asset_with_channel_detail(
                ASSET_ID, channel_id
            )
        )
        assert output["status"] == 404, f"Expected {404}, but got: {output['status']}"
        assert (
            output["output"]["errors"][0]["detail"]
            == "Channel with Id: BIG_BUCK_BUNNY_DF30 not found"
        ), (
            f"Expected {'Channel with Id: BIG_BUCK_BUNNY_DF30 not found'},"
            f" but got: {output['output']['errors'][0]['detail']}"
        )
        eio_client.close()
