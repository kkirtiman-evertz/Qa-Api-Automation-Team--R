"""It contains configurations and dependencies for testing schedule asset feature"""

import re
import uuid
from collections import namedtuple

SCHEDULE_FILE_NAME_PXF = "scheduled_assets_internal.pxf"
SCHEDULE_FILE_PATH = "tests/tests_scheduled_assets/resources/"
CLIENT_ID = str(uuid.uuid4())
ASSET_ID = "BIG_BUCK_BUNNY_DF30"
EVENT_SIZE = 100
MAX_WAIT_TIME = 30  # Maximum wait time in seconds
regex_pattern_for_start_date_time = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*")
TestParameters = namedtuple(
    "TestParameters",
    ["test_number", "status", "details", "asset_id", "page", "pageSize"],
)
TestParametersForChannels = namedtuple(
    "TestParameters_for_channels",
    ["test_number", "status", "details", "asset_id", "channel_id", "page", "pageSize"],
)
