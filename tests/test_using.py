# coding: spec

from photons_messages_generator import test_helpers as thp
from photons_messages_generator import errors

from delfick_project.errors_pytest import assertRaises

describe "Using helper":
    it "can replace packets with a using construct":
        src = """
            packets:
              one:
                OneSetPacket:
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

                OneStatePacket:
                  pkt_type: 2
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
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OneStatePacket:
            using: OneSetPacket
        """

        with thp.generate(src, adjustments) as output:
            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                SetPacket = msg(1
                    , ("one", T.Uint8)
                    , ("two", T.Uint8)
                    , ("three", T.Uint8)
                    )
            
                StatePacket = SetPacket.using(2)

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("messages.py", expected_messages)

    it "can replace packets with a using construct when original has extras and defaults":
        src = """
            packets:
              one:
                OneSetPacket:
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

                OneStatePacket:
                  pkt_type: 2
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
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OneSetPacket:
            fields:
              One:
                default: "0"
                extras: "optional()"
              Two:
                default: "20"
                extras: "dynamic()"
          OneStatePacket:
            using: OneSetPacket
        """

        with thp.generate(src, adjustments) as output:
            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                SetPacket = msg(1
                    , ("one", T.Uint8.default(0).optional())
                    , ("two", T.Uint8.default(20).dynamic())
                    , ("three", T.Uint8)
                    )
            
                StatePacket = SetPacket.using(2)

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("messages.py", expected_messages)

    it "complains if fields are different names":
        src = """
            packets:
              one:
                OneSetPacket:
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

                OneStatePacket:
                  pkt_type: 2
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Two"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Four"
                      type: "uint8"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OneStatePacket:
            using: OneSetPacket
        """

        msg = "The two packets have different field names"
        kwargs = {"OneSetPacket": ["One", "Two", "Three"], "OneStatePacket": ["One", "Two", "Four"]}
        with assertRaises(errors.BadUsingInstruction, msg, **kwargs):
            with thp.generate(src, adjustments):
                pass

    it "complains if different number of fields":
        src = """
            packets:
              one:
                OneSetPacket:
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

                OneStatePacket:
                  pkt_type: 2
                  size_bytes: 3
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Two"
                      type: "uint8"
                      size_bytes: 1
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OneStatePacket:
            using: OneSetPacket
        """

        msg = "The two packets have different field names"
        kwargs = {"OneSetPacket": ["One", "Two", "Three"], "OneStatePacket": ["One", "Two"]}
        with assertRaises(errors.BadUsingInstruction, msg, **kwargs):
            with thp.generate(src, adjustments):
                pass

    it "complains if fields are different types":
        src = """
            packets:
              one:
                OneSetPacket:
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

                OneStatePacket:
                  pkt_type: 2
                  size_bytes: 6
                  fields:
                    - name: "One"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Two"
                      type: "uint8"
                      size_bytes: 1
                    - name: "Three"
                      type: "uint32"
                      size_bytes: 4
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OneStatePacket:
            using: OneSetPacket
        """

        msg = "The two packets have different field types"

        field_on_set = "\n<<\n\tname: Three\n\ttype: uint8\n>>\n"
        field_on_state = "\n<<\n\tname: Three\n\ttype: uint32\n>>\n"
        kwargs = {"OneSetPacket": field_on_set, "OneStatePacket": field_on_state}
        with assertRaises(errors.BadUsingInstruction, msg, **kwargs):
            with thp.generate(src, adjustments):
                pass
