"""
This module contains configuration constants used in scte capture
"""

HOST = "https://us-east-1.dev.api.evertz.io/"
WS_HOST = "us-east-1.dev.api.evertz.io"
TENANT = "63a61456-ead0-4a87-8902-5ab5de617ee3"
CHANNEL_ID = "61b165db-66f3-4d72-b478-03cb90185b20"
SCTE_TEST_EC2_IP_ADDRESS = "52.201.243.218"
SCTE_TEST_INSTANCE_NAME = "SCTE Test"
FILE_DATE_FORMAT = "%Y%m%d"
CRED_PARAM_PATH = (
    "/account/credentials/playout-api-automation-tests/build-test/dev/root"
)
SECURITY_GROUP_ID = "sg-05ce19b82a184ca0c"
PROTOCOL, DESTINATION_NAME, PORT = "rist", "scte-test-automation", 1024
