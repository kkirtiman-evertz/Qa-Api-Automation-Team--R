"""Importing necessary modules for logging,time and json"""

import datetime
import json
import logging

from websocket import create_connection

logger = logging.getLogger(__name__)


class EIOWSClient:
    """WebSocket client for Evertz.io"""

    def __init__(self, server, auth_token="", client_id="apiuser"):
        super(EIOWSClient, self).__init__()
        self.server = server
        self.auth_token = auth_token
        self.WS = create_connection(
            f"wss://{server}/wss?token={auth_token}&clientId={client_id}"
        )

    def _send_and_receive(self, json_request, timeout_seconds=5):
        try:
            logger.debug("WS Request: %s", json_request)
            correlation_id = json_request["id"]
            start = datetime.datetime.utcnow()
            self.WS.send(json.dumps(json_request))

            end = None
            size = 0
            result = None
            timeout_duration = datetime.timedelta(seconds=timeout_seconds)
            while (end is None or (result and result.get("id") != correlation_id)) and (
                datetime.datetime.utcnow() - start
            ) < timeout_duration:
                response = self.WS.recv()
                end = datetime.datetime.utcnow()
                logger.debug("WS Response: %s", response)

                size = len(response)
                result = json.loads(response)

            elapsed_time = (end - start).microseconds / 1000

            return result, size, elapsed_time
        except Exception as exception:
            logger.exception(
                "WebSocket request failed: [%s--%s]", type(exception), str(exception)
            )
            return None, 0, 0

    def ws_call(self, json_request, raw=False):
        """WS call"""
        result, size, exec_time = self._send_and_receive(json_request)

        if raw:
            return {"result": result, "size": size, "exec": exec_time}

        output = None
        session = None

        if result:
            if "result" in result:
                output = result["result"]
                session = result.get("session")
                if "message" in output:
                    logger.debug("WS Response - Reason: %s", output["message"])
            elif "error" in result:
                output = result["error"]
                logger.debug(
                    "WS Response - Code: %s Reason: %s",
                    output["code"],
                    output["message"],
                )

        return {"output": output, "session": session, "size": size, "exec": exec_time}

    def ws_receive(self, timeout=5):
        """Setting up WS connection to receive data"""
        try:
            self.WS.settimeout(timeout)
            response = self.WS.recv()
            self.WS.settimeout(None)
            result = json.loads(response)
            size = len(response)
            logger.debug("WS Receive Event: %s", result)
        except Exception as err:
            logger.error("WS Receive Event: %s", err)
            result = {"error": "TimedOut"}
            size = len(json.dumps(result))
        return {"result": result, "size": size}

    def close(self):
        """To close WS connection"""
        self.WS.close()
