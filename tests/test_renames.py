# coding: spec

from photons_messages_generator.test_helpers import TestCase
from photons_messages_generator import errors

import keyword

describe TestCase, "renames":
    it "auto renames packets and fields":
        src = """
            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "OneThing"
                    type: "uint8"
                    size_bytes: 1

            packets:
              one:
                OneGet:
                  pkt_type: 1
                  size_bytes: 0
                  fields: []

                OneSet:
                  pkt_type: 2
                  size_bytes: 0
                  fields: []

                OneState:
                  pkt_type: 3
                  size_bytes: 0
                  fields: []

                OneGetThings:
                  pkt_type: 4
                  size_bytes: 1
                  fields:
                    - name: "TheField"
                      type: "uint8"
                      size_bytes: 1

                OneSetThings:
                  pkt_type: 4
                  size_bytes: 1
                  fields:
                    - name: "TheField"
                      type: "uint8"
                      size_bytes: 1

                OneStateThings:
                  pkt_type: 4
                  size_bytes: 1
                  fields:
                    - name: "TheField"
                      type: "uint8"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params = (
                  ("one_thing", T.Uint8)
                )
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                GetOne = msg(1)

                SetOne = msg(2)

                OneState = msg(3)

                GetThings = msg(4
                    , ("the_field", T.Uint8)
                    )

                SetThings = msg(4
                    , ("the_field", T.Uint8)
                    )

                StateThings = msg(4
                    , ("the_field", T.Uint8)
                    )

            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can rename enums":
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
                OnePacketWithEnum:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "Enum"
                      type: "<SomeEnum>"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeEnum:
            rename: "RenamedEnum"
        """

        with self.generate(src, adjustments) as output:
            expected_enums = """
            class RenamedEnum(Enum):
                ONE = 1
                TWO = 2
            """

            expected_fields = """
            some_params = (
                  ("one", T.Uint8.enum(enums.RenamedEnum))
                )
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                PacketWithEnum = msg(1
                    , ("enum", T.Uint8.enum(enums.RenamedEnum))
                    )

            __all__ = ["OneMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can rename structs":
        src = """
            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "One"
                    type: "uint8"
                    size_bytes: 1

              OtherParams:
                size_bytes: 5
                fields:
                  - name: "Blah"
                    type: "uint32"
                    size_bytes: 4
                  - name: "Params"
                    type: "<SomeParams>"
                    size_bytes: 1

              MoreParams:
                size_bytes: 3
                fields:
                  - name: "Params"
                    type: "[3]<SomeParams>"
                    size_bytes: 3

            packets:
              one:
                OnePacketWithStruct:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "Params"
                      type: "<SomeParams>"
                      size_bytes: 1
                    - name: "ManyParams"
                      type: "[3]<SomeParams>"
                      size_bytes: 3
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            rename: "renamed_params"
            many_options:
              name: "RenamedParamsKls"
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            renamed_params = (
                  ("one", T.Uint8)
                )

            class RenamedParamsKls(dictobj.PacketSpec):
                fields = renamed_params

            other_params = (
                  ("blah", T.Uint32)
                , *renamed_params
                )

            more_params = (
                  ("params", T.Bytes(8 * 3).many(lambda pkt: RenamedParamsKls))
                )
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                PacketWithStruct = msg(1
                    , *fields.renamed_params
                    , ("many_params", T.Bytes(8 * 3).many(lambda pkt: fields.RenamedParamsKls))
                    )

            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can rename structs fields":
        src = """
            fields:
              SomeParams:
                size_bytes: 1
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
                rename: hello
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params = (
                  ("hello", T.Uint8)
                )
            """

            output.assertFileContents("fields.py", expected_fields)

    it "can rename structs fields on renamed structs":
        src = """
            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "One"
                    type: "uint8"
                    size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            rename: example_params

            fields:
              One:
                rename: hello
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            example_params = (
                  ("hello", T.Uint8)
                )
            """

            output.assertFileContents("fields.py", expected_fields)

    it "cannot rename struct field to invalid name":
        src = """
            fields:
              SomeParams:
                size_bytes: 1
                fields:
                  - name: "One"
                    type: "uint8"
                    size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        invalid_field_names: ["payload"]

        changes:
          SomeParams:
            fields:
              One:
                rename: Payload
        """

        msg = "Fields cannot be one of the invalid field names"
        kwargs = {"field": "payload", "parent": "SomeParams", "invalid_names": ["payload"]}
        with self.fuzzyAssertRaisesError(errors.InvalidName, msg, **kwargs):
            with self.generate(src, adjustments) as output:
                pass

    it "cannot rename struct field to reserved keywords":
        src = """
            fields:
              SomeParams:
                size_bytes: 1
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
                rename: Finally
        """

        msg = "Field names cannot be reserved python keywords"
        kwargs = {"field": "finally", "parent": "SomeParams", "invalid_names": keyword.kwlist}
        with self.fuzzyAssertRaisesError(errors.InvalidName, msg, **kwargs):
            with self.generate(src, adjustments) as output:
                pass

    it "can rename packets":
        src = """
            fields:
              SomeParams:
                size_bytes: 3
                fields:
                  - name: "One"
                    type: "<OnePacketExample>"
                    size_bytes: 3

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Two"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Three"
                      type: "uint8"
                      size_bytes: 1

                OnePacketExampleTwo:
                  pkt_type: 2
                  size_bytes: 3
                  fields:
                    - name: "Field"
                      type: <OnePacketExample>
                      size_bytes: 3
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OnePacketExample:
            rename: "ExamplePacket"
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params = (
                  ("one_one", T.Uint8)
                , ("one_two", T.Uint8)
                , ("one_three", T.Uint8)
                )
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                ExamplePacket = msg(1
                    , ("one", T.Uint8)
                    , ("two", T.Uint8)
                    , ("three", T.Uint8)
                    )

                PacketExampleTwo = msg(2
                    , ("field_one", T.Uint8)
                    , ("field_two", T.Uint8)
                    , ("field_three", T.Uint8)
                    )

            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can rename packet fields":
        src = """
            fields:
              SomeParams:
                size_bytes: 3
                fields:
                  - name: "One"
                    type: "<OnePacketExample>"
                    size_bytes: 3
                  - name: "Two"
                    type: "<OnePacketExampleTwo>"
                    size_bytes: 1

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Two"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Three"
                      type: "uint8"
                      size_bytes: 1

                OnePacketExampleTwo:
                  pkt_type: 2
                  size_bytes: 1
                  fields:
                    - name: "Field"
                      type: uint8
                      size_bytes: 1

                OnePacketExampleThree:
                  pkt_type: 2
                  size_bytes: 1
                  fields:
                    - name: "Attr"
                      type: <OnePacketExampleTwo>
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OnePacketExample:
            fields:
              Three:
                rename: "Four"

          OnePacketExampleTwo:
            rename: Different
            fields:
              Field:
                rename: Stuff
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params = (
                  ("one_one", T.Uint8)
                , ("one_two", T.Uint8)
                , ("one_four", T.Uint8)
                , ("two_stuff", T.Uint8)
                )
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Uint8)
                    , ("two", T.Uint8)
                    , ("four", T.Uint8)
                    )

                Different = msg(2
                    , ("stuff", T.Uint8)
                    )

                PacketExampleThree = msg(2
                    , ("attr_stuff", T.Uint8)
                    )

            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can rename namespaces":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1

              two:
                TwoPacketThing:
                  pkt_type: 2
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        rename_namespaces:
            two: other

        output:
         - create: enums
           dest: enums.py
         - create: fields
           dest: fields.py
         - create: packets
           dest: messages.py
           options:
             include: "*"
             exclude: "other"
         - create: packets
           dest: other.py
           options:
             include: "other"
        """

        with self.generate(src, adjustments) as output:
            expected_messages = """
            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Uint8)
                    )

            __all__ = ["OneMessages"]
            """

            expected_other = """
            ########################
            ###   OTHER
            ########################

            class OtherMessages(Messages):
                PacketThing = msg(2
                    , ("one", T.Uint8)
                    )

            __all__ = ["OtherMessages"]
            """

            output.assertFileContents("messages.py", expected_messages)
            output.assertFileContents("other.py", expected_other)

    it "cannot rename packet field to invalid name":
        src = """
            packets:
              one:
                OnePacket:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        invalid_field_names: ["payload", "fields"]

        changes:
          OnePacket:
            fields:
              One:
                rename: fields
        """

        msg = "Fields cannot be one of the invalid field names"
        kwargs = {"field": "fields", "parent": "OnePacket", "invalid_names": ["payload", "fields"]}
        with self.fuzzyAssertRaisesError(errors.InvalidName, msg, **kwargs):
            with self.generate(src, adjustments) as output:
                pass

    it "cannot rename packet field to invalid name":
        src = """
            packets:
              one:
                OnePacket:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OnePacket:
            fields:
              One:
                rename: finally
        """

        msg = "Field names cannot be reserved python keywords"
        kwargs = {"field": "finally", "parent": "OnePacket", "invalid_names": keyword.kwlist}
        with self.fuzzyAssertRaisesError(errors.InvalidName, msg, **kwargs):
            with self.generate(src, adjustments) as output:
                pass

    it "can put a packet into a different namespace":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1

                OnePacketThing:
                  pkt_type: 2
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OnePacketExample:
            namespace: core

        """

        with self.generate(src, adjustments) as output:
            expected_messages = """
            ########################
            ###   CORE
            ########################

            class CoreMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Uint8)
                    )

            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                PacketThing = msg(2
                    , ("one", T.Uint8)
                    )

            __all__ = ["CoreMessages", "OneMessages"]
            """

            output.assertFileContents("messages.py", expected_messages)
