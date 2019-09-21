# coding: spec

from photons_messages_generator import test_helpers as thp

describe "Output":
    it "can generate static at the top of the file and split packets":
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

        output:
         - create: enums
           dest: enums_output.py
           static: |
             from enum import Enum

         - create: fields
           dest: fields_output.py
           static: |
            from photons_protocol.messages import T

            def example():
              pass

         - create: packets
           dest: messages/one.py
           options:
             include: "*"
             exclude: "two"
           static: |
            from photons_messages.frame import msg
            from photons_messages import enums

            from photons_protocol.messages import Messages, T

         - create: packets
           dest: messages/two.py
           options:
             include: "two"
           static: |
            from photons_protocol.messages import Messages, T
        """

        with thp.generate(src, adjustments) as output:
            expected_enums = """
            from enum import Enum

            class SomeEnum(Enum):
                ONE = 1
                TWO = 2
            """

            expected_fields = """
            from photons_protocol.messages import T

            def example():
              pass

            # fmt: off

            some_params = [
                  ("one", T.Uint8.enum(enums.SomeEnum))
                ]

            # fmt: on
            """

            expected_one = """
            from photons_messages.frame import msg
            from photons_messages import enums

            from photons_protocol.messages import Messages, T

            # fmt: off

            ########################
            ###   ONE
            ########################

            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Uint8)
                    )

            # fmt: on

            __all__ = ["OneMessages"]
            """

            expected_two = """
            from photons_protocol.messages import Messages, T

            # fmt: off

            ########################
            ###   TWO
            ########################

            class TwoMessages(Messages):
                PacketThing = msg(2
                    , ("one", T.Uint8)
                    )

            # fmt: on

            __all__ = ["TwoMessages"]
            """

            output.assertFileContents("enums_output.py", expected_enums)
            output.assertFileContents("fields_output.py", expected_fields)
            output.assertFileContents("messages/one.py", expected_one)
            output.assertFileContents("messages/two.py", expected_two)
