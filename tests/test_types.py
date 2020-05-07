# coding: spec

from photons_messages_generator import test_helpers as thp
from photons_messages_generator import errors

from delfick_project.errors_pytest import assertRaises

describe "Types":
    it "complains about structs used as multiple without multiple_options":
        src = """
            fields:
              SomeParams:
                size_bytes: 4
                fields:
                  - name: "One"
                    type: "uint32"
                    size_bytes: 4

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 3
                  fields:
                    - name: "Params"
                      type: "[3]<SomeParams>"
                      size_bytes: 3
        """

        adjustments = """
        num_reserved_fields_in_frame: 3
        """

        msg = "Struct some_params is used in a .multiple block but has no multi_name specified"
        with assertRaises(errors.ExpectedMultiName, msg):
            with thp.generate(src, adjustments):
                pass

    it "complains about cycle packets":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 4
                  fields:
                    - name: "Params"
                      type: "<OneOtherPacket>"
                      size_bytes: 4

                OneOtherPacket:
                  pkt_type: 2
                  size_bytes: 4
                  fields:
                    - name: "Params"
                      type: "<OnePacketExample>"
                      size_bytes: 4
        """

        adjustments = """
        num_reserved_fields_in_frame: 3
        """

        kwargs = {"chain": ["OneOtherPacket", "OnePacketExample"]}
        with assertRaises(errors.CyclicPacketField, **kwargs):
            with thp.generate(src, adjustments):
                pass

    it "can replace a field":
        src = """
            fields:
              SomeParams:
                size_bytes: 4
                fields:
                  - name: "One"
                    type: "uint32"
                    size_bytes: 4

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 8
                  fields:
                    - name: "Duration"
                      type: "uint32"
                      size_bytes: 4
                    - name: "Params"
                      type: "<SomeParams>"
                      size_bytes: 4

                OneOtherPacket:
                  pkt_type: 2
                  size_bytes: 8
                  fields:
                    - name: "thing"
                      type: "<OnePacketExample>"
                      size_bytes: 8
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        types:
          duration_type:
            type: uint32
            size_bytes: 4
            default: "0"
            extras:
              - |
                transform(
                      lambda _, value: int(1000 * float(value))
                    , lambda value: float(value) / 1000
                    )
              - "allow_float()"

        changes:
          SomeParams:
            fields:
              One:
                special_type: duration_type

          OnePacketExample:
            fields:
              Duration:
                special_type: duration_type
        """

        with thp.generate(src, adjustments) as output:
            expected_fields = """
            # fmt: off

            duration_type = T.Uint32.default(0).transform(
                  lambda _, value: int(1000 * float(value))
                , lambda value: float(value) / 1000
                ).allow_float()
            
            some_params = [
                  ("one", duration_type)
                ]

            # fmt: on
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("duration", fields.duration_type)
                    , *fields.some_params
                    )
            
                OtherPacket = msg(2
                    , ("thing_duration", fields.duration_type)
                    , ("thing_one", fields.duration_type)
                    )

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "complains if special type doesn't exist":
        src = """
            fields:
              SomeParams:
                size_bytes: 4
                fields:
                  - name: "One"
                    type: "uint8"
                    size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                special_type: duration_type
        """

        kwargs = {"available": [], "wanted": "duration_type"}
        with assertRaises(errors.UnknownSpecialType, **kwargs):
            with thp.generate(src, adjustments):
                pass

    it "complains if replacing a field with different type":
        src = """
            fields:
              SomeParams:
                size_bytes: 4
                fields:
                  - name: "One"
                    type: "uint8"
                    size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        types:
          duration_type:
            type: uint32
            size_bytes: 4
            default: "0"
            extras:
              - |
                transform(
                      lambda _, value: int(1000 * float(value))
                    , lambda value: float(value) / 1000
                    )
              - "allow_float()"

        changes:
          SomeParams:
            fields:
              One:
                special_type: duration_type
        """

        msg = "Tried to set type to something that is wrong"
        try:
            with thp.generate(src, adjustments):
                pass
            assert False, "Expected an exception"
        except errors.NotSameType as error:
            assert error.message == msg
            assert error.kwargs["name"] == "SomeParams"
            assert error.kwargs["should_be"].val == "uint8"
            assert error.kwargs["want"].options.name == "duration_type"

    it "complains if replacing a non bytes field with a string type":
        src = """
            fields:
              SomeParams:
                size_bytes: 4
                fields:
                  - name: "One"
                    type: "uint8"
                    size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                string_type: true
        """

        msg = "Only bytes can be turned into string"
        with assertRaises(errors.CantBeString, msg, name="SomeParams"):
            with thp.generate(src, adjustments):
                pass

    it "can replace bytes with a string":
        src = """
            fields:
              SomeParams:
                size_bytes: 5
                fields:
                  - name: "One"
                    type: "[5]byte"
                    size_bytes: 5

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 7
                  fields:
                    - name: "Value"
                      type: "[3]byte"
                      size_bytes: 3
                    - name: "Params"
                      type: "<SomeParams>"
                      size_bytes: 4

                OneOtherPacket:
                  pkt_type: 2
                  size_bytes: 8
                  fields:
                    - name: "thing"
                      type: "<OnePacketExample>"
                      size_bytes: 8
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                string_type: true
                default: '"hello"'
                extras: "optional()"

          OnePacketExample:
            fields:
              Value:
                string_type: true
        """

        with thp.generate(src, adjustments) as output:
            expected_fields = """
            # fmt: off

            some_params = [
                  ("one", T.String(5 * 8).default("hello").optional())
                ]

            # fmt: on
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("value", T.String(3 * 8))
                    , *fields.some_params
                    )
            
                OtherPacket = msg(2
                    , ("thing_value", T.String(3 * 8))
                    , ("thing_one", T.String(5 * 8).default("hello").optional())
                    )

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can replace type with something arbitrary":
        src = """
            fields:
              SomeParams:
                size_bytes: 5
                fields:
                  - name: "One"
                    type: "[5]byte"
                    size_bytes: 5

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 7
                  fields:
                    - name: "Value"
                      type: "[3]byte"
                      size_bytes: 3
                    - name: "Params"
                      type: "<SomeParams>"
                      size_bytes: 4

                OneOtherPacket:
                  pkt_type: 2
                  size_bytes: 8
                  fields:
                    - name: "thing"
                      type: "<OnePacketExample>"
                      size_bytes: 8
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                override_type: "T.Blah()"
                default: "0"
                extras: "transform()"

          OnePacketExample:
            fields:
              Value:
                override_type: "T.Other()"
        """

        with thp.generate(src, adjustments) as output:
            expected_fields = """
            # fmt: off

            some_params = [
                  ("one", T.Blah().default(0).transform())
                ]

            # fmt: on
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("value", T.Other())
                    , *fields.some_params
                    )
            
                OtherPacket = msg(2
                    , ("thing_value", T.Other())
                    , ("thing_one", T.Blah().default(0).transform())
                    )

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can replace an item with Bool values":
        src = """
            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "One"
                    type: "uint8"
                    size_bytes: 1

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 5
                  fields:
                    - name: "Value"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Params"
                      type: "<SomeParams>"
                      size_bytes: 4

                OneOtherPacket:
                  pkt_type: 2
                  size_bytes: 5
                  fields:
                    - name: "thing"
                      type: "<OnePacketExample>"
                      size_bytes: 5
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                bits:
                 - One
                 - Two
                 - Three
                 - Four
                 - Five
                 - Six
                 - Seven
                 - Eight

          OnePacketExample:
            fields:
              Value:
                bits:
                  - Hello
                  - There
                  - This
                  - IsA
                  - Very
                  - Great
                  - Test
                  - Yeah
        """

        with thp.generate(src, adjustments) as output:
            expected_fields = """
            # fmt: off

            some_params = [
                  ("one", T.Bool)
                , ("two", T.Bool)
                , ("three", T.Bool)
                , ("four", T.Bool)
                , ("five", T.Bool)
                , ("six", T.Bool)
                , ("seven", T.Bool)
                , ("eight", T.Bool)
                ]

            # fmt: on
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("hello", T.Bool)
                    , ("there", T.Bool)
                    , ("this", T.Bool)
                    , ("is_a", T.Bool)
                    , ("very", T.Bool)
                    , ("great", T.Bool)
                    , ("test", T.Bool)
                    , ("yeah", T.Bool)
                    , *fields.some_params
                    )
            
                OtherPacket = msg(2
                    , ("thing_hello", T.Bool)
                    , ("thing_there", T.Bool)
                    , ("thing_this", T.Bool)
                    , ("thing_is_a", T.Bool)
                    , ("thing_very", T.Bool)
                    , ("thing_great", T.Bool)
                    , ("thing_test", T.Bool)
                    , ("thing_yeah", T.Bool)
                    , ("thing_one", T.Bool)
                    , ("thing_two", T.Bool)
                    , ("thing_three", T.Bool)
                    , ("thing_four", T.Bool)
                    , ("thing_five", T.Bool)
                    , ("thing_six", T.Bool)
                    , ("thing_seven", T.Bool)
                    , ("thing_eight", T.Bool)
                    )

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "complains if replacing a value with not enough bits":
        src = """
            fields:
              SomeParams:
                size_bytes: 4
                fields:
                  - name: "One"
                    type: "uint32"
                    size_bytes: 4
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                bits:
                 - One
                 - Two
                 - Three
                 - Four
                 - Five
                 - Six
                 - Seven
                 - Eight
        """

        msg = "Need 32 options but only have 8"
        with assertRaises(errors.InvalidBits, msg, field="One", packet="SomeParams"):
            with thp.generate(src, adjustments):
                pass

    it "can understand defaults for enums":
        src = """
            enums:
              SomeEnum:
                type: uint8
                values:
                  - name: "SOME_ENUM_ONE"
                    value: 1
                  - name: "SOME_ENUM_TWO"
                    value: 2

            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "One"
                    type: "<SomeEnum>"
                    size_bytes: 1

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "<SomeEnum>"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                default: "ONE"

          OnePacketExample:
            fields:
              One:
                default: "TWO"
        """

        with thp.generate(src, adjustments) as output:
            expected_enums = """
            class SomeEnum(Enum):
                ONE = 1
                TWO = 2
            """

            expected_fields = """
            # fmt: off

            some_params = [
                  ("one", T.Uint8.enum(enums.SomeEnum).default(enums.SomeEnum.ONE))
                ]

            # fmt: on
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Uint8.enum(enums.SomeEnum).default(enums.SomeEnum.TWO))
                    )

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "complains if default is not an enum value":
        src = """
            enums:
              SomeEnum:
                type: uint8
                values:
                  - name: "SOME_ENUM_ONE"
                    value: 1
                  - name: "SOME_ENUM_TWO"
                    value: 2

            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "One"
                    type: "<SomeEnum>"
                    size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                default: "WAT"
        """

        kwargs = {"available": ["ONE", "TWO"], "enum": "SomeEnum", "wanted": "WAT"}

        with assertRaises(errors.NoSuchEnumValue, **kwargs):
            with thp.generate(src, adjustments):
                pass

    it "can understand unknown values for enums":
        src = """
            enums:
              SomeEnum:
                type: uint8
                values:
                  - name: "SOME_ENUM_ONE"
                    value: 1
                  - name: "SOME_ENUM_TWO"
                    value: 2

              SomeOtherEnum:
                type: uint8
                values:
                  - name: "SOME_OTHER_ENUM_THREE"
                    value: 3
                  - name: "SOME_OTHER_ENUM_FOUR"
                    value: 4

              AnotherEnum:
                type: uint8
                values:
                  - name: "ANOTHER_ENUM_FIVE"
                    value: 5
                  - name: "ANOTHER_ENUM_SIX"
                    value: 6

              BestEnum:
                type: uint8
                values:
                  - name: "BEST_ENUM_SEVEN"
                    value: 7
                  - name: "BEST_ENUM_EIGHT"
                    value: 8

            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "One"
                    type: "<SomeEnum>"
                    size_bytes: 1
                  - name: "Two"
                    type: "<SomeOtherEnum>"
                    size_bytes: 1
                  - name: "Three"
                    type: "<SomeEnum>"
                    size_bytes: 1

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "Four"
                      type: "<AnotherEnum>"
                      size_bytes: 1
                    - name: "Five"
                      type: "<BestEnum>"
                      size_bytes: 1
                    - name: "Six"
                      type: "<BestEnum>"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            fields:
              One:
                allow_unknown_enums: true
              Three:
                default: ONE
                allow_unknown_enums: true

          OnePacketExample:
            fields:
              Five:
                allow_unknown_enums: true
              Six:
                default: EIGHT
                allow_unknown_enums: true
        """

        with thp.generate(src, adjustments) as output:
            expected_enums = """
            class SomeEnum(Enum):
                ONE = 1
                TWO = 2

            class SomeOtherEnum(Enum):
                THREE = 3
                FOUR = 4

            class AnotherEnum(Enum):
                FIVE = 5
                SIX = 6

            class BestEnum(Enum):
                SEVEN = 7
                EIGHT = 8
            """

            expected_fields = """
            # fmt: off

            some_params = [
                  ("one", T.Uint8.enum(enums.SomeEnum, allow_unknown=True))
                , ("two", T.Uint8.enum(enums.SomeOtherEnum))
                , ("three", T.Uint8.enum(enums.SomeEnum, allow_unknown=True).default(enums.SomeEnum.ONE))
                ]

            # fmt: on
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("four", T.Uint8.enum(enums.AnotherEnum))
                    , ("five", T.Uint8.enum(enums.BestEnum, allow_unknown=True))
                    , ("six", T.Uint8.enum(enums.BestEnum, allow_unknown=True).default(enums.BestEnum.EIGHT))
                    )

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)
