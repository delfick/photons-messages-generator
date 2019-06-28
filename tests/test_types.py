# coding: spec

from photons_messages_generator.test_helpers import TestCase
from photons_messages_generator import field_types as ft
from photons_messages_generator import errors

describe TestCase, "Types":
    it "complains about structs used as multiple without many_options":
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

        msg = "Struct some_params is used in a .many block but has no many_name specified"
        with self.fuzzyAssertRaisesError(errors.ExpectedManyName, msg):
            with self.generate(src, adjustments) as output:
                pass

    it "complains about enums as multiples":
        src = """
            enums:
              SomeEnum:
                type: uint8
                values:
                  - name: ONE
                    value: 1

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 3
                  fields:
                    - name: "Params"
                      type: "[3]<SomeEnum>"
                      size_bytes: 3
        """

        adjustments = """
        num_reserved_fields_in_frame: 3
        """

        msg = "Enums cannot be multiple"
        kwargs = {"wanted": 3}
        with self.fuzzyAssertRaisesError(errors.NonsensicalMultiplier, msg, **kwargs):
            with self.generate(src, adjustments) as output:
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
        with self.fuzzyAssertRaisesError(errors.CyclicPacketField, **kwargs):
            with self.generate(src, adjustments) as output:
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

        with self.generate(src, adjustments) as output:
            expected_fields = """
            duration_type = T.Uint32.default(0).transform(
                  lambda _, value: int(1000 * float(value))
                , lambda value: float(value) / 1000
                ).allow_float()
            
            some_params = [
                  ("one", duration_type)
                ]
            """

            expected_messages = """
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
        with self.fuzzyAssertRaisesError(errors.UnknownSpecialType, **kwargs):
            with self.generate(src, adjustments) as output:
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
            with self.generate(src, adjustments) as output:
                pass
            assert False, "Expected an exception"
        except errors.NotSameType as error:
            self.assertEqual(error.message, msg)
            self.assertEqual(error.kwargs["name"], "SomeParams")
            self.assertEqual(error.kwargs["should_be"].val, "uint8")
            self.assertEqual(error.kwargs["want"].options.name, "duration_type")

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
        with self.fuzzyAssertRaisesError(errors.CantBeString, msg, name="SomeParams"):
            with self.generate(src, adjustments) as output:
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

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params = [
                  ("one", T.String(5 * 8).default("hello").optional())
                ]
            """

            expected_messages = """
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

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params = [
                  ("one", T.Blah().default(0).transform())
                ]
            """

            expected_messages = """
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

        with self.generate(src, adjustments) as output:
            expected_fields = """
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
            """

            expected_messages = """
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
        with self.fuzzyAssertRaisesError(errors.InvalidBits, msg, field="One", packet="SomeParams"):
            with self.generate(src, adjustments) as output:
                pass

    it "can understand defaults for enums":
        src ="""
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

        with self.generate(src, adjustments) as output:
            expected_enums = """
            class SomeEnum(Enum):
                ONE = 1
                TWO = 2
            """

            expected_fields = """
            some_params = [
                  ("one", T.Uint8.enum(enums.SomeEnum).default(enums.SomeEnum.ONE))
                ]
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Uint8.enum(enums.SomeEnum).default(enums.SomeEnum.TWO))
                    )
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "complains if default is not an enum value":
        src ="""
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

        kwargs = {
              "available": ["ONE", "TWO"]
            , "enum": "SomeEnum"
            , "wanted": "WAT"
            }

        with self.fuzzyAssertRaisesError(errors.NoSuchEnumValue, **kwargs):
            with self.generate(src, adjustments) as output:
                pass

    it "can understand unknown values for enums":
        src ="""
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

        with self.generate(src, adjustments) as output:
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
            some_params = [
                  ("one", T.Uint8.enum(enums.SomeEnum, allow_unknown=True))
                , ("two", T.Uint8.enum(enums.SomeOtherEnum))
                , ("three", T.Uint8.enum(enums.SomeEnum, allow_unknown=True).default(enums.SomeEnum.ONE))
                ]
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("four", T.Uint8.enum(enums.AnotherEnum))
                    , ("five", T.Uint8.enum(enums.BestEnum, allow_unknown=True))
                    , ("six", T.Uint8.enum(enums.BestEnum, allow_unknown=True).default(enums.BestEnum.EIGHT))
                    )
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)
