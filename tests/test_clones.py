# coding: spec

from photons_messages_generator.test_helpers import TestCase

describe TestCase, "clones":
    it "uses the clone instead of original struct":
        src = """
            fields:
              SomeParams:
                size_bytes: 5
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
                  - name: "Four"
                    type: "uint8"
                    size_bytes: 1
                  - name: "Five"
                    type: "uint8"
                    size_bytes: 1

            packets:
              one:
                OnePacketExample:
                  pkt_type: 1
                  size_bytes: 5
                  fields:
                    - name: "One"
                      type: "<SomeParams>"
                      size_bytes: 5

                OneOtherExample:
                  pkt_type: 2
                  size_bytes: 5
                  fields:
                    - name: "One"
                      type: "<SomeParams>"
                      size_bytes: 5

                OneAnotherExample:
                  pkt_type: 3
                  size_bytes: 15
                  fields:
                    - name: "Params"
                      type: "[3]<SomeParams>"
                      size_bytes: 15
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        clones:
          some_params_with_optionals:
            cloning: SomeParams
            many_options:
              name: ParamsOptionals
            fields:
              One:
                more_extras: ["optional()"]
              Two:
                remove_default: true
                more_extras: ["optional()"]
              Four:
                remove_default: true

        changes:
          SomeParams:
            fields:
              One:
                default: "0"
                extras: "transform()"
              Two:
                default: "20"
                extras: "transform()"
              Three:
                default: "30"
              Four:
                default: "30"
                extras: "dynamic()"
              Five:
                extras: "other()"

          OneOtherExample:
            fields:
              One:
                override_struct: some_params_with_optionals

          OneAnotherExample:
            fields:
              Params:
                override_struct: some_params_with_optionals
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params_with_optionals = [
                  ("one", T.Uint8.default(0).transform().optional())
                , ("two", T.Uint8.transform().optional())
                , ("three", T.Uint8.default(30))
                , ("four", T.Uint8.dynamic())
                , ("five", T.Uint8.other())
                ]

            class ParamsOptionals(dictobj.PacketSpec):
                fields = some_params_with_optionals

            some_params = [
                  ("one", T.Uint8.default(0).transform())
                , ("two", T.Uint8.default(20).transform())
                , ("three", T.Uint8.default(30))
                , ("four", T.Uint8.default(30).dynamic())
                , ("five", T.Uint8.other())
                ]
            """

            expected_messages = """
            ########################
            ###   ONE
            ########################
            
            class OneMessages(Messages):
                PacketExample = msg(1
                    , *fields.some_params
                    )
            
                OtherExample = msg(2
                    , *fields.some_params_with_optionals
                    )

                AnotherExample = msg(3
                    , ("params", T.Bytes(40 * 3).many(lambda pkt: fields.ParamsOptionals))
                    )
            
            __all__ = ["OneMessages"]
            """

            output.assertFileContents("fields.py", expected_fields)
            output.assertFileContents("messages.py", expected_messages)

    it "can use the clone in other fields":
        src = """
            fields:
              SomeParams:
                size_bytes: 5
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
                  - name: "Four"
                    type: "uint8"
                    size_bytes: 1
                  - name: "Five"
                    type: "uint8"
                    size_bytes: 1

              AnotherParams:
                size_bytes: 5
                fields:
                  - name: "Params"
                    type: "<SomeParams>"
                    size_bytes: 5

              MoreParams:
                size_bytes: 15
                fields:
                  - name: "Params"
                    type: "[3]<SomeParams>"
                    size_bytes: 15
        """

        adjustments = """
        num_reserved_fields_in_frame: 3

        clones:
          some_params_with_optionals:
            cloning: SomeParams
            many_options:
              name: ParamsOptionals
            fields:
              One:
                more_extras: ["optional()"]
              Two:
                remove_default: true
                more_extras: ["optional()"]
              Four:
                remove_default: true

        changes:
          SomeParams:
            fields:
              One:
                default: "0"
                extras: "transform()"
              Two:
                default: "20"
                extras: "transform()"
              Three:
                default: "30"
              Four:
                default: "30"
                extras: "dynamic()"
              Five:
                extras: "other()"

          AnotherParams:
            fields:
              Params:
                override_struct: some_params_with_optionals

          MoreParams:
            fields:
              Params:
                override_struct: some_params_with_optionals
        """

        with self.generate(src, adjustments) as output:
            expected_fields = """
            some_params_with_optionals = [
                  ("one", T.Uint8.default(0).transform().optional())
                , ("two", T.Uint8.transform().optional())
                , ("three", T.Uint8.default(30))
                , ("four", T.Uint8.dynamic())
                , ("five", T.Uint8.other())
                ]

            class ParamsOptionals(dictobj.PacketSpec):
                fields = some_params_with_optionals

            some_params = [
                  ("one", T.Uint8.default(0).transform())
                , ("two", T.Uint8.default(20).transform())
                , ("three", T.Uint8.default(30))
                , ("four", T.Uint8.default(30).dynamic())
                , ("five", T.Uint8.other())
                ]
            
            another_params = [
                  *some_params_with_optionals
                ]
            
            more_params = [
                  ("params", T.Bytes(40 * 3).many(lambda pkt: ParamsOptionals))
                ]
            """

            output.assertFileContents("fields.py", expected_fields)
