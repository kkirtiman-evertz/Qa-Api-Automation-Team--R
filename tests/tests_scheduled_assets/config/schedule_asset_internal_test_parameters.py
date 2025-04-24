"""It contains configurations and dependencies for testing schedule asset feature"""

import pytest

from tests.tests_scheduled_assets.config.schedule_asset_internal_config import (
    ASSET_ID,
    TestParameters,
    TestParametersForChannels,
)

ParameterSets = [
    pytest.param(
        TestParameters(
            1,
            400,
            "Parameter 'pageSize' is expected in range [1, 40]",
            ASSET_ID,
            "1",
            "41",
        ),
        id="Error-invalid_page_parameters",
    ),
    pytest.param(
        TestParameters(2, 200, 0, "Test_01", "1", "10"),
        id="Error-invalid_asset_id",
    ),
    pytest.param(
        TestParameters(3, 400, "DEFAULT_4XX", "", "", ""),
        id="Error-Passing_empty_string",
    ),
]
ParameterSets_for_channels = [
    pytest.param(
        TestParametersForChannels(1, 400, "BAD_REQUEST_PARAMETERS", "", "", "", ""),
        id="Error-Passing_empty_string_for_channels",
    ),
    pytest.param(
        TestParametersForChannels(2, 200, 0, "Test_01", "", "1", "10"),
        id="Error-invalid_asset_id_for_channels",
    ),
    pytest.param(
        TestParametersForChannels(
            3,
            400,
            "Parameter 'pageSize' is expected in range [1, 40]",
            ASSET_ID,
            "",
            "1",
            "41",
        ),
        id="Error-invalid_page_parameters_for_channels",
    ),
]
