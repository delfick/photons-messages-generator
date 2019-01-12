LIFX Photons Messages Generator
===============================

This is the code that takes in the LIFX protocol definition and some adjustments
and outputs the code for the ``photons_messages`` module.

Photons is a framework for interacting with LIFX products and can be found at
https://github.com/delfick/photons-core

Changelog
---------

0.5.1 - 12 Jan 2019
    * Make it possible to say an enum value allows unknown values

0.5 - 3 Jan 2019
    Initial release

Tests
-----

Create a virtualenv somewhere and run the following in that virtualenv from this
directory::

    $ pip install -e .
    $ pip install -e ".[tests]"
    $ ./test.sh

Generating messages
-------------------

Once you have this installed in your virtualenv you can run the
``generate_photons_messages`` script in your PATH.

This takes in the following options:

--src or the SRC environment variable
    The path to the yaml file containing the definition of all the messages

--adjustments or the ADJUSTMENTS environment variable
    The path to the adjustments.yml that contains all the customization

--output-folder or the OUTPUT_FOLDER environment variable
    The directory that is the root of the output

Auto customization
------------------

The generator will make the following changes for you without you having to
specify them in the adjustments.yml

Packet names
    Packet names in the source yaml are of the form <Namespace><PacketName>.
    The code will strip the <Namespace>. So for example DeviceSetLabel is turned
    into SetLabel under the DeviceMessages class.

    If the name is ``<Namespace>Get`` then it's turned into ``Get<Namespace>``.
    Similar transformation is done for ``<Namespace>Set``. A ``<Namespace>State``
    message is kept as is.

Field names
    All field names are snake_case after transformation. For example if the field
    was called AmazingField, it would appear as amazing_field.

Adjustments
-----------

The main point of this code is that ``photons_messages`` has some high level
concepts and changes to the source definition. The adjustments.yml looks like
this:

.. code-block:: yaml

    ---

    # If fields end up with these names then the generator complains
    invalid_field_names: ["payload", "count", "index", "fields", "Meta"]

    # Where to start counting reserved fields from
    # So because we say 5 here, the first reserved field will be called reserved6
    # the next will be reserved7, etc
    num_reserved_fields_in_frame: 5

    # The packets are split up by namespace, this list will say the order of the
    # namespaces in the list. All other namespaces not in the list will be added
    # at the end in whatever order they've been defined
    namespace_order: ["core", "discovery", "device", "light"]
    
    # We can use this to rename an entire namespace
    # So here we're saying the namespace `some_namespace` should actually be
    # called `other_namespace`. This new name is used in output options and the
    # namespace_order option above
    rename_namespaces:
      some_namespace: other_namespace
    
    # We can choose to ignore structs from being output
    # Here we're saying don't output either StructOne or StructTwo in fields.py
    # and replace StructOne with a `T.Bytes(size_bytes * 8)` where the size_bytes
    # comes from the field that is using this struct
    # And fields using StructTwo with the fields that are in StructTwo. Note that
    # StructOne doesn't need to actually be in the source yaml, but StructTwo does.
    ignore:
      StructOne: {}
      StructTwo:
        expanded: true
    
    # Output options define where we put our output
    # This is a list of options. You must specify printing enums, fields and all
    # the packets
    #
    # Each item in the list has the following options:
    #
    # create
    #   either "enums", "fields" or "packets"
    #
    # dest
    #   either a string that is the name of the file under output_directory
    #   or a list of strings specifying the path. So saying ``["messages", "lan.py"]``
    #     would produce a file at ``<output_folder>/messages/lan.py``
    #
    # static
    #   A string that is put at the top of that file
    #
    # options
    #   If create is packet then this is a dictionary of ``include`` and ``exclude``
    #   These are either a string or a list of strings of globs to be applied to
    #   the namespaces. Include is applied first and then exclude is applied.
    #   To include all namespaces, say ``include: "*"``
    output:
      - create: enums
        dest: "enums.py"
        static: |
          from enum import Enum
    
      - create: fields
        dest: "fields.py"
        static: |
          from photons_messages import enums
    
          from photons_protocol.packets import dictobj
          from photons_protocol.messages import T
    
          from lru import LRU
    
      - create: packets
        dest: "messages.py"
        options:
          include: "*"
        static: |
          from photons_messages import enums, fields
          from photons_messages.frame import msg
    
          from photons_protocol.messages import T, Messages, MultiOptions
          from photons_protocol.types import Optional
    
          def empty(pkt, attr):
              return pkt.actual(attr) in (Optional, sb.NotSpecified)
    
    # Types let's us specify special types that can then be used multiple times
    # by packets and structs. This let's us specify transformations in one place
    # rather than many.
    # They are of the form ``{<name>: <options>}`` and can be used by specifying
    # ``special_type: <name>`` in the options for a field (see "changes" below)
    # Note that we specify the type here so that you can only override a field
    # with the same type as this special type
    # So here we're defining a type called duration_type, it will appear in
    # fields.py like this:
    #   
    #  duration_type = T.Uint32.default(0).transform(
    #        lambda _, value: int(1000 * float(value))
    #      , lambda value: float(value) / 1000
    #      ).allow_float()
    #
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
    
    # Clones let us create a clone of a struct that has different options for use
    # elsewhere. For example the clone here is the LightHsbk struct but where all
    # the fields are optional
    # The options for each field include ``more_extras`` and ``remove_default``
    # where more_extras adds more options to the type and remove_default makes it
    # so the type has no default even if one was set on the original struct.
    # Note that in this case LightHsbk has extras and defaults specified under
    # the "changes" section.
    clones:
      hsbk_with_optional:
        cloning: LightHsbk
        fields:
          Hue:
            more_extras: ["optional()"]
          Saturation:
            more_extras: ["optional()"]
          Brightness:
            more_extras: ["optional()"]
          Kelvin:
            remove_default: true
            more_extras: ["optional()"]

      scaled_hue:
        ...

      scaled_to_65535:
        ...
    
    # The changes section lets us specify renames, different types, field renames
    # , namespace changes, many_options and using helper
    # Note that all names here are the original names in the source yaml
    # We are guaranteed that enums/structs/packets are all unique names and so
    # you don't need to specify what name is what type.
    changes:
      # First we're renaming LightHsbk as hsbk
      # Then we're saying that if it's used like ``[8]<LightHsbk>`` then we will
      # use the classname of Color and give it a cache amount of 8000
      # We also give special types to some fields. This produces:
      #
      #
      # hsbk = (
      #       ("hue", scaled_hue)
      #     , ("saturation", scaled_to_65535)
      #     , ("brightness", scaled_to_65535)
      #     , ("kelvin", T.Uint16.default(3500))
      #     )
      # 
      # class Color(dictobj.PacketSpec):
      #     fields = hsbk
      # Color.Meta.cache = LRU(8000)
      #
      # Then if anything uses many of these then they will say
      # ``T.Bytes(size_bytes * 8).many(lambda pkt: fields.Color)``
      #
      LightHsbk:
        rename: hsbk
        many_options:
          name: Color
          cache_amount: 8000
        fields:
          Hue:
            special_type: scaled_hue
          Saturation:
            special_type: scaled_to_65535
          Brightness:
            special_type: scaled_to_65535
          Kelvin:
            default: "3500"

      # Here we rename the enum DeviceService to Services
      DeviceService:
        rename: Services
    
      # Here we put the DeviceAcknowledgement packet in the "core" namespace
      DeviceAcknowledgement:
        namespace: core
    
      # Here we're saying the Label field on the DeviceSetLabel packet is a string
      # This only works for fields that are bytes and will output
      # ``T.String(size_bytes * 8)`` instead of ``T.Bytes(size_bytes * 8)``
      DeviceSetLabel:
        fields:
          Label:
            string_type: true
    
      # Here we're saying DeviceStateLabel has the same fields as DeviceSetLabel
      # And will output ``StateLabel = SetLabel.using(pkt_type)`` where
      # pkt_type is the pkt_type for DeviceStateLabel from the source yaml.
      # This will complain if the fields are infact not the same.
      DeviceStateLabel:
        using: DeviceSetLabel
    
      # Here we're saying that GetService is under the discovery namespace and
      # has a multi option of -1
      # So it will output:
      # 
      #  GetService = msg(2
      #      , multi = -1
      #      )
      #
      DeviceGetService:
        namespace: discovery
        multi: "-1"
    
      # Here we're renaming the Payload field on EchoRequest to be echoing
      # This is because payload is one of our fields we're not allowed to have.
      DeviceEchoRequest:
        fields:
          Payload:
            rename: echoing

      # Here we're giving the Version field a version_number() option
      # So it'll output
      #
      #   StateHostFirmware = msg(15
      #       , ("build", T.Uint64)
      #       , ("install", T.Uint64)
      #       , ("version", T.Uint32.version_number())
      #       )
      #
      DeviceStateHostFirmware:
        fields:
          Version:
            extras: ["version_number()"]
    
      # Here we give Duration the special type of duration_type
      # So it produces
      #
      #  SetColor = msg(102
      #      , ("reserved6", T.Reserved(8))
      #      , *fields.hsbk
      #      , ("duration", fields.duration_type)
      #      )
      #
      # Note that the *fields.hsbk means we are using the fields from hsbk here
      # inline.
      LightSetColor:
        rename: SetColor
        fields:
          Duration:
            special_type: duration_type
    
      # Here we use override_struct to use our hsbk_with_optional clone instead
      # of hsbk which is what would otherwise be used
      LightSetWaveformOptional:
        fields:
          Color:
            override_struct: hsbk_with_optional
    
      # Apply is an enum here (as defined in the source yaml) and so the code
      # will make sure the default we specify is a valid value from that enum.
      MultiZoneSetColorZones:
        fields:
          Apply:
            default: "APPLY"
    
      # We can split up a field into a value for each of the bits in that field
      # So let's say we have a packet called ExamplePacket with a field Flags
      # that is a uint8, then the following will produce:
      #
      #   ExamplePacket = msg(9001
      #     , ("option_one", T.Bool)
      #     , ("option_two", T.Bool)
      #     , ("option_three", T.Bool)
      #     , ("option_four", T.Bool)
      #     , ("option_five", T.Bool)
      #     , ("option_six", T.Bool)
      #     , ("option_seven", T.Bool)
      #     , ("option_eight", T.Bool)
      #     )
      #
      # Note that the number of options must match the number of bits for that
      # field.
      ExamplePacket:
        fields:
          Flags:
            bits:
              - OptionOne
              - OptionTwo
              - OptionThree
              - OptionFour
              - OptionFive
              - OptionSix
              - OptionSeven
              - OptionEight
