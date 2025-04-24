"""
Scte capture utils
"""

from e2e.scte_capture.constants import CRED_PARAM_PATH
from e2e.scte_capture.exception.ScteCaptureException import ScteCaptureException
from utils.aws_helper import AwsHelper


def fetch_credentials():
    """
    Fetches credentials from the given path
    """
    try:
        aws_helper = AwsHelper()
        credentials = aws_helper.fetch_credentials(CRED_PARAM_PATH)
        return aws_helper, credentials
    except Exception as error:
        raise ScteCaptureException("Unable to fetch credentials.") from error
