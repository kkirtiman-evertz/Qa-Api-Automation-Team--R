from utils.eio.services import Service


class ScheduledAssetsInternalHelper(Service):
    def __init__(self, eio_client):
        super().__init__(eio_client)

    def get_asset_detail(self, asset_id=None, page=None, pageSize=None):
        """
        Search list of channels where asset is scheduled along with total scheduled events within a channel
        @param asset_id: A unique identifier for an event.
        @param page: Page number to be returned.
        @param pageSize:Sets the maximum number of items returned in a page.
        @return: Returns metadata of asset where it is scheduled.
        """
        params = {"page": page, "pageSize": pageSize}
        try:
            return self.eio_client.rest_call(
                "GET", end_point=f"scheduled-assets/assets/{asset_id}", params=params
            )
        except Exception as exception:
            raise exception

    def get_asset_with_channel_detail(
        self, channel_id=None, asset_id=None, page=None, pageSize=None
    ):
        """
        Get list of scheduled events for an asset within a channel along with total scheduled events
        @param channel_id : A unique identifier for a Channel.
        @param asset_id: A unique identifier for an event.
        @param page: Page number to be returned.
        @param pageSize:Sets the maximum number of items returned in a page.
        @return: Returns metadata of asset where it is scheduled.
        """
        params = {"page": page, "pageSize": pageSize}
        try:
            return self.eio_client.rest_call(
                "GET",
                end_point=f"scheduled-assets/assets/{asset_id}/channels/{channel_id}",
                params=params,
            )
        except Exception as exception:
            raise exception
