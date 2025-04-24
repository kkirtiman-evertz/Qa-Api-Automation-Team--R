import logging

from utils.eio.services import Service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class ScheduleAssetExternal(Service):
    def __init__(self, eio_client):
        super().__init__(eio_client)

    def get_channels_where_asset_scheduled_on(self, asset_id, page=None, pagesize=None):
        """
        Get the list of channels that an asset is scheduled on.
        @param asset_id: A unique identifier for an event.
        @param page: Page number to be returned.
        @param pagesize: Sets the maximum number of items returned in a page.
        @return: Returns metadata of channel where asset is scheduled.
        """
        try:
            params = {}
            if page is not None:
                params["page"] = page
            if pagesize is not None:
                params["pageSize"] = pagesize

            output = self.eio_client.rest_call(
                "GET",
                end_point=f"external/scheduled-assets/v1/assets/{asset_id}/channels",
                params=params,
            )
            return output
        except Exception as e:
            logger.error(f"Failed to retrieve channels for asset {asset_id}: {str(e)}")
            raise

    def get_timings_when_asset_scheduled_on(
        self, asset_id, channel_id, page=None, pagesize=None
    ):
        """
        Get the times that an asset is scheduled on a channel
        @param asset_id: A unique identifier for an event.
        @param channel_id: A unique identifier for a Channel.
        @param page: Page number to be returned.
        @param pagesize: Sets the maximum number of items returned in a page.
        @return: Returns times when asset is scheduled on the channel
        """
        try:
            params = {}
            if page is not None:
                params["page"] = page
            if pagesize is not None:
                params["pageSize"] = pagesize

            output = self.eio_client.rest_call(
                "GET",
                end_point=f"external/scheduled-assets/v1/assets/{asset_id}/channels/{channel_id}",
                params=params,
            )
            return output
        except Exception as e:
            logger.error(
                f"Failed to Get the times that an asset is scheduled on a channel {channel_id}: {str(e)}"
            )
            raise
