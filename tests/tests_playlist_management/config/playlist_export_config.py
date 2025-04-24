"""
Module for managing aws related operations
"""

import uuid

TEMPLATE_NAME = "Program"
START_MODE = "variable"
CLIENT_ID = str(uuid.uuid4())
DEFAULT_ROUTE = "channel-service.default"
INVALID_ROUTE_SETUP = "channel-service"
ASSET_ID = "TESTING-ASSET"
EVENT_SIZE = 50
EXPORT_BUCKET = "playlist-export-"
EVERTZ_TV_TENANT_ID = "a8a8f532-9d3f-4d22-b007-e2706a13112d"
PLAYOUT_BUILD_TEST_TENANT_ID = "63a61456-ead0-4a87-8902-5ab5de617ee3"

FILE_STORE_IDS = {
    PLAYOUT_BUILD_TEST_TENANT_ID: "f2f0cd68-8ab8-4729-9f57-d013986d42d8",
    EVERTZ_TV_TENANT_ID: "4a8bec69-a682-45ae-8504-4d42c697c89d",
}
