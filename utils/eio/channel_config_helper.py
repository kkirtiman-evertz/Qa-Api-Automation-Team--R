import uuid


def construct_metadata_config(**kwargs):
    return {
        "name": kwargs.get(
            "name", f"backend-automation-test-channel{str(uuid.uuid4())}"
        ),
        "displayName": kwargs.get("display_name", "Backend Automation Test Channel"),
        "timezone": kwargs.get("timezone", "America/Toronto"),
        "frameRate": kwargs.get("frame_rate", "DF_29_97"),
        "logo": kwargs.get("logo", None),
        "hourOfJam": kwargs.get("hour_of_jam", 0),
        "dayStart": {
            "frames": kwargs.get("frames", 1078921),
            "rate": kwargs.get("rate", "DF_29_97"),
        },
        "canary": kwargs.get("canary", False),
        "serviceType": kwargs.get("service_type", "broadcast"),
        "serviceTier": kwargs.get("service_tier", "lite"),
        "id": kwargs.get("id", str(uuid.uuid4())),
        "additionalFeatures": {
            "automatedPromotions": kwargs.get("automated_promotions", False),
            "componentScheduling": kwargs.get("component_scheduling", False),
            "broadcastLiveEvent": kwargs.get("broadcast_live_event", False),
            "broadcastSchedulePreparationGrid": kwargs.get(
                "broadcast_schedule_preparation_grid", False
            ),
            "smartBlocks": kwargs.get("smart_blocks", False),
        },
    }


def construct_video_config(**kwargs):
    return {
        "scaleProfile": kwargs.get("scale_profile", "Full Raster"),
        "muxer": {
            "pmtPid": kwargs.get("pmt_pid", 32),
            "programNumber": kwargs.get("program_number", 1),
        },
        "rtp": {"ssrc": kwargs.get("ssrc", 2), "ttl": kwargs.get("ttl", 64)},
        "pid": kwargs.get("pid", 102),
        "videoStandard": kwargs.get("video_standard", "1080i/59.94"),
        "shadowOutput": kwargs.get("shadow_output", False),
        "publicName": kwargs.get("public_name", "Backend Automation Test Channel"),
    }


def construct_miscellaneous_config(**kwargs):
    return {
        "incomingScteTriggers": [
            {"dpi": kwargs.get("dpi", 300), "command": kwargs.get("command", "hold")}
        ]
    }


def construct_anc_data_config(**kwargs):
    return {
        "encoderTypes": kwargs.get("encoder_types", ["Open Caption"]),
        "openCaption": {
            "fileDefinitions": [
                {
                    "locale": kwargs.get("locale", "en_GB"),
                    "format": kwargs.get("format", "stl"),
                    "subType": kwargs.get("sub_type", "main"),
                }
            ],
            "styling": {
                "advancedStyling": kwargs.get("advanced_styling", False),
                "stylePreset": {
                    "overallStyle": kwargs.get("overall_style", "Outlined Text"),
                    "fontSize": kwargs.get("font_sizer", "Small"),
                },
            },
        },
    }


def construct_audio_config(**kwargs):
    return {
        "outputNodes": [
            {
                "channels": kwargs.get("channels", "Stereo"),
                "pid": kwargs.get("pid", 101),
                "bitrate": kwargs.get("bitrate", "192kbps"),
                "type": kwargs.get("type", "AC3"),
                "fileDefinitions": kwargs.get(
                    "file_definitions",
                    [
                        {
                            "locale": kwargs.get("locale", "en_GB"),
                            "format": kwargs.get("audio_format", "stereo-pcm"),
                            "subType": kwargs.get("sub_type", "main"),
                        }
                    ],
                ),
            }
        ]
    }
