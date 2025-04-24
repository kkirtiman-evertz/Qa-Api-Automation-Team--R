"""Importing necessary modules for Channel management service. """

import requests

from utils.eio.services import Service, logger


class ChannelManagement(Service):
    """Defining methods for Channel management service."""

    def __init__(self, eio_client):
        super().__init__(eio_client)

    def update_channel_deployment(self, channel_id, required_state):
        """
        Patch channel required state to ON or OFF
        @param channel_id : Id of the channel
        @param required_state : Required state of the channel - On/Off
        @return : Channel Deployment update ; or error code.
        """
        update_channel_deployment = {
            "data": {
                "type": "channelDeployment",
                "attributes": {"requiredState": required_state},
            }
        }
        output = self.eio_client.rest_call(
            "PATCH",
            end_point="channel-management/channels/" + channel_id + "/deployment",
            payload=update_channel_deployment,
        )
        return output

    def get_channel_by_id(self, channel_id):
        """
        get channel details for the channel_id
        @params channel_id : id for the required channel
        @returns: channel object with extended config for the given channel ; or the error code.
        """
        return self.eio_client.rest_call(
            "GET", end_point="channel-management/channels/" + channel_id
        )

    def create_and_save_channel_config(
        self,
        metadata_config,
        video_config,
        miscellaneous_config,
        anc_data_config,
        audio_config,
    ):
        """
        Create and Save Channel with provided config

        Args:
            metadata_config (dict): Metadata configuration for the channel
            video_config (dict): Video configuration for the channel
            miscellaneous_config (dict): Miscellaneous configuration for the channel
            anc_data_config (dict): Ancillary data configuration for the channel
            audio_config (dict): Audio configuration for the channel

        Returns: saved values of the channel config.

        """

        channel_config = self._construct_channel_data(
            metadata_config,
            video_config,
            miscellaneous_config,
            anc_data_config,
            audio_config,
        )

        response = self.eio_client.rest_call(
            "POST", end_point="channel-management/channels", payload=channel_config
        )
        return response

    def update_channel_config(
        self,
        channel_id,
        metadata_config,
        video_config,
        miscellaneous_config,
        anc_data_config,
        audio_config,
    ):
        """
        Updates channel config for the given channel

        Args:
            channel_id (str): A unique identifier for the channel
            metadata_config (dict): Metadata configuration for the channel
            video_config (dict): Video configuration for the channel
            miscellaneous_config (dict): Miscellaneous configuration for the channel
            anc_data_config (dict): Ancillary data configuration for the channel
            audio_config (dict): Audio configuration for the channel

        Returns: updated values of the channel config.

        """
        channel_config_to_update = self._construct_channel_data(
            metadata_config,
            video_config,
            miscellaneous_config,
            anc_data_config,
            audio_config,
        )

        response = self.eio_client.rest_call(
            "PATCH",
            end_point=f"channel-management/channels/{channel_id}",
            payload=channel_config_to_update,
        )
        return response

    def delete_channel_config(self, channel_id):
        """
        Deletes the channel with the given Id
        Args:
            channel_id: A unique identifier for a Channel

        """
        try:
            output = self.eio_client.rest_call(
                "DELETE", end_point=f"channel-management/channels/{channel_id}"
            )
            return output
        except requests.exceptions.RequestException as e:
            # Logging the error and include exception details
            logger.error("An error occurred during the delete request:", exc_info=True)
            raise e

    @staticmethod
    def _construct_channel_data(
        metadata_config,
        video_config,
        miscellaneous_config,
        anc_data_config,
        audio_config,
    ):
        channel_data = {
            "data": {
                "type": "channel",
                "attributes": {
                    "metadata": metadata_config,
                    "video": video_config,
                    "miscellaneous": miscellaneous_config,
                    "ancData": anc_data_config,
                    "audio": audio_config,
                },
            }
        }
        return channel_data

    def trigger_deployment(self, channel_id: str, required_state: str):
        response = self.eio_client.rest_call(
            method="PATCH",
            end_point="channel-management/channels/" + channel_id + "/deployment",
            payload={
                "data": {
                    "type": "channelDeployment",
                    "attributes": {"requiredState": required_state},
                }
            },
        )
        return response
