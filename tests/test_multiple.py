# coding: spec

from photons_messages_generator import test_helpers as thp
from photons_messages_generator import field_types as ft
from photons_messages_generator import errors

from delfick_error_pytest import assertRaises

describe "Multiple":
    it "allows multiple of things":
        src = """
            enums:
              SomeEnum:
                type: uint8
                values:
                  - name: SOME_ENUM_ONE
                    value: 1

            fields:
              SomeParams:
                size_bytes: 16
                fields:
                  - name: "One"
                    type: "uint32"
                    size_bytes: 4
                  - name: "Two"
                    type: "[3]uint32"
                    size_bytes: 12

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 264
                  fields:
                    - name: "Enums"
                      type: "[3]<SomeEnum>"
                      size_bytes: 36
                    - name: "Enums2"
                      type: "[3]<SomeEnum>"
                      size_bytes: 36
                    - name: "Numbers"
                      type: "[10]uint8"
                      size_bytes: 80
                    - name: "Params"
                      type: "[3]<SomeParams>"
                      size_bytes: 48
                    - name: "Bts"
                      type: "[32]byte"
                      size_bytes: 32
                    - name: "Strs"
                      type: "[32]byte"
                      size_bytes: 32
                    - name: "Reserved0"
                      type: "[10]uint8"
                      size_bytes: 10
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            multi_options:
              name: Params

          OnePacketExample:
            fields:
              Enums2:
                default: ONE

              Strs:
                string_type: true
        """

        with thp.generate(src, adjustments) as output:
            expected_enums = """
            class SomeEnum(Enum):
                ONE = 1
            """

            expected_fields = """
            # fmt: off

            some_params = [
                  ("one", T.Uint32)
                , ("two", T.Uint32.multiple(3))
                ]

            class Params(dictobj.PacketSpec):
                fields = some_params

            # fmt: on
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("enums", T.Uint8.enum(enums.SomeEnum).multiple(3))
                    , ("enums2", T.Uint8.enum(enums.SomeEnum).multiple(3).default(enums.SomeEnum.ONE))
                    , ("numbers", T.Uint8.multiple(10))
                    , ("params", T.Bytes(128).multiple(3, kls=fields.Params))
                    , ("bts", T.Bytes(32 * 8))
                    , ("strs", T.String(32 * 8))
                    , ("reserved4", T.Reserved(80))
                    )

            # fmt: on

            __all__ = ["OneMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "complains if size bytes and multiples don't line up in a packet field":
        src = """
            fields:
              SomeParams:
                size_bytes: 16
                fields:
                  - name: "One"
                    type: "uint32"
                    size_bytes: 4
                  - name: "Two"
                    type: "[3]uint32"
                    size_bytes: 12

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 144
                  fields:
                    - name: "Things"
                      type: "[3]<SomeParams>"
                      size_bytes: 49
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            multi_options:
              name: Params
        """

        kwargs = {
            "multiple": 3,
            "size_bytes": 49,
            "packet_name": "PacketExample",
            "field_name": "things",
        }
        msg = "Expected size bytes to be divisible by multiple"
        with assertRaises(errors.BadSizeBytes, msg, **kwargs):
            with thp.generate(src, adjustments) as output:
                pass

    it "complains if size bytes and multiples don't line up in a struct field":
        src = """
            fields:
              SomeParams:
                size_bytes: 16
                fields:
                  - name: "One"
                    type: "uint32"
                    size_bytes: 4
                  - name: "Two"
                    type: "[3]uint32"
                    size_bytes: 13

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 144
                  fields:
                    - name: "Things"
                      type: "[3]<SomeParams>"
                      size_bytes: 48
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            multi_options:
              name: Params
        """

        kwargs = {
            "multiple": 3,
            "size_bytes": 13,
            "struct_name": "some_params",
            "field_name": "two",
        }
        msg = "Expected size bytes to be divisible by multiple"
        with assertRaises(errors.BadSizeBytes, msg, **kwargs):
            with thp.generate(src, adjustments) as output:
                pass
