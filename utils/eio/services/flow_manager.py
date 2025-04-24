import logging

from utils.eio.services import Service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class FlowManager(Service):
    def __init__(self, eio_client):
        super().__init__(eio_client)

    def create_source(
        self, protocol, source_name, ip, port, file_definition_profile, id
    ):
        """
        Creates a new source in the flow manager with the specified configuration.
        Args:
            protocol (str): The communication protocol used by the source.
            source_name (str): The name of the source.
            ip (str): The IP address of the source.
            port (int): The port number associated with the source.
            file_definition_profile (str): The file definition profile used by the source.
            id (str): The unique identifier of the file definition profile.
        Returns:
            dict: A dictionary containing the response from the flow manager.
        Raises:
            Exception: If an error occurs during the source creation process.
        """
        try:
            payload = {
                "data": {
                    "type": "device",
                    "attributes": {
                        "type": "input-receiver",
                        "displayName": source_name,
                        "name": source_name,
                        "fileDefinitionProfile": {
                            "name": file_definition_profile,
                            "id": id,
                        },
                        "config": {
                            "flow": {
                                "primaryInboundConfig": {
                                    "inboundCidr": ip,
                                    "inboundPort": port,
                                    "transport": {
                                        "protocol": protocol,
                                    },
                                }
                            }
                        },
                    },
                }
            }
            return self.eio_client.rest_call(
                method="POST", end_point="flow-manager/v2/devices", payload=payload
            )
        except Exception as exception:
            raise exception

    def get_all_sources(self):
        """
        Retrieves information about all sources from the flow manager.
        Returns:
            dict: A dictionary containing the response from the flow manager, including information
                  about all sources.
        Raises:
            Exception: If an error occurs during the retrieval of source information.
        """
        try:
            return self.eio_client.rest_call(
                method="GET", end_point="flow-manager/v2/devices/type/input-receiver"
            )
        except Exception as exception:
            raise exception

    def manage_source(self, device_id, source_id):
        """
        Associates a source with a device in the flow manager.
        Args:
            device_id (str): The unique identifier of the device to be associated with the source.
            source_id (str): The unique identifier of the source to be associated with the device.
        Returns:
            dict: A dictionary containing the response from the flow manager.
        Raises:
            Exception: If an error occurs during the association of the source with the device.
        """
        try:
            return self.eio_client.rest_call(
                method="POST",
                end_point=f"flow-manager/v2/devices/{source_id}/{device_id}",
            )
        except Exception as exception:
            raise exception

    def add_destination(self, channel_id, protocol, destination_name, ip_address, port):
        """
        Adds a destination to a channel configuration in the flow manager.
        Args:
            channel_id (str): The unique identifier of the channel to which the destination will be added.
            protocol (str): The communication protocol used by the destination.
            destination_name (str): The name of the destination.
            ip_address (str): The IP address of the destination.
            port (int): The port number associated with the destination.
        Returns:
            dict: A dictionary containing the response from the flow manager.
        Raises:
            Exception: If an error occurs during the addition of the destination to the channel configuration.
        """
        try:
            payload = {
                "data": {
                    "type": "device",
                    "attributes": {
                        "name": destination_name,
                        "type": "edge-destination",
                        "inputs": [
                            {"ip": ip_address, "port": port, "protocol": protocol}
                        ],
                        "ownerType": "channel",
                        "ownerId": channel_id,
                    },
                },
            }

            return self.eio_client.rest_call(
                method="POST",
                end_point=f"flow-manager/v2/devices",
                payload=payload,
            )
        except Exception as exception:
            raise exception

    def create_connection(self, source_id, destination_id):
        """
        Creates a connection between a source and a destination in the channel configuration.
        Args:
            source_id (str): The unique identifier of the source for the connection.
            destination_id (str): The unique identifier of the destination for the connection.
        Returns:
            dict: A dictionary containing the response from the flow manager.
        Raises:
            Exception: If an error occurs during the creation of the connection.
        """
        try:
            payload = {
                "data": {
                    "type": "connection",
                    "attributes": {
                        "source": {"id": source_id},
                        "destination": {"id": destination_id},
                    },
                }
            }
            response = self.eio_client.rest_call(
                method="POST",
                end_point=f"flow-manager/v2/connections/edge-destinations",
                payload=payload,
            )
            logging.info(
                f"Invoking create connection call {source_id}..{destination_id}.."
            )
            return response
        except Exception as exception:
            raise exception

    def get_channel_configurations(self, channel_id):
        """
        Retrieves information about a specific channel configuration from the flow manager.
        Args:
            channel_id (str): The unique identifier of the channel configuration to retrieve.
        Returns:
            dict: A dictionary containing the response from the flow manager, including information
                  about the specified channel configuration.
        Raises:
            Exception: If an error occurs during the retrieval of channel configuration information.
        """
        try:
            return self.eio_client.rest_call(
                method="GET",
                end_point=f"flow-manager/v2/devices/ownership/{channel_id}?deviceType=output-receiver&deviceType=edge-destination&deviceType=entitlement",
            )
        except Exception as exception:
            raise exception
