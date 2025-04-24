"""Uploads scte playlist to s3"""

import logging
import uuid

from e2e.scte_capture import scte_utils
from e2e.scte_capture.constants import CHANNEL_ID, HOST, TENANT, WS_HOST
from utils.eio.clients.httpclient import EIOHttpClient
from utils.eio.clients.wsclient import EIOWSClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

playlist_mapping = {
    1: "e2e/scte_capture/resources/YoutubeTV-SCTETest.xml",
    2: "e2e/scte_capture/resources/PlutoTV-SCTETest.xml",
    3: "e2e/scte_capture/resources/SlingTV-SCTETest.xml",
}


def lambda_handler(event, _):
    """
    Lambda function for importing and clearing a playlist using EIOHttpClient and AWS Helper.
    """
    # pylint: disable=R0801
    aws_helper, credentials = scte_utils.fetch_credentials()

    eio_client = EIOHttpClient(
        server=HOST,
        ws_server_host=WS_HOST,
        tenant=TENANT,
        user=credentials["username"],
        password=credentials["password"],
    )
    eio_client.signin()
    ws_client = EIOWSClient(WS_HOST, eio_client.auth_token, str(uuid.uuid4()))

    loop_counter = event["loop_counter"]
    playlist_name = playlist_mapping.get(loop_counter)
    logger.info(f"loop_counter: {loop_counter} & playlist_name: {playlist_name}")
    eio_client.channel_service.clear_playlist(CHANNEL_ID, ws_client)
    pre_signed_url = eio_client.playlist_management.generate_presigned_url(
        playlist_name, CHANNEL_ID
    )
    import_response = aws_helper.upload_to_s3(
        pre_signed_url["output"]["data"]["attributes"]["url"],
        pre_signed_url["output"]["data"]["attributes"]["fields"],
        playlist_name,
    )
    logger.info(f"Import response: {import_response}")

    aws_helper.close()
    return event
