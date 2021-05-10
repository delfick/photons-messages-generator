# coding: spec

from photons_messages_generator import test_helpers as thp


describe "Unions":
    it "allows unions!":
        src = """
            enums:
              Choice:
                type: uint8
                values:
                  - name: CHOICE_ONE
                    value: 1
                  - name: CHOICE_TWO
                    value: 2
                  - name: CHOICE_THREE
                    value: 3
                  - name: CHOICE_FOUR
                    value: 4

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

              OtherParams:
                size_bytes: 4
                fields:
                  - name: "Blah"
                    type: "uint32"
                    size_bytes: 4

            unions:
              Data:
                size_bytes: 16
                fields:
                  - name: "One"
                    type: "[16]uint8"
                    size_bytes: 16
                  - name: "Two"
                    type: "<SomeParams>"
                    size_bytes: 16
                  - name: "Three"
                    type: "[4]<OtherParams>"
                    size_bytes: 16
                  - name: "Four"
                    type: "[16]byte"
                    size_bytes: 16

            packets:
              one:
                OnePacketWithUnionExample:
                  pkt_type: 1
                  size_bytes: 17
                  fields:
                    - name: "Choice"
                      type: "<Choice>"
                      size_bytes: 1
                    - name: "Value"
                      type: "<Data>"
                      size_bytes: 16
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          SomeParams:
            multi_options:
              name: Params
            fields:
              One:
                default: "0"
              Two:
                default: "1"

          OtherParams:
            multi_options:
              name: Other

          OnePacketWithUnionExample:
            fields:
              Value:
                union_enum: Choice
                union_switch_field: choice

          Data:
            fields:
              One:
                default: "20"
              Four:
                extras: "default(b'')"
        """

        with thp.generate(src, adjustments) as output:
            expected_enums = """
            class Choice(Enum):
                ONE = 1
                TWO = 2
                THREE = 3
                FOUR = 4
            """

            expected_fields = """
            # fmt: off
            
            
            def union_fields_Data(typ):
                if typ is enums.Choice.ONE:
                    yield from (("one", T.Uint8.multiple(16).default(20)), )
                if typ is enums.Choice.TWO:
                    yield from (*some_params, )
                if typ is enums.Choice.THREE:
                    yield from (("three", T.Bytes(32).multiple(4, kls=Other)), )
                if typ is enums.Choice.FOUR:
                    yield from (("four", T.Bytes(16 * 8).default(b'')), )
            
            
            some_params = [
                  ("one", T.Uint32.default(0))
                , ("two", T.Uint32.multiple(3).default(1))
                ]
            
            class Params(dictobj.PacketSpec):
                fields = some_params
            
            other_params = [
                  ("blah", T.Uint32)
                ]
            
            class Other(dictobj.PacketSpec):
                fields = other_params
            
            # fmt: on
            """

            expected_messages = """
            # fmt: off
            
            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketWithUnionExample = msg(1
                    , ("choice", T.Uint8.enum(enums.Choice))
                    , ("value", T.Bytes(16 * 8).dynamic(lambda pkt: fields.union_fields_Data(pkt.choice)))
                    )
            
            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("enums.py", expected_enums)
            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)
