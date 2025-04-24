"""
Module for managing aws related operations
"""

import uuid

BUCKET_NAME = "api-external-import-"
FILE_PATH = (
    "tests/tests_playlist_management/resources/playlist_external_import_export"
    "/external_import.xml"
)
FILE_NAME = "import_files/external_import.xml"
CLIENT_ID = str(uuid.uuid4())
EVENT_SIZE = 100
SERVICE_NAME = "playlist-management"
