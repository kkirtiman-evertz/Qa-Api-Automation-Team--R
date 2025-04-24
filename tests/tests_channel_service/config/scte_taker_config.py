"""Importing necessary modules for SCTE config."""

import uuid

CLIENT_ID = str(uuid.uuid4())
FILE_DEFINITION_PROFILE = "live-captions"
PROTOCOL = "rist"
SOURCE_NAME = "scte-external-taker-test-source"
SOURCE_RECEIVER_NAME = "scte-external-taker-test-source_receiver"
DESTINATION_NAME = f"scte-taker-destination-{uuid.uuid4()}"
SCHEDULE_FILE_PATH = "tests/tests_channel_service/resources/"
SOURCE_FILE = "scte_taker_source.xml"
RECEIVER_FILE = "scte_taker_receiver.xml"
DISABLED_FLAG_RECEIVER_FILE = "scte_taker_receiver_flag_disabled.xml"
SOURCE_HOLD_TRIGGER_FILE = "scte_taker_hold_source.xml"
RECEIVER_HOLD_TRIGGER_FILE = "scte_taker_hold_receiver.xml"
DISABLED_FLAG_HOLD_RECEIVER_FILE = "scte_hold_receiver_flag_disabled.xml"
START_ID = "start"
STOP_ID = "stop"
IP = "0.0.0.0/0"
ID = "01JJ93QGE4QS1DFBMP7TKD9TKW"
PORT = 1234
EVENT_SIZE = 10
TEMPLATE_NAME = "Program"
START_MODE = "variable"
ASSET_ID = "COMMHUG"
MAX_WAIT_TIME = 30  # Maximum wait time in seconds
