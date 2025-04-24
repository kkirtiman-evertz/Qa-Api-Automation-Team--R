"""
Module Docstring: Test Configuration for Schedule Asset External APi.
"""

import re
import uuid

SCHEDULE_EXTERNAL_FILE_NAME_PXF = "schedule_asset_external.pxf"
SCHEDULE_FILE_PATH = "tests/tests_scheduled_assets/resources/"
ASSET_ID = "BIG_BUCK_BUNNY_DF30"
REGEX_PATTERN_FOR_START_DATE_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*")
CLIENT_ID = str(uuid.uuid4())
EVENT_SIZE = 100
MAX_WAIT_TIME = 30  # Maximum wait time in seconds
PAGE = 1
PAGE_SIZE = 20
