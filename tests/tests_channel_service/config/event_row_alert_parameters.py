"""
Module Docstring: Test Configuration for Event Row Alerts.
This module contains Pytest parameter sets for testing event row alerts in the channel service.
"""

import pytest

from tests.tests_channel_service.config.event_row_alert_config import TestParameters

ParameterSetsFileAlerts = [
    pytest.param(
        TestParameters(
            1, "file.graphics-asset-unknown", "minor", ["graphic"], "DSK1", {"assetId"}
        ),
        id="File-Alert.graphics-asset-unknown",
    ),
    pytest.param(
        TestParameters(
            2, "file.no-channel-logo-file", "minor", ["bug"], "Bug", {"assetId"}
        ),
        id="File-Alert.no-channel-logo-file",
    ),
    pytest.param(
        TestParameters(
            3, "file.no-graphics-file", "minor", ["graphic"], "DSK1", {"assetId"}
        ),
        id="File-Alert.no-graphics-file",
    ),
    pytest.param(
        TestParameters(
            4,
            "file.no-primary-file",
            "major",
            ["video", "audio", "caption"],
            "MainVideo",
            {"assetId"},
        ),
        id="File-Alert.no-primary-file",
    ),
    pytest.param(
        TestParameters(
            5,
            "file.primary-asset-unknown",
            "major",
            ["video", "audio", "caption"],
            "MainVideo",
            {"assetId"},
        ),
        id="File-Alert.primary-asset-unknown",
    ),
]

ParameterSetsLiveAlerts = [
    pytest.param(
        TestParameters(
            1,
            "live.primary-source-error",
            "major",
            ["live-video"],
            "LiveVideo",
            {"sourceName"},
        ),
        id="Live-Alert.unknown-source",
    )
]

ParameterSetsPlayoutAlerts = [
    pytest.param(
        TestParameters(
            1,
            "playout.primary-playout-error",
            "major",
            ["video", "audio", "caption"],
            "MainVideo",
            {"machineId"},
        ),
        id="Playout-Alert.primary-playout-error",
    )
]

ParameterSetsScteAlerts = [
    # 1,3,5 ... SCTE Block position
    pytest.param(
        TestParameters(
            1, "schedule.scte-unknown-preset", "minor", ["anc-data"], "Scte", set()
        ),
        id="Scte-Alert.scte-unknown-preset",
    ),
    pytest.param(
        TestParameters(
            3,
            "schedule.anc-data-schedule-parameters-invalid",
            "minor",
            ["anc-data"],
            "Scte",
            {"parameter"},
        ),
        id="schedule.anc-data-schedule-parameters-invalid",
    ),
]
