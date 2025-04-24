"""Importing necessary modules for logging and time"""

import logging
import time

from utils.eio.services import Service


class PlaylistSearchAndReplace(Service):
    """Creating helper function for our service"""

    def __init__(self, eio_client):
        super().__init__(eio_client)

    def playlist_search_by_assetId(
        self,
        page_size=None,
        op=None,
        field=None,
        value=None,
        page_after=None,
        page_before=None,
        channel_id=None,
    ):
        """
        Search for events in a playlist
        @param channel_id : A unique identifier for a Channel.
        @param page_size : Sets the maximum number of items returned in a page.
        @param page_after : cursor for the next page.
        @param page_before : cursor for the previous page.
        @param op : Operation to be performed between `field` and `value`.
        @param field : Property of the asset to be compared.
        @param value : Value to be used for operation against the `field`.
        @returns: It returns a json object with key-value pair about asset details.
        """
        event_search_query = {"query": {"op": op, "field": field, "value": value}}
        param = {
            "page[after]": page_after,
            "page[before]": page_before,
            "page[size]": page_size,
        }
        try:
            output = self.eio_client.rest_call(
                "POST",
                end_point="playlist-search/channels/" + channel_id + "/search",
                params=param,
                payload=event_search_query,
            )
            return output
        except Exception as exception:
            logging.info(f"Unable to do perform search call {str(exception)}")
            raise exception

    @staticmethod
    def replace_searched_item(
        ws_client,
        request_id,
        search_asset_id=None,
        replace_asset_id=None,
        items_to_replace=None,
        channel_id=None,
    ):
        """
        Replace searched event in the playlist
        @param ws_client : Websocket client.
        @param request_id : A unique identifier for each request.
        @param channel_id : A unique identifier for a Channel.
        @param search_asset_id : asset id of searched item.
        @param replace_asset_id : asset id of replace item.
        @param items_to_replace : List of sequence id to replace.
        @returns: It returns a Json object
        """
        replace_item = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "replaceItems",
            "route": "channel-service.default",
            "params": {
                "channelId": channel_id,
                "replaceAction": {
                    "type": "replace-asset",
                    "oldValue": search_asset_id,
                    "newValue": replace_asset_id,
                },
                "itemsToReplace": items_to_replace,
            },
        }
        try:
            result = ws_client.ws_call(replace_item, raw=True)
            result.update({"method": replace_item["method"]})
            logging.info(result)
            return result
        except Exception as exception:
            logging.info(f"Unable to do perform replace call {str(exception)}")
            raise exception
