"""
Event Row Alert Test Configuration.
"""

import uuid
from collections import namedtuple

CLIENT_ID = str(uuid.uuid4())
FILE_ALERTS_PLAYLIST = "event_row_alert_file_alerts.xml"
LIVE_ALERTS_PLAYLIST = "event_row_alert_live_alerts.xml"
PLAYOUT_ALERTS_PLAYLIST = "event_row_alert_playout_alerts.xml"
SCTE_ALERTS_PLAYLIST = "event_row_alert_scte_alerts.xml"
SCHEDULE_FILE_PATH = "tests/tests_channel_service/resources/event_row_alerts/"
EVENT_SIZE = "100"
MAX_WAIT_TIME = 30  # Maximum wait time in seconds
TestParameters = namedtuple(
    "TestParameters",
    ["test_number", "alert_code", "severity", "event_types", "streamName", "data"],
)
