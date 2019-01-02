# coding: spec

from photons_messages_generator.test_helpers import TestCase

describe TestCase, "Without adjustments":
    it "works":
        src = """
            enums:
              SomeEnum:
                type: uint8
                values:
                  - name: "SOME_ENUM_ONE"
                    value: 1
                  - name: "SOME_ENUM_TWO"
                    value: 2

              OtherEnum:
                type: uint32
                values:
                  - name: "OTHER_ENUM_THREE"
                    value: 5
                  - name: "OTHER_ENUM_FOUR"
                    value: 6

            fields:
              SomeParams:
                size_bytes: 12
                fields:
                  - name: "One"
                    type: "[16]byte"
                    size_bytes: 2
                  - name: "Two"
                    type: "[6]byte"
                    size_bytes: 6
                  - name: "Three"
                    type: "uint32"
                    size_bytes: 4

              MoreParams:
                size_bytes: 11
                fields:
                  - name: "Reserved0"
                    type: "Bool"
                    size_bytes: 1
                  - name: "Params"
                    type: "<SomeParams>"
                    size_bytes: 6
                  - name: "Reset"
                    type: "uint32"
                    size_bytes: 4

            packets:
              device:
                DevicePacketOne:
                  pkt_type: 1
                  size_bytes: 0
                  fields: []

                DevicePacketTwo:
                  pkt_type: 2
                  size_bytes: 5
                  fields:
                    - name: "Numbers"
                      type: "<SomeEnum>"
                      size_bytes: 1
                    - name: "Params"
                      type: "<SomeParams>"
                      size_bytes: 54

              other:
                OtherPacketThree:
                  pkt_type: 3
                  size_bytes: 1
                  fields:
                    - type: reserved
                      size_bytes: 1

                OtherPacketFour:
                  pkt_type: 4
                  size_bytes: 13
                  fields:
                    - name: "Reserved0"
                      type: int64
                      size_bytes: 8
                    - name: "Blah"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Reserved1"
                      type: uint32
                      size_bytes: 4
        """

        adjustments = """
        num_reserved_fields_in_frame: 3
        """

        with self.generate(src, adjustments) as output:
            expected_enums = """
            class SomeEnum(Enum):
                ONE = 1
                TWO = 2

            class OtherEnum(Enum):
                THREE = 5
                FOUR = 6
            """


            expected_fields = """
            some_params = (
                  ("one", T.Bytes(2 * 8))
                , ("two", T.Bytes(6 * 8))
                , ("three", T.Uint32)
                )

            more_params = (
                  ("reserved4", T.Reserved(8))
                , *some_params
                , ("reset", T.Uint32)
                )
            """

            expected_messages = """
            ########################
            ###   DEVICE
            ########################

            class DeviceMessages(Messages):
                PacketOne = msg(1)

                PacketTwo = msg(2
                    , ("numbers", T.Uint8.enum(enums.SomeEnum))
                    , *fields.some_params
                    )

            ########################
            ###   OTHER
            ########################

            class OtherMessages(Messages):
                PacketThree = msg(3
                    , ("reserved4", T.Reserved(8))
                    )

                PacketFour = msg(4
                    , ("reserved4", T.Reserved(64))
                    , ("blah", T.Uint8)
                    , ("reserved5", T.Reserved(32))
                    )

            __all__ = ["DeviceMessages", "OtherMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)
