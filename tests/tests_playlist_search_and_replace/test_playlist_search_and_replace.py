"""Importing necessary modules for logging,time,pytest and UUIDs """

import logging
import time
import uuid

import pytest

from tests.tests_playlist_search_and_replace.config.playlist_search_and_replace_config import (
    ASSET_ID,
    CLIENT_ID,
    CURSOR,
    EVENT_SIZE,
    MAX_WAIT_TIME,
    REPLACE_ASSET_ID,
    SCHEDULE_FILE_NAME_PXF,
    SCHEDULE_FILE_PATH,
    SEQUENCE_ID,
)
from utils.aws_helper import AwsHelper
from utils.eio.clients.httpclient import EIOHttpClient


class TestPlaylistSearchAndReplace:
    """
    Testing Playlist Search and Replace features under different circumstances.
    """

    # pylint: disable=duplicate-code
    def test_playlist_search_using_asset_id(self, eio_client, current_environment):
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

        try:
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
            )
            output = eio_client.playlist_search_replace.playlist_search_by_assetId(
                value=ASSET_ID,
                op="eq",
                field="any-asset-id",
                page_size=2,
                channel_id=channel_id,
            )
            total_count_of_asset = output["output"]["meta"]["totalCount"]
            data = output["output"]["data"]
            # Checking if there is next link in the response.
            assert output["output"]["links"] is not None
            while "next" in output["output"]["links"]:
                cursor = output["output"]["links"]["next"]["meta"]["cursor"]

                output = eio_client.playlist_search_replace.playlist_search_by_assetId(
                    value=ASSET_ID,
                    op="eq",
                    field="any-asset-id",
                    page_size=2,
                    page_after=cursor,
                    channel_id=channel_id,
                )
                data += output["output"]["data"]
            assert total_count_of_asset == len(data)
            for count in range(total_count_of_asset):
                assert data[count]["id"].startswith("sequence$")
                assert data[count]["type"] == "playlist-search-result"
                assert data[count]["attributes"]["startMode"] in (
                    "FIXED",
                    "MANUAL",
                    "VARIABLE",
                )
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

        eio_client.channel_service.clear_playlist(channel_id, ws_client)
        logging.info("Playlist clear successfully")
        time.sleep(2)
        eio_client.close()

    def test_replace_call_in_playlist(self, eio_client, current_environment):
        """
        Test case for replace few assets in a playlist using sequence id.
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
        # Replace Item with search event
        output = eio_client.playlist_search_replace.playlist_search_by_assetId(
            value=ASSET_ID,
            op="eq",
            field="any-asset-id",
            page_size=2,
            channel_id=channel_id,
        )
        sequence_id_for_replace = output["output"]["meta"]["allSequenceIds"][:2]

        try:
            replace_selected_data = (
                eio_client.playlist_search_replace.replace_searched_item(
                    ws_client,
                    str(uuid.uuid4()),
                    ASSET_ID,
                    REPLACE_ASSET_ID,
                    sequence_id_for_replace,
                    channel_id,
                )
            )
            assert replace_selected_data["method"] == "replaceItems"
            if "error" in replace_selected_data["result"]:
                pytest.fail("Error: Failed to replace the items")
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

    # invalid Scenarios for search call
    @pytest.mark.parametrize(
        "page_size, op, field",
        [
            (100, "eq", "any-asset-id"),
            (1, "test", "any-asset-id"),
            (1, "eq", "test"),
        ],
    )
    # pylint: disable=too-many-arguments,invalid-name
    def test_invalid_page_parameter(
        self,
        page_size,
        op,
        field,
        eio_client: EIOHttpClient,
        current_environment,
    ):
        """
        Test case for searching a playlist by invalid page parameters and
         check whether the response are expected or not.
        Args:
            page_size: Defining a page_size.
            op: Defining op parameter.
            field: Defining  field parameter.
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
            current_environment (dict): The currently used regions.

        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        channel_id = current_environment["channel_id"]

        output = eio_client.playlist_search_replace.playlist_search_by_assetId(
            page_size=page_size, op=op, field=field, channel_id=channel_id
        )
        assert output["status"] == 400
        assert output["output"]["errors"][0]["code"] == "InvalidInput"
        assert (
            output["output"]["errors"][0]["detail"] == "Invalid format for request body"
        )

    # pylint: disable=too-many-arguments
    @pytest.mark.parametrize(
        "cursor, status, expected_result, detail",
        [
            (
                CURSOR,
                500,
                "UnexpectedError",
                "An unexpected error has occurred "
                "please contact support for more details.",
            ),
            ("1", 400, "InvalidCursor", "Unable to fetch next results"),
            (1, 400, "InvalidCursor", "Unable to fetch next results"),
            (-1, 400, "InvalidCursor", "Invalid version [-] for cursor"),
        ],
    )
    def test_invalid_cursor(
        self,
        cursor,
        status,
        expected_result,
        detail,
        eio_client: EIOHttpClient,
        current_environment,
    ):
        """
        Test case for searching a playlist by pass invalid cursor.
        Args:
            cursor: Defining cursor to test.
            status: Expected status.
            expected_result: Expected result what we will be expecting in output.
            detail: Expected detail what we will be expecting in output.
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
            current_environment (dict): The currently used regions.

        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        channel_id = current_environment["channel_id"]

        output = eio_client.playlist_search_replace.playlist_search_by_assetId(
            page_size=1,
            page_after=cursor,
            op="eq",
            field="any-asset-id",
            value=ASSET_ID,
            channel_id=channel_id,
        )
        assert output["status"] == status
        assert output["output"]["errors"][0]["code"] == expected_result
        assert output["output"]["errors"][0]["detail"] == detail

    def test_invalid_channel_id(self, eio_client: EIOHttpClient):
        """
        Test case for searching a playlist by passing invalid value in channel_id.
        Args:
            eio_client (EIOHttpClient): An instance of EIOHttpClient used for credentials.
        Raises:
            Any exceptions that might occur during the test.

        Returns:
            None
        """
        output = eio_client.playlist_search_replace.playlist_search_by_assetId(
            page_size=1,
            op="eq",
            field="any-asset-id",
            value=ASSET_ID,
            channel_id="123232jfbdb3223hfb13h4ddsh",
        )
        assert output["status"] == 404
        assert output["output"]["errors"][0]["code"] == "ChannelNotFound"
        assert output["output"]["errors"][0]["detail"] == "Channel Not Found"

    # invalid Scenarios for replace call
    def test_invalid_asset_id_(self, eio_client: EIOHttpClient, current_environment):
        """
        Test case for searching a playlist by passing invalid or incorrect asset id.
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
        output = eio_client.playlist_search_replace.replace_searched_item(
            ws_client,
            str(uuid.uuid4()),
            "Test_search",
            REPLACE_ASSET_ID,
            SEQUENCE_ID,
            channel_id,
        )
        assert output["method"] == "replaceItems"
        assert output["result"]["error"]["code"] == 3400
        assert output["result"]["error"]["message"] == "Failed to Replace [1] items."

        eio_client.close()

    def test_same_asset_id_(self, eio_client: EIOHttpClient, current_environment):
        """
        Test case for searching a playlist by passing same asset_id.
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

        output = eio_client.playlist_search_replace.replace_searched_item(
            ws_client, str(uuid.uuid4()), ASSET_ID, ASSET_ID, SEQUENCE_ID, channel_id
        )
        assert output["method"] == "replaceItems"
        assert output["result"]["error"]["code"] == 1000
        assert (
            output["result"]["error"]["message"]
            == "Api [replaceItems] received invalid input "
            "[ChannelServiceException: Item already has the same AssetId]"
        )
        eio_client.close()

    def test_invalid_for_replacing_on_air_event(
        self, eio_client: EIOHttpClient, current_environment
    ):
        """
        Test case for replacing an on-air event.
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
        eio_client.channel_service.insert_sequence(
            channel_id, "variable", "Program", "COMMHUG", ws_client
        )
        output = eio_client.playlist_search_replace.playlist_search_by_assetId(
            value="COMMHUG",
            op="eq",
            field="any-asset-id",
            page_size=5,
            channel_id=channel_id,
        )
        sequence_id_for_replace = output["output"]["meta"]["allSequenceIds"][:1]
        eio_client.channel_service.control_playlist(channel_id, ws_client, "take")
        time.sleep(2)
        item_detail = eio_client.channel_service.get_item_details(
            channel_id, ws_client, sequence_id_for_replace[0]
        )
        assert item_detail["output"]["item"]["timing"]["state"] == "now"
        replace_selected_data = (
            eio_client.playlist_search_replace.replace_searched_item(
                ws_client,
                str(uuid.uuid4()),
                "COMMHUG",
                ASSET_ID,
                sequence_id_for_replace,
                channel_id,
            )
        )
        assert replace_selected_data["method"] == "replaceItems"
        assert replace_selected_data["result"]["error"]["code"] == 3400
        assert (
            replace_selected_data["result"]["error"]["data"][
                sequence_id_for_replace[0]
            ]["message"]
            == "Cannot replace item in now state"
        )
        assert (
            replace_selected_data["result"]["error"]["data"][
                sequence_id_for_replace[0]
            ]["severity"]
            == "error"
        )
        assert (
            replace_selected_data["result"]["error"]["data"][
                sequence_id_for_replace[0]
            ]["data"]["sequenceState"]
            == "now"
        )
        eio_client.close()

    def test_invalid_for_replacing_played_out_event_(
        self, eio_client: EIOHttpClient, current_environment
    ):
        """
        Test case for replacing a passed event.
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
        eio_client.channel_service.insert_sequence(
            channel_id, "variable", "Program", "COMMHUG", ws_client
        )
        output = eio_client.playlist_search_replace.playlist_search_by_assetId(
            value="COMMHUG",
            op="eq",
            field="any-asset-id",
            page_size=5,
            channel_id=channel_id,
        )
        sequence_id_for_replace = output["output"]["meta"]["allSequenceIds"][:1]
        eio_client.channel_service.control_playlist(channel_id, ws_client, "take")
        time.sleep(17)

        item_detail = eio_client.channel_service.get_item_details(
            channel_id, ws_client, sequence_id_for_replace[0]
        )
        assert item_detail["output"]["item"]["timing"]["state"] == "done"
        replace_selected_data = (
            eio_client.playlist_search_replace.replace_searched_item(
                ws_client,
                str(uuid.uuid4()),
                "COMMHUG",
                ASSET_ID,
                sequence_id_for_replace,
                channel_id,
            )
        )
        assert replace_selected_data["method"] == "replaceItems"
        assert replace_selected_data["result"]["error"]["code"] == 3400
        assert (
            replace_selected_data["result"]["error"]["data"][
                sequence_id_for_replace[0]
            ]["message"]
            == "Cannot replace item in done state"
        )
        assert (
            replace_selected_data["result"]["error"]["data"][
                sequence_id_for_replace[0]
            ]["severity"]
            == "error"
        )
        assert (
            replace_selected_data["result"]["error"]["data"][
                sequence_id_for_replace[0]
            ]["data"]["sequenceState"]
            == "done"
        )
        eio_client.channel_service.clear_playlist(channel_id, ws_client)
        eio_client.close()
