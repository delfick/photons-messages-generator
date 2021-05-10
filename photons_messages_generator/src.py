from photons_messages_generator.helpers import valid_enum_types
from photons_messages_generator import field_types as ft
from photons_messages_generator import errors

from delfick_project.norms import dictobj, sb, BadSpecValue


class EnumValue(dictobj.Spec):
    name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    value = dictobj.Field(sb.integer_spec, wrapper=sb.required)


class Enum(dictobj.Spec):
    name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    full_name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    type = dictobj.Field(sb.string_choice_spec(valid_enum_types), wrapper=sb.required)
    values = dictobj.Field(sb.listof(EnumValue.FieldSpec()))


class struct_field_spec(sb.Spec):
    def normalise_filled(self, meta, val):
        val = sb.dictionary_spec().normalise(meta, val)
        if val.get("type") == "reserved":
            if "name" in val:
                raise BadSpecValue(
                    "Expected reserved field to not have a name", meta=meta.at("name")
                )
        else:
            if "name" not in val:
                raise BadSpecValue("Expected field to have a name", meta=meta.at("name"))
            val["full_name"] = val["name"]

        if "type" in val:
            val["original_type"] = val["type"]

        sf = StructField.FieldSpec().normalise(meta, val)

        size_bits_defined = sf.size_bits is not sb.NotSpecified
        size_bytes_defined = sf.size_bytes is not sb.NotSpecified

        if not (size_bits_defined ^ size_bytes_defined):
            raise BadSpecValue("Expected one of size_bits or size_bytes", meta=meta)

        if size_bytes_defined:
            sf.size_bits = sf.size_bytes * 8

        return sf


class StructField(dictobj.Spec):
    name = dictobj.NullableField(sb.string_spec)
    full_name = dictobj.NullableField(sb.string_spec)
    type = dictobj.Field(sb.string_spec, wrapper=sb.required)
    original_type = dictobj.Field(sb.string_spec, wrapper=sb.required)
    size_bits = dictobj.Field(sb.integer_spec, wrapper=sb.optional_spec)
    size_bytes = dictobj.Field(sb.integer_spec, wrapper=sb.optional_spec)
    default = dictobj.NullableField(sb.string_spec)
    extras = dictobj.Field(sb.listof(sb.string_spec()))

    def format(self, in_fields=False, type_only=False):
        extras = ".".join(self.format_extras())
        if extras:
            extras = f".{extras}"

        if isinstance(self.type, ft.StructType):
            if self.type.multiples == 1 and not self.original_type.startswith("["):
                prefix = "" if in_fields else "fields."
                return f"*{prefix}{self.type.struct.name}"

        type_info = f"{self.type.format(self.size_bits, in_fields=in_fields)}{extras}"
        if type_only:
            return type_info

        if isinstance(self.type, ft.StructType):
            return f'("{self.name}", {type_info})'
        else:
            return f'("{self.name}", {type_info})'

    def format_extras(self):
        if self.default is not None:
            if isinstance(self.type, ft.EnumType):
                yield f"default(enums.{self.type.enum.name}.{self.type.value(self.default)})"
            else:
                yield f"default({self.default})"

        for extra in self.extras:
            yield extra.strip()

    def expand_fields(self, chain=None, prefix=None, expand_structs=False):
        if not getattr(self.type, "expanded", False):
            if isinstance(self.type, ft.StructType):
                if self.type.multiples > 1:
                    return self
            else:
                raise errors.CannotExpand(cant_expand=self.type)

        if prefix is None:
            prefix = []

        if not isinstance(self.type, ft.StructType) or getattr(self.type, "expanded", False):
            prefix.append(self.name)

        yield from self.type.expand_fields(
            chain=chain, prefix=prefix, expand_structs=expand_structs
        )

    def with_prefix(self, prefix):
        clone = self.clone()

        if self.name is None:
            return clone

        clone.name = "".join(prefix + [self.name])
        return clone


class CloneStruct(dictobj.Spec):
    name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    multi_options = dictobj.NullableField(sb.any_spec)

    @property
    def full_name(self):
        return self.name

    @property
    def multi_name(self):
        if self.multi_options is None:
            raise errors.ExpectedMultiName(
                f"Struct {self.name} is used in a .multiple block but has no multi_name specified"
            )
        return self.multi_options.name


class struct_spec(sb.Spec):
    def normalise_filled(self, meta, val):
        val = sb.dictionary_spec().normalise(meta, val)
        if "fields" in val:
            val["item_fields"] = val["fields"]
        return Struct.FieldSpec().normalise(meta, val)


class Struct(dictobj.Spec):
    name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    full_name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    size_bytes = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    item_fields = dictobj.Field(sb.listof(struct_field_spec()))
    multi_options = dictobj.NullableField(sb.any_spec)

    @property
    def multi_name(self):
        if self.multi_options is None:
            raise errors.ExpectedMultiName(
                f"Struct {self.name} is used in a .multiple block but has no multi_name specified"
            )
        return self.multi_options.name

    @property
    def dynamic_function_name(self):
        return f"union_fields_{self.name}"

    def __hash__(self):
        return hash(self.full_name)


class packet_spec(sb.Spec):
    def normalise_filled(self, meta, val):
        val = sb.dictionary_spec().normalise(meta, val)
        if "fields" in val:
            val["item_fields"] = val["fields"]
        return Packet.FieldSpec().normalise(meta, val)


class Packet(dictobj.Spec):
    name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    full_name = dictobj.Field(sb.string_spec, wrapper=sb.required)
    namespace = dictobj.Field(sb.string_spec, wrapper=sb.required)
    pkt_type = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    size_bytes = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    item_fields = dictobj.Field(sb.listof(struct_field_spec()), wrapper=sb.required)


class Type(dictobj.Spec):
    multiples = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    type = dictobj.Field(sb.any_spec, wrapper=sb.required)


class named_spec(sb.Spec):
    def __init__(self, spec):
        self.spec = spec

    def normalise_empty(self, meta):
        return []

    def normalise_filled(self, meta, val):
        val = sb.dictof(sb.string_spec(), sb.dictionary_spec()).normalise(meta, val)

        final = []
        for name, v in val.items():
            v["name"] = name
            v["full_name"] = name
            final.append(self.spec.normalise(meta.at(name), v))

        return final


class packets_spec(sb.Spec):
    def normalise_empty(self, meta):
        return []

    def normalise_filled(self, meta, val):
        val = sb.dictionary_spec().normalise(meta, val)

        final = []
        for namespace, packets in val.items():
            for name, v in packets.items():
                if type(v) is dict:
                    v = dict(v)
                    v["namespace"] = namespace
                    v["full_name"] = name
                    v["name"] = name
                final.append(packet_spec().normalise(meta.at(name), v))

        return final


class unions_spec(sb.Spec):
    def normalise_empty(self, meta):
        return []

    def normalise_filled(self, meta, val):
        val = sb.dictionary_spec().normalise(meta, val)

        final = []
        for name, v in val.items():
            if type(v) is dict:
                if "fields" in v:
                    v["item_fields"] = v["fields"]
                v = dict(v)
                v["full_name"] = name
                v["name"] = name
            final.append(struct_spec().normalise(meta.at(name), v))

        return final


class Src(dictobj.Spec):
    enums = dictobj.Field(named_spec(Enum.FieldSpec()))
    unions = dictobj.Field(unions_spec())
    groups = dictobj.Field(named_spec(struct_spec()))
    packets = dictobj.Field(packets_spec())
