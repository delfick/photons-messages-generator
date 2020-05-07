# coding: spec

from photons_messages_generator import test_helpers as thp
from photons_messages_generator import errors

from delfick_project.errors_pytest import assertRaises

describe "Multiple":
    it "does not allow broken bytes":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 2
                  fields:
                    - name: "Failure"
                      type: "[10]byte"
                      size_bits: 10
                    - type: "reserved"
                      size_bits: 6
        """

        adjustments = """
        num_reserved_fields_in_frame: 3
        """

        msg = "Only basic types and reserved may be a partial byte"
        with assertRaises(errors.BadSizeBytes, msg, name="byte"):
            with thp.generate(src, adjustments):
                pass

    it "does not allow broken strings":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 2
                  fields:
                    - name: "Failure"
                      type: "[10]byte"
                      size_bits: 10
                    - type: "reserved"
                      size_bits: 6
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        changes:
          OnePacketExample:
            fields:
              Failure:
                string_type: true
        """

        msg = "Only basic types and reserved may be a partial byte"
        with assertRaises(errors.BadSizeBytes, msg, name="string"):
            with thp.generate(src, adjustments):
                pass

    it "Treats size_bits 1 bool as a Bool":
        src = """
            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 2
                  fields:
                    - name: "ABool"
                      type: "bool"
                      size_bytes: 1
                    - name: "ARealBool"
                      type: "bool"
                      size_bits: 1
                    - type: "reserved"
                      size_bits: 7
        """

        adjustments = """
        num_reserved_fields_in_frame: 3
        """

        with thp.generate(src, adjustments) as output:
            expected_messages = """
            # fmt: off

            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , ("a_bool", T.BoolInt)
                    , ("a_real_bool", T.Bool)
                    , ("reserved4", T.Reserved(7))
                    )

            # fmt: on
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("messages.py", expected_messages)
