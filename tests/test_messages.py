from json import loads as json_loads
from unittest import TestCase, main

from buttplug.errors import ErrorCode
from buttplug.messages import Decoder, Encoder, Incoming, Outgoing, \
    ProtocolSpec, v0, v1, v2, v3


class TestMessagesMachinery(TestCase):
    """Contains the machinery for the message tests"""

    encoder = Encoder()
    decoder: Decoder

    def expect_encode_success(self, msg: Outgoing, raw: str) -> None:
        msg.id = 1
        self.assertEqual(
            json_loads(self.encoder.encode(msg)),
            json_loads(raw),
        )
        msg.id = 4659283659
        self.assertNotEqual(
            json_loads(self.encoder.encode(msg)),
            json_loads(raw),
        )

    def expect_encode_fail(self, msg: Outgoing, raw: str) -> None:
        self.assertNotEqual(
            json_loads(self.encoder.encode(msg)),
            json_loads(raw),
        )

    def expect_decode_success(self, raw: str, msg: Incoming) -> None:
        self.assertEqual(self.decoder.decode("[" + raw + "]"), [msg])

    def expect_decode_fail(self, raw: str, msg: Incoming) -> None:
        self.assertNotEqual(self.decoder.decode("[" + raw + "]"), [msg])

    def expect_decode_exception(self, raw: str) -> None:
        with self.assertRaisesRegex(
                TypeError,
                '^unsupported message received: ',
        ):
            self.decoder.decode("[" + raw + "]")


class TestMessagesV0(TestMessagesMachinery):
    decoder = Decoder(ProtocolSpec.v0)
    messages = v0

    # Status messages

    ok_json = '''
        {
            "Ok": {
                "Id": 1
            }
        }
    '''

    error_json = '''
        {
            "Error": {
                "Id": 0,
                "ErrorMessage": "Server received invalid JSON.",
                "ErrorCode": 3
            }
        }
    '''

    ping_json = '''
        {
            "Ping": {
                "Id": 1
            }
        }
    '''

    # Handshake messages

    request_server_info_json = '''
        {
            "RequestServerInfo": {
                "Id": 1,
                "ClientName": "Test Client"
            }
        }
    '''

    server_info_json = '''
    {
        "ServerInfo": {
            "Id": 1,
            "ServerName": "Test Server",
            "MajorVersion": 1,
            "MinorVersion": 0,
            "BuildVersion": 0,
            "MessageVersion": 0,
            "MaxPingTime": 100
        }
    }
    '''

    # Enumeration messages

    start_scanning_json = '''
    {
        "StartScanning": {
            "Id": 1
        }
    }
    '''

    stop_scanning_json = '''
    {
        "StopScanning": {
            "Id": 1
        }
    }
    '''

    scanning_finished_json = '''
    {
        "ScanningFinished": {
            "Id": 0
        }
    }
    '''

    request_device_list_json = '''
    {
        "RequestDeviceList": {
            "Id": 1
        }
    }
    '''

    device_list_json = '''
    {
        "DeviceList": {
            "Id": 1,
            "Devices": [
                {
                    "DeviceName": "TestDevice 1",
                    "DeviceIndex": 0,
                    "DeviceMessages": ["SingleMotorVibrateCmd", "RawCmd", "KiirooCmd", "StopDeviceCmd"]
                },
                {
                    "DeviceName": "TestDevice 2",
                    "DeviceIndex": 1,
                    "DeviceMessages": ["SingleMotorVibrateCmd", "LovenseCmd", "StopDeviceCmd"]
                }
            ]
        }
    }
    '''

    device_added_json = '''
    {
        "DeviceAdded": {
            "Id": 0,
            "DeviceName": "TestDevice 1",
            "DeviceIndex": 0,
            "DeviceMessages": ["SingleMotorVibrateCmd", "RawCmd", "KiirooCmd", "StopDeviceCmd"]
        }
    }
    '''

    device_removed_json = '''
    {
        "DeviceRemoved": {
            "Id": 0,
            "DeviceIndex": 0
        }
    }
    '''

    # Generic device messages

    stop_device_cmd_json = '''
    {
        "StopDeviceCmd": {
            "Id": 1,
            "DeviceIndex": 0
        }
    }
    '''

    stop_all_devices_json = '''
    {
        "StopAllDevices": {
            "Id": 1
        }
    }
    '''

    single_motor_vibrate_cmd_json = '''
    {
        "SingleMotorVibrateCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Speed": 0.5
        }
    }
    '''

    # Specific device messages

    kiiroo_cmd_json = '''
    {
        "KiirooCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Command": "4"
        }
    }
    '''

    fleshlight_launch_fw12_cmd_json = '''
    {
        "FleshlightLaunchFW12Cmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Position": 95,
            "Speed": 90
        }
    }
    '''

    lovense_cmd_json = '''
    {
        "LovenseCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Command": "Vibrate:20;"
        }
    }
    '''

    vorze_a10_cyclone_cmd_json = '''
    {
        "VorzeA10CycloneCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Speed": 50,
            "Clockwise": true
        }
    }
    '''

    # Status message tests

    def test_ok(self):
        # Correct message
        self.expect_decode_success(
            self.ok_json,
            self.messages.Ok(1)
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.ok_json,
            self.messages.Ok(2)
        )

    def test_error(self):
        # Correct message
        self.expect_decode_success(
            self.error_json,
            self.messages.Error(
                0,
                "Server received invalid JSON.",
                ErrorCode.ERROR_MSG,
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.error_json,
            self.messages.Error(
                1,
                "Server received invalid JSON.",
                ErrorCode.ERROR_MSG,
            )
        )
        # Incorrect error message
        self.expect_decode_fail(
            self.error_json,
            self.messages.Error(
                0,
                "Server offline.",
                ErrorCode.ERROR_MSG,
            )
        )
        # Incorrect error code
        self.expect_decode_fail(
            self.error_json,
            self.messages.Error(
                0,
                "Server received invalid JSON.",
                ErrorCode.ERROR_INIT,
            )
        )

    def test_ping(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.Ping(),
            self.ping_json
        )

    # Handshake message tests

    def test_request_server_info(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RequestServerInfo(
                "Test Client",
            ),
            self.request_server_info_json
        )
        # Incorrect client name
        self.expect_encode_fail(
            self.messages.RequestServerInfo(
                "Production Client",
            ),
            self.request_server_info_json
        )

    def test_server_info(self):
        # Correct message
        self.expect_decode_success(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                1,
                0,
                0,
                ProtocolSpec.v0,
                100,
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                2,
                "Test Server",
                1,
                0,
                0,
                ProtocolSpec.v0,
                100,
            )
        )
        # Incorrect server name
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Production Server",
                1,
                0,
                0,
                ProtocolSpec.v0,
                100,
            )
        )
        # Incorrect mayor version
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                2,
                0,
                0,
                ProtocolSpec.v0,
                100,
            )
        )
        # Incorrect minor version
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                1,
                1,
                0,
                ProtocolSpec.v0,
                100,
            )
        )
        # Incorrect build version
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                1,
                0,
                1,
                ProtocolSpec.v0,
                100,
            )
        )
        # Incorrect protocol version
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                1,
                0,
                0,
                ProtocolSpec.v1,
                100,
            )
        )
        # Incorrect max ping time
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                1,
                0,
                0,
                ProtocolSpec.v0,
                200,
            )
        )

    # Enumeration message tests

    def test_start_scanning(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.StartScanning(),
            self.start_scanning_json
        )

    def test_stop_scanning(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.StopScanning(),
            self.stop_scanning_json
        )

    def test_scanning_finished(self):
        # Correct message
        self.expect_decode_success(
            self.scanning_finished_json,
            self.messages.ScanningFinished(0)
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.scanning_finished_json,
            self.messages.ScanningFinished(1)
        )

    def test_request_device_list(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RequestDeviceList(),
            self.request_device_list_json
        )

    def test_device_list(self):
        # Correct message
        self.expect_decode_success(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": [
                            "SingleMotorVibrateCmd",
                            "RawCmd",
                            "KiirooCmd",
                            "StopDeviceCmd",
                        ],
                    },
                    {
                        "device_name": "TestDevice 2",
                        "device_index": 1,
                        "device_messages": [
                            "SingleMotorVibrateCmd",
                            "LovenseCmd",
                            "StopDeviceCmd",
                        ],
                    },
                ],
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                2,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": [
                            "SingleMotorVibrateCmd",
                            "RawCmd",
                            "KiirooCmd",
                            "StopDeviceCmd",
                        ],
                    },
                    {
                        "device_name": "TestDevice 2",
                        "device_index": 1,
                        "device_messages": [
                            "SingleMotorVibrateCmd",
                            "LovenseCmd",
                            "StopDeviceCmd",
                        ],
                    },
                ],
            )
        )
        # Incorrect devices
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": [
                            "SingleMotorVibrateCmd",
                            "RawCmd",
                            "KiirooCmd",
                            "StopDeviceCmd",
                        ],
                    },
                ],
            )
        )

    def test_device_added(self):
        # Correct message
        self.expect_decode_success(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                0,
                [
                    "SingleMotorVibrateCmd",
                    "RawCmd",
                    "KiirooCmd",
                    "StopDeviceCmd",
                ],
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                1,
                "TestDevice 1",
                0,
                [
                    "SingleMotorVibrateCmd",
                    "RawCmd",
                    "KiirooCmd",
                    "StopDeviceCmd",
                ],
            )
        )
        # Incorrect device name
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 2",
                0,
                [
                    "SingleMotorVibrateCmd",
                    "RawCmd",
                    "KiirooCmd",
                    "StopDeviceCmd",
                ],
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                1,
                [
                    "SingleMotorVibrateCmd",
                    "RawCmd",
                    "KiirooCmd",
                    "StopDeviceCmd",
                ],
            )
        )
        # Incorrect device messages
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                0,
                [
                    "RawCmd",
                    "KiirooCmd",
                    "StopDeviceCmd",
                ],
            )
        )

    def test_device_removed(self):
        # Correct message
        self.expect_decode_success(
            self.device_removed_json,
            self.messages.DeviceRemoved(
                0,
                0,
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_removed_json,
            self.messages.DeviceRemoved(
                1,
                0,
            )
        )
        # Incorrect device ID
        self.expect_decode_fail(
            self.device_removed_json,
            self.messages.DeviceRemoved(
                0,
                1,
            )
        )

    # Generic device message tests

    def test_stop_device_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.StopDeviceCmd(0),
            self.stop_device_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.StopDeviceCmd(1),
            self.stop_device_cmd_json
        )

    def test_stop_all_devices(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.StopAllDevices(),
            self.stop_all_devices_json
        )

    def test_single_motor_vibrate_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.SingleMotorVibrateCmd(
                0,
                0.5,
            ),
            self.single_motor_vibrate_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.SingleMotorVibrateCmd(
                1,
                0.5,
            ),
            self.single_motor_vibrate_cmd_json
        )
        # Incorrect speed
        self.expect_encode_fail(
            self.messages.SingleMotorVibrateCmd(
                0,
                0.25,
            ),
            self.single_motor_vibrate_cmd_json
        )

    # Specific device message tests

    def test_kiiroo_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.KiirooCmd(
                0,
                "4",
            ),
            self.kiiroo_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.KiirooCmd(
                1,
                "4",
            ),
            self.kiiroo_cmd_json
        )
        # Incorrect command
        self.expect_encode_fail(
            self.messages.KiirooCmd(
                0,
                "1",
            ),
            self.kiiroo_cmd_json
        )

    def test_fleshlight_launch_fw12_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.FleshlightLaunchFW12Cmd(
                0,
                95,
                90,
            ),
            self.fleshlight_launch_fw12_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.FleshlightLaunchFW12Cmd(
                1,
                95,
                90,
            ),
            self.fleshlight_launch_fw12_cmd_json
        )
        # Incorrect position
        self.expect_encode_fail(
            self.messages.FleshlightLaunchFW12Cmd(
                0,
                5,
                90,
            ),
            self.fleshlight_launch_fw12_cmd_json
        )
        # Incorrect speed
        self.expect_encode_fail(
            self.messages.FleshlightLaunchFW12Cmd(
                0,
                95,
                10,
            ),
            self.fleshlight_launch_fw12_cmd_json
        )

    def test_lovense_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.LovenseCmd(
                0,
                "Vibrate:20;",
            ),
            self.lovense_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.LovenseCmd(
                1,
                "Vibrate:20;",
            ),
            self.lovense_cmd_json
        )
        # Incorrect command
        self.expect_encode_fail(
            self.messages.LovenseCmd(
                0,
                "Vibrate:10;",
            ),
            self.lovense_cmd_json
        )

    def test_vorze_a10_cyclone_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.VorzeA10CycloneCmd(
                0,
                50,
                True,
            ),
            self.vorze_a10_cyclone_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.VorzeA10CycloneCmd(
                1,
                50,
                True,
            ),
            self.vorze_a10_cyclone_cmd_json
        )
        # Incorrect speed
        self.expect_encode_fail(
            self.messages.VorzeA10CycloneCmd(
                0,
                25,
                True,
            ),
            self.vorze_a10_cyclone_cmd_json
        )
        # Incorrect clockwise
        self.expect_encode_fail(
            self.messages.VorzeA10CycloneCmd(
                0,
                50,
                False,
            ),
            self.vorze_a10_cyclone_cmd_json
        )


class TestMessagesV1(TestMessagesV0):
    decoder = Decoder(ProtocolSpec.v1)
    messages = v1

    # Handshake messages

    request_server_info_json = '''
        {
            "RequestServerInfo": {
                "Id": 1,
                "ClientName": "Test Client",
                "MessageVersion": 1
            }
        }
    '''

    # Enumeration messages

    device_list_json = '''
    {
        "DeviceList": {
            "Id": 1,
            "Devices": [
                {
                    "DeviceName": "TestDevice 1",
                    "DeviceIndex": 0,
                    "DeviceMessages": {
                        "VibrateCmd": { "FeatureCount": 2 },
                        "StopDeviceCmd": {}
                    }
                },
                {
                    "DeviceName": "TestDevice 2",
                    "DeviceIndex": 1,
                    "DeviceMessages": {
                        "LinearCmd": { "FeatureCount": 1 },
                        "StopDeviceCmd": {}
                    }
                }
            ]
        }
    }
    '''

    device_added_json = '''
    {
        "DeviceAdded": {
            "Id": 0,
            "DeviceName": "TestDevice 1",
            "DeviceIndex": 0,
            "DeviceMessages": {
                "VibrateCmd": { "FeatureCount": 2 },
                "StopDeviceCmd": {}
            }
        }
    }
    '''

    # Generic device messages

    vibrate_cmd_json = '''
    {
        "VibrateCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Speeds": [
                {
                    "Index": 0,
                    "Speed": 0.5
                },
                {
                    "Index": 1,
                    "Speed": 1.0
                }
            ]
        }
    }
    '''

    linear_cmd_json = '''
    {
        "LinearCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Vectors": [
                {
                    "Index": 0,
                    "Duration": 500,
                    "Position": 0.3
                },
                {
                    "Index": 1,
                    "Duration": 1000,
                    "Position": 0.8
                }
            ]
        }
    }
    '''

    rotate_cmd_json = '''
    {
        "RotateCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Rotations": [
                {
                    "Index": 0,
                    "Speed": 0.5,
                    "Clockwise": true
                },
                {
                    "Index": 1,
                    "Speed": 1.0,
                    "Clockwise": false
                }
            ]
        }
    }
    '''

    # Handshake message tests

    def test_request_server_info(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RequestServerInfo(
                "Test Client",
                ProtocolSpec.v1,
            ),
            self.request_server_info_json
        )
        # Incorrect client name
        self.expect_encode_fail(
            self.messages.RequestServerInfo(
                "Production Client",
                ProtocolSpec.v1,
            ),
            self.request_server_info_json
        )
        # Incorrect protocol version
        self.expect_encode_fail(
            self.messages.RequestServerInfo(
                "Test Client",
                ProtocolSpec.v0,
            ),
            self.request_server_info_json
        )

    # Enumeration message tests

    def test_device_list(self):
        # Correct message
        self.expect_decode_success(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": {
                            "VibrateCmd": {
                                "FeatureCount": 2,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                    {
                        "device_name": "TestDevice 2",
                        "device_index": 1,
                        "device_messages": {
                            "LinearCmd": {
                                "FeatureCount": 1,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                ],
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                2,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": {
                            "VibrateCmd": {
                                "FeatureCount": 2,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                    {
                        "device_name": "TestDevice 2",
                        "device_index": 1,
                        "device_messages": {
                            "LinearCmd": {
                                "FeatureCount": 1,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                ],
            )
        )
        # Incorrect devices
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": {
                            "VibrateCmd": {
                                "FeatureCount": 2,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                ],
            )
        )

    def test_device_added(self):
        # Correct message
        self.expect_decode_success(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                0,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                1,
                "TestDevice 1",
                0,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect device name
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 2",
                0,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                1,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect device messages
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                0,
                {
                    "StopDeviceCmd": {},
                },
            )
        )

    # Generic device message tests

    test_single_motor_vibrate_cmd = None

    def test_vibrate_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.VibrateCmd(
                0,
                [
                    {
                        "index": 0,
                        "speed": 0.5,
                    },
                    {
                        "index": 1,
                        "speed": 1.0,
                    },
                ],
            ),
            self.vibrate_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.VibrateCmd(
                1,
                [
                    {
                        "index": 0,
                        "speed": 0.5,
                    },
                    {
                        "index": 1,
                        "speed": 1.0,
                    },
                ],
            ),
            self.vibrate_cmd_json
        )
        # Incorrect device speeds
        self.expect_encode_fail(
            self.messages.VibrateCmd(
                0,
                [
                    {
                        "index": 0,
                        "speed": 0.5,
                    },
                ],
            ),
            self.vibrate_cmd_json
        )

    def test_linear_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.LinearCmd(
                0,
                [
                    {
                        "index": 0,
                        "duration": 500,
                        "position": 0.3,
                    },
                    {
                        "index": 1,
                        "duration": 1000,
                        "position": 0.8,
                    },
                ],
            ),
            self.linear_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.LinearCmd(
                1,
                [
                    {
                        "index": 0,
                        "duration": 500,
                        "position": 0.3,
                    },
                    {
                        "index": 1,
                        "duration": 1000,
                        "position": 0.8,
                    },
                ],
            ),
            self.linear_cmd_json
        )
        # Incorrect device speeds
        self.expect_encode_fail(
            self.messages.LinearCmd(
                0,
                [
                    {
                        "index": 0,
                        "duration": 500,
                        "position": 0.3,
                    },
                ],
            ),
            self.linear_cmd_json
        )

    def test_rotate_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RotateCmd(
                0,
                [
                    {
                        "index": 0,
                        "speed": 0.5,
                        "clockwise": True,
                    },
                    {
                        "index": 1,
                        "speed": 1.0,
                        "clockwise": False,
                    },
                ],
            ),
            self.rotate_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.RotateCmd(
                1,
                [
                    {
                        "index": 0,
                        "speed": 0.5,
                        "clockwise": True,
                    },
                    {
                        "index": 1,
                        "speed": 1.0,
                        "clockwise": False,
                    },
                ],
            ),
            self.rotate_cmd_json
        )
        # Incorrect device speeds
        self.expect_encode_fail(
            self.messages.RotateCmd(
                0,
                [
                    {
                        "index": 0,
                        "speed": 0.5,
                        "clockwise": True,
                    },
                ],
            ),
            self.rotate_cmd_json
        )

    # Specific device message tests

    test_kiiroo_cmd = None

    test_fleshlight_launch_fw12_cmd = None

    test_lovense_cmd = None

    test_vorze_a10_cyclone_cmd = None


class TestMessagesV2(TestMessagesV1):
    decoder = Decoder(ProtocolSpec.v2)
    messages = v2

    # Handshake messages

    server_info_json = '''
    {
        "ServerInfo": {
            "Id": 1,
            "ServerName": "Test Server",
            "MessageVersion": 1,
            "MaxPingTime": 100
        }
    }
    '''

    # Enumeration messages

    device_list_json = '''
    {
        "DeviceList": {
            "Id": 1,
            "Devices": [
                {
                    "DeviceName": "TestDevice 1",
                    "DeviceIndex": 0,
                    "DeviceMessages": {
                        "VibrateCmd": {
                            "FeatureCount": 2,
                            "StepCount": 20
                        },
                        "StopDeviceCmd": {}
                    }
                },
                {
                    "DeviceName": "TestDevice 2",
                    "DeviceIndex": 1,
                    "DeviceMessages": {
                        "LinearCmd": { "FeatureCount": 1 },
                        "StopDeviceCmd": {}
                    }
                }
            ]
        }
    }
    '''

    device_added_json = '''
    {
        "DeviceAdded": {
            "Id": 0,
            "DeviceName": "TestDevice 1",
            "DeviceIndex": 0,
            "DeviceMessages": {
                "VibrateCmd": {
                    "FeatureCount": 2,
                    "StepCount": 20
                },
                "StopDeviceCmd": {}
            }
        }
    }
    '''

    # Generic sensor messages

    battery_level_cmd_json = '''
    {
        "BatteryLevelCmd": {
            "Id": 1,
            "DeviceIndex": 0
        }
    }
    '''

    battery_level_reading_json = '''
    {
        "BatteryLevelReading": {
            "Id": 1,
            "DeviceIndex": 0,
            "BatteryLevel": 0.5
        }
    }
    '''

    rssi_level_cmd_json = '''
    {
        "RSSILevelCmd": {
            "Id": 1,
            "DeviceIndex": 0
        }
    }
    '''

    rssi_level_reading_json = '''
    {
        "RSSILevelReading": {
            "Id": 1,
            "DeviceIndex": 0,
            "RSSILevel": -40
        }
    }
    '''

    # Raw device messages

    raw_write_cmd_json = '''
    {
        "RawWriteCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Endpoint": "tx",
            "Data": [0, 1, 0],
            "WriteWithResponse": false
        }
    }
    '''

    raw_read_cmd_json = '''
    {
        "RawReadCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Endpoint": "tx",
            "ExpectedLength": 0,
            "WaitForData": false
        }
    }
    '''

    raw_reading_json = '''
    {
        "RawReading": {
            "Id": 1,
            "DeviceIndex": 0,
            "Endpoint": "rx",
            "Data": [0, 1, 0]
        }
    }
    '''

    raw_subscribe_cmd_json = '''
    {
        "RawSubscribeCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Endpoint": "tx"
        }
    }
    '''

    raw_unsubscribe_cmd_json = '''
    {
        "RawUnsubscribeCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Endpoint": "tx"
        }
    }
    '''

    # Handshake message tests

    def test_server_info(self):
        # Correct message
        self.expect_decode_success(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                ProtocolSpec.v1,
                100,
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                2,
                "Test Server",
                ProtocolSpec.v1,
                100,
            )
        )
        # Incorrect server name
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Production Server",
                ProtocolSpec.v1,
                100,
            )
        )
        # Incorrect protocol version
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                ProtocolSpec.v0,
                100,
            )
        )
        # Incorrect max ping time
        self.expect_decode_fail(
            self.server_info_json,
            self.messages.ServerInfo(
                1,
                "Test Server",
                ProtocolSpec.v1,
                200,
            )
        )

    # Enumeration message tests

    def test_device_list(self):
        # Correct message
        self.expect_decode_success(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": {
                            "VibrateCmd": {
                                "FeatureCount": 2,
                                "StepCount": 20,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                    {
                        "device_name": "TestDevice 2",
                        "device_index": 1,
                        "device_messages": {
                            "LinearCmd": {
                                "FeatureCount": 1,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                ],
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                2,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": {
                            "VibrateCmd": {
                                "FeatureCount": 2,
                                "StepCount": 20,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                    {
                        "device_name": "TestDevice 2",
                        "device_index": 1,
                        "device_messages": {
                            "LinearCmd": {
                                "FeatureCount": 1,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                ],
            )
        )
        # Incorrect devices
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "TestDevice 1",
                        "device_index": 0,
                        "device_messages": {
                            "VibrateCmd": {
                                "FeatureCount": 2,
                                "StepCount": 20,
                            },
                            "StopDeviceCmd": {},
                        },
                    },
                ],
            )
        )

    def test_device_added(self):
        # Correct message
        self.expect_decode_success(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                0,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                        "StepCount": 20,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                1,
                "TestDevice 1",
                0,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                        "StepCount": 20,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect device name
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 2",
                0,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                        "StepCount": 20,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                1,
                {
                    "VibrateCmd": {
                        "FeatureCount": 2,
                        "StepCount": 20,
                    },
                    "StopDeviceCmd": {},
                },
            )
        )
        # Incorrect device messages
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "TestDevice 1",
                0,
                {
                    "StopDeviceCmd": {},
                },
            )
        )

    # Generic sensor message tests

    def test_battery_level_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.BatteryLevelCmd(0),
            self.battery_level_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.BatteryLevelCmd(1),
            self.battery_level_cmd_json
        )

    def test_battery_level_reading(self):
        # Correct message
        self.expect_decode_success(
            self.battery_level_reading_json,
            self.messages.BatteryLevelReading(
                1,
                0,
                0.5,
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.battery_level_reading_json,
            self.messages.BatteryLevelReading(
                0,
                0,
                0.5,
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.battery_level_reading_json,
            self.messages.BatteryLevelReading(
                1,
                1,
                0.5,
            )
        )
        # Incorrect battery level
        self.expect_decode_fail(
            self.battery_level_reading_json,
            self.messages.BatteryLevelReading(
                1,
                0,
                0.75,
            )
        )

    def test_rssi_level_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RSSILevelCmd(0),
            self.rssi_level_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.RSSILevelCmd(1),
            self.rssi_level_cmd_json
        )

    def test_rssi_level_reading(self):
        # Correct message
        self.expect_decode_success(
            self.rssi_level_reading_json,
            self.messages.RSSILevelReading(
                1,
                0,
                -40,
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.rssi_level_reading_json,
            self.messages.RSSILevelReading(
                0,
                0,
                -40,
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.rssi_level_reading_json,
            self.messages.RSSILevelReading(
                1,
                1,
                -40,
            )
        )
        # Incorrect RSSI level
        self.expect_decode_fail(
            self.rssi_level_reading_json,
            self.messages.RSSILevelReading(
                1,
                0,
                -50,
            )
        )

    # Raw device message tests

    def test_raw_write_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RawWriteCmd(
                0,
                "tx",
                [0, 1, 0],
            ),
            self.raw_write_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.RawWriteCmd(
                1,
                "tx",
                [0, 1, 0],
            ),
            self.raw_write_cmd_json
        )
        # Incorrect endpoint
        self.expect_encode_fail(
            self.messages.RawWriteCmd(
                0,
                "rx",
                [0, 1, 0],
            ),
            self.raw_write_cmd_json
        )
        # Incorrect data
        self.expect_encode_fail(
            self.messages.RawWriteCmd(
                0,
                "tx",
                [0, 1],
            ),
            self.raw_write_cmd_json
        )
        # Incorrect write-with-response
        self.expect_encode_fail(
            self.messages.RawWriteCmd(
                0,
                "tx",
                [0, 1, 0],
                True,
            ),
            self.raw_write_cmd_json
        )

    def test_raw_read_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RawReadCmd(
                0,
                "tx",
            ),
            self.raw_read_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.RawReadCmd(
                1,
                "tx",
            ),
            self.raw_read_cmd_json
        )
        # Incorrect endpoint
        self.expect_encode_fail(
            self.messages.RawReadCmd(
                0,
                "rx",
            ),
            self.raw_read_cmd_json
        )
        # Incorrect expected length
        self.expect_encode_fail(
            self.messages.RawReadCmd(
                0,
                "tx",
                1,
            ),
            self.raw_read_cmd_json
        )
        # Incorrect wait-for-data
        self.expect_encode_fail(
            self.messages.RawReadCmd(
                0,
                "tx",
                0,
                True,
            ),
            self.raw_read_cmd_json
        )

    def test_raw_reading(self):
        # Correct message
        self.expect_decode_success(
            self.raw_reading_json,
            self.messages.RawReading(
                1,
                0,
                "rx",
                [0, 1, 0],
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.raw_reading_json,
            self.messages.RawReading(
                0,
                0,
                "rx",
                [0, 1, 0],
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.raw_reading_json,
            self.messages.RawReading(
                1,
                1,
                "rx",
                [0, 1, 0],
            )
        )
        # Incorrect endpoint
        self.expect_decode_fail(
            self.raw_reading_json,
            self.messages.RawReading(
                1,
                0,
                "tx",
                [0, 1, 0],
            )
        )
        # Incorrect data
        self.expect_decode_fail(
            self.raw_reading_json,
            self.messages.RawReading(
                1,
                0,
                "rx",
                [0, 1],
            )
        )

    def test_raw_subscribe_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RawSubscribeCmd(
                0,
                "tx",
            ),
            self.raw_subscribe_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.RawSubscribeCmd(
                1,
                "tx",
            ),
            self.raw_subscribe_cmd_json
        )
        # Incorrect endpoint
        self.expect_encode_fail(
            self.messages.RawSubscribeCmd(
                0,
                "rx",
            ),
            self.raw_subscribe_cmd_json
        )

    def test_raw_unsubscribe_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.RawUnsubscribeCmd(
                0,
                "tx",
            ),
            self.raw_unsubscribe_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.RawUnsubscribeCmd(
                1,
                "tx",
            ),
            self.raw_unsubscribe_cmd_json
        )
        # Incorrect endpoint
        self.expect_encode_fail(
            self.messages.RawUnsubscribeCmd(
                0,
                "rx",
            ),
            self.raw_unsubscribe_cmd_json
        )


rabbit_messages = {
    "ScalarCmd": [
        {
            "StepCount": 20,
            "FeatureDescriptor": "Clitoral Stimulator",
            "ActuatorType": "Vibrate",
        },
        {
            "StepCount": 20,
            "FeatureDescriptor": "Insertable Vibrator",
            "ActuatorType": "Vibrate",
        },
    ],
    "StopDeviceCmd": [],
}
stroker_messages = {
    "LinearCmd": [
        {
            "StepCount": 100,
            "FeatureDescriptor": "Stroker"
        },
    ],
    "StopDeviceCmd": [],
}


class TestMessagesV3(TestMessagesV2):
    decoder = Decoder(ProtocolSpec.v3)
    messages = v3

    # Enumeration messages

    device_list_json = '''
    {
        "DeviceList": {
            "Id": 1,
            "Devices": [
                {
                    "DeviceName": "Test Vibrator",
                    "DeviceIndex": 0,
                    "DeviceMessages": {
                        "ScalarCmd": [
                            {
                                "StepCount": 20,
                                "FeatureDescriptor": "Clitoral Stimulator",
                                "ActuatorType": "Vibrate"
                            },
                            {
                                "StepCount": 20,
                                "FeatureDescriptor": "Insertable Vibrator",
                                "ActuatorType": "Vibrate"
                            }
                        ],
                        "StopDeviceCmd": {}
                    }
                },
                {
                    "DeviceName": "Test Stroker",
                    "DeviceIndex": 1,
                    "DeviceMessageTimingGap": 100,
                    "DeviceDisplayName": "User set name",
                    "DeviceMessages": {
                        "LinearCmd": [
                            {
                                "StepCount": 100,
                                "FeatureDescriptor": "Stroker"
                            }
                        ],
                        "StopDeviceCmd": {}
                    }
                }
            ]
        }
    }
    '''

    device_added_json = '''
    {
        "DeviceAdded": {
            "Id": 0,
            "DeviceName": "Test Vibrator",
            "DeviceIndex": 0,
            "DeviceMessageTimingGap": 100,
            "DeviceDisplayName": "Rabbit Vibrator",
            "DeviceMessages": {
                "ScalarCmd": [
                    {
                    "StepCount": 20,
                    "FeatureDescriptor": "Clitoral Stimulator",
                    "ActuatorType": "Vibrate"
                    },
                    {
                    "StepCount": 20,
                    "FeatureDescriptor": "Insertable Vibrator",
                    "ActuatorType": "Vibrate"
                    }
                ],
                "StopDeviceCmd": {}
            }
        }
    }
    '''

    # Generic device messages

    scalar_cmd_json = '''
    {
        "ScalarCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "Scalars": [
                {
                    "Index": 0,
                    "Scalar": 0.5,
                    "ActuatorType": "Vibrate"
                },
                {
                    "Index": 1,
                    "Scalar": 1.0,
                    "ActuatorType": "Inflate"
                }
            ]
        }
    }
    '''

    # Generic sensor messages

    sensor_read_cmd_json = '''
    {
        "SensorReadCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "SensorIndex": 0,
            "SensorType": "Pressure"
        }
    }
    '''

    sensor_reading_json = '''
    {
        "SensorReading": {
            "Id": 1,
            "DeviceIndex": 0,
            "SensorIndex": 0,
            "SensorType": "Pressure",
            "Data": [591]
        }
    }
    '''

    sensor_subscribe_cmd_json = '''
    {
        "SensorSubscribeCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "SensorIndex": 0,
            "SensorType": "Pressure"
        }
    }
    '''

    sensor_unsubscribe_cmd_json = '''
    {
        "SensorUnsubscribeCmd": {
            "Id": 1,
            "DeviceIndex": 0,
            "SensorIndex": 0,
            "SensorType": "Pressure"
        }
    }
    '''

    # Enumeration message tests

    def test_device_list(self):
        # Correct message
        self.expect_decode_success(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "Test Vibrator",
                        "device_index": 0,
                        "device_messages": rabbit_messages,
                    },
                    {
                        "device_name": "Test Stroker",
                        "device_index": 1,
                        "device_message_timing_gap": 100,
                        "device_display_name": "User set name",
                        "device_messages": stroker_messages,
                    },
                ],
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                2,
                [
                    {
                        "device_name": "Test Vibrator",
                        "device_index": 0,
                        "device_messages": rabbit_messages,
                    },
                    {
                        "device_name": "Test Stroker",
                        "device_index": 1,
                        "device_message_timing_gap": 100,
                        "device_display_name": "User set name",
                        "device_messages": stroker_messages,
                    },
                ],
            )
        )
        # Incorrect devices
        self.expect_decode_fail(
            self.device_list_json,
            self.messages.DeviceList(
                1,
                [
                    {
                        "device_name": "Test Vibrator",
                        "device_index": 0,
                        "device_messages": rabbit_messages,
                    },
                ],
            )
        )

    def test_device_added(self):
        # Correct message
        self.expect_decode_success(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "Test Vibrator",
                0,
                rabbit_messages,
                100,
                "Rabbit Vibrator",
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                1,
                "Test Vibrator",
                0,
                rabbit_messages,
                100,
                "Rabbit Vibrator",
            )
        )
        # Incorrect device name
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "Test Rabbit",
                0,
                rabbit_messages,
                100,
                "Rabbit Vibrator",
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "Test Vibrator",
                1,
                rabbit_messages,
                100,
                "Rabbit Vibrator",
            )
        )
        # Incorrect device messages
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "Test Vibrator",
                0,
                stroker_messages,
                100,
                "Rabbit Vibrator",
            )
        )
        # Incorrect message timing gap
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "Test Vibrator",
                0,
                rabbit_messages,
                200,
                "Rabbit Vibrator",
            )
        )
        # Incorrect display name
        self.expect_decode_fail(
            self.device_added_json,
            self.messages.DeviceAdded(
                0,
                "Test Vibrator",
                0,
                rabbit_messages,
                100,
                "Rabbit",
            )
        )

    # Generic device message tests

    test_vibrate_cmd = None

    def test_scalar_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.ScalarCmd(
                0,
                [
                    {
                        "index": 0,
                        "scalar": 0.5,
                        "actuator_type": "Vibrate",
                    },
                    {
                        "index": 1,
                        "scalar": 1.0,
                        "actuator_type": "Inflate",
                    },
                ],
            ),
            self.scalar_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.ScalarCmd(
                1,
                [
                    {
                        "index": 0,
                        "scalar": 0.5,
                        "actuator_type": "Vibrate",
                    },
                    {
                        "index": 1,
                        "scalar": 1.0,
                        "actuator_type": "Inflate",
                    },
                ],
            ),
            self.scalar_cmd_json
        )
        # Incorrect device speeds
        self.expect_encode_fail(
            self.messages.ScalarCmd(
                0,
                [
                    {
                        "index": 0,
                        "scalar": 0.5,
                        "actuator_type": "Vibrate",
                    },
                ],
            ),
            self.scalar_cmd_json
        )

    # Generic sensor message tests

    test_battery_level_cmd = None

    def test_battery_level_reading(self):
        self.expect_decode_exception(self.battery_level_reading_json)

    test_rssi_level_cmd = None

    def test_rssi_level_reading(self):
        self.expect_decode_exception(self.rssi_level_reading_json)

    def test_sensor_read_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.SensorReadCmd(
                0,
                0,
                "Pressure",
            ),
            self.sensor_read_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.SensorReadCmd(
                1,
                0,
                "Pressure",
            ),
            self.sensor_read_cmd_json
        )
        # Incorrect sensor index
        self.expect_encode_fail(
            self.messages.SensorReadCmd(
                0,
                1,
                "Pressure",
            ),
            self.sensor_read_cmd_json
        )
        # Incorrect sensor type
        self.expect_encode_fail(
            self.messages.SensorReadCmd(
                0,
                0,
                "Speed",
            ),
            self.sensor_read_cmd_json
        )

    def test_sensor_reading(self):
        # Correct message
        self.expect_decode_success(
            self.sensor_reading_json,
            self.messages.SensorReading(
                1,
                0,
                0,
                "Pressure",
                [591],
            )
        )
        # Incorrect ID
        self.expect_decode_fail(
            self.sensor_reading_json,
            self.messages.SensorReading(
                0,
                0,
                0,
                "Pressure",
                [591],
            )
        )
        # Incorrect device index
        self.expect_decode_fail(
            self.sensor_reading_json,
            self.messages.SensorReading(
                1,
                1,
                0,
                "Pressure",
                [591],
            )
        )
        # Incorrect sensor index
        self.expect_decode_fail(
            self.sensor_reading_json,
            self.messages.SensorReading(
                1,
                0,
                1,
                "Pressure",
                [591],
            )
        )
        # Incorrect sensor type
        self.expect_decode_fail(
            self.sensor_reading_json,
            self.messages.SensorReading(
                1,
                0,
                0,
                "Speed",
                [591],
            )
        )
        # Incorrect data
        self.expect_decode_fail(
            self.sensor_reading_json,
            self.messages.SensorReading(
                1,
                0,
                0,
                "Pressure",
                [],
            )
        )

    def test_sensor_subscribe_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.SensorSubscribeCmd(
                0,
                0,
                "Pressure",
            ),
            self.sensor_subscribe_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.SensorSubscribeCmd(
                1,
                0,
                "Pressure",
            ),
            self.sensor_subscribe_cmd_json
        )
        # Incorrect sensor index
        self.expect_encode_fail(
            self.messages.SensorSubscribeCmd(
                0,
                1,
                "Pressure",
            ),
            self.sensor_subscribe_cmd_json
        )
        # Incorrect sensor type
        self.expect_encode_fail(
            self.messages.SensorSubscribeCmd(
                0,
                0,
                "Speed",
            ),
            self.sensor_subscribe_cmd_json
        )

    def test_sensor_unsubscribe_cmd(self):
        # Correct message and incorrect ID
        self.expect_encode_success(
            self.messages.SensorUnsubscribeCmd(
                0,
                0,
                "Pressure",
            ),
            self.sensor_unsubscribe_cmd_json
        )
        # Incorrect device index
        self.expect_encode_fail(
            self.messages.SensorUnsubscribeCmd(
                1,
                0,
                "Pressure",
            ),
            self.sensor_unsubscribe_cmd_json
        )
        # Incorrect sensor index
        self.expect_encode_fail(
            self.messages.SensorUnsubscribeCmd(
                0,
                1,
                "Pressure",
            ),
            self.sensor_unsubscribe_cmd_json
        )
        # Incorrect sensor type
        self.expect_encode_fail(
            self.messages.SensorUnsubscribeCmd(
                0,
                0,
                "Speed",
            ),
            self.sensor_unsubscribe_cmd_json
        )


__all__ = (
    'TestMessagesV0',
    'TestMessagesV1',
    'TestMessagesV2',
    'TestMessagesV3',
)

if __name__ == '__main__':
    main()
