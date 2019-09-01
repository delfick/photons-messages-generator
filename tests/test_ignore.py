# coding: spec

from photons_messages_generator.test_helpers import TestCase
from photons_messages_generator import errors

describe TestCase, "ignoring structs":
    it "can replace existing structs with just bytes":
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
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "<SomeParams>"
                      size_bytes: 1

              two:
                TwoPacketThing:
                  pkt_type: 2
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "[3]<SomeParams>"
                      size_bytes: 3
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        ignore:
          SomeParams: {}
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Bytes(1 * 8))
                    )
            
            ########################
            ###   TWO
            ########################
            
            class TwoMessages(Messages):
                PacketThing = msg(2
                    , ("one", T.Bytes(3 * 8))
                    )

            # fmt: on
            
            __all__ = ["OneMessages", "TwoMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "replaced fields can have extras and defaults":
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
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "<SomeParams>"
                      size_bytes: 1

              two:
                TwoPacketThing:
                  pkt_type: 2
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "[3]<SomeParams>"
                      size_bytes: 3

                TwoPacketBlah:
                  pkt_type: 3
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "[3]<NotThereParams>"
                      size_bytes: 9
                    - name: "Field"
                      type: "<NotThereParams>"
                      size_bytes: 3
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        ignore:
          SomeParams: {}
          NotThereParams: {}

        changes:
          OnePacketExample:
            fields:
              One:
                default: "b'yeap'"
                extras: "dynamic()"

          TwoPacketThing:
            fields:
              One:
                default: "b'stuff'"
                extras: "transform()"

          TwoPacketBlah:
            fields:
              One:
                default: "b'things'"
                extras: "other()"
              Field:
                default: "b'field'"
                extras: "option()"
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Bytes(1 * 8).default(b'yeap').dynamic())
                    )
            
            ########################
            ###   TWO
            ########################
            
            class TwoMessages(Messages):
                PacketThing = msg(2
                    , ("one", T.Bytes(3 * 8).default(b'stuff').transform())
                    )

                PacketBlah = msg(3
                    , ("one", T.Bytes(9 * 8).default(b'things').other())
                    , ("field", T.Bytes(3 * 8).default(b'field').option())
                    )

            # fmt: on
            
            __all__ = ["OneMessages", "TwoMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can expand a struct":
        src = """
            fields:
              SomeParams:
                size_bytes: 9
                fields:
                  - name: "Option"
                    type: "uint8"
                    size_bytes: 1
                  - name: "Setting"
                    type: "int64"
                    size_bytes: 8

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 1
                  fields:
                    - name: "One"
                      type: "<SomeParams>"
                      size_bytes: 1

              two:
                TwoPacketThing:
                  pkt_type: 2
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "[3]<SomeParams>"
                      size_bytes: 3
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        ignore:
          SomeParams:
            expanded: true
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one_option", T.Uint8)
                    , ("one_setting", T.Int64)
                    )
            
            ########################
            ###   TWO
            ########################
            
            class TwoMessages(Messages):
                PacketThing = msg(2
                    , ("one", T.Bytes(8 * 3))
                    )

            # fmt: on
            
            __all__ = ["OneMessages", "TwoMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can replace structs that don't exist":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 30
                  fields:
                    - name: "One"
                      type: "<SomeParams>"
                      size_bytes: 10
                    - name: "Two"
                      type: "[2]<SomeParams>"
                      size_bytes: 20
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        ignore:
          SomeParams: {}
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            """

            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("one", T.Bytes(10 * 8))
                    , ("two", T.Bytes(20 * 8))
                    )

            # fmt: on

            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can't expand a struct that doesn't exist":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 30
                  fields:
                    - name: "One"
                      type: "<SomeParams>"
                      size_bytes: 10
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        ignore:
          SomeParams:
            expanded: true
        """

        with self.fuzzyAssertRaisesError(errors.NoSuchType, wanted='SomeParams'):
            with self.generate(src, adjustments) as output:
                pass
