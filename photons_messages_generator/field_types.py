from photons_messages_generator.helpers import convert_type
from photons_messages_generator import errors


class SimpleType:
    def __init__(self, val, multiples):
        self.val = val
        self.multiples = multiples

    def __repr__(self):
        return f"<Simple: {self.multiples}: {self.val}>"

    def format(self, size_bits, **kwargs):
        multiples = ""
        if self.multiples > 1:
            multiples = f".multiple({self.multiples})"

        if size_bits % self.multiples != 0:
            raise errors.BadSizeBytes(
                "Expected size bytes to be divisible by multiple",
                multiple=self.multiples,
                size_bits=size_bits,
            )

        if self.val == "byte":
            multiples = ""
        else:
            size_bits = int(size_bits / self.multiples)
        return f"{convert_type(self.val, size_bits)}{multiples}"


class StringType:
    def __repr__(self):
        return "<String>"

    def format(self, size_bits, **kwargs):
        return f"{convert_type('string', size_bits)}"


class EnumType:
    def __init__(self, enum, multiples, allow_unknown=False):
        self.enum = enum
        self.allow_unknown = allow_unknown
        self.multiples = multiples

    def value(self, name):
        names = [v.name for v in self.enum.values]
        if name not in names:
            raise errors.NoSuchEnumValue(wanted=name, available=names, enum=self.enum.name)
        return name

    def __repr__(self):
        return f"<Enum: {self.enum.type}: {self.enum.name}>"

    def format(self, size_bits, **kwargs):
        options = ""
        multiple = ""
        if self.allow_unknown:
            options = ", allow_unknown=True"
        if self.multiples > 1:
            multiple = f".multiple({self.multiples})"
        return f"{convert_type(self.enum.type, size_bits)}.enum(enums.{self.enum.name}{options}){multiple}"


class StructOverrideType:
    def __init__(self, struct):
        self.struct = struct

    def __repr__(self):
        return f"<StructOverride: {self.struct}>"

    def format(self, size_bits, **kwargs):
        raise errors.GeneratorError("Struct overrides should be resolved before format")


class SpecialType:
    def __init__(self, options):
        self.options = options

    def __repr__(self):
        return f"<SpecialType: {self.options.name}: {self.options.type}>"

    def format(self, size_bits, in_fields=False, **kwargs):
        if size_bits != self.options.size_bits:
            raise errors.GeneratorError(
                "Special type has different size_bits than expected",
                name=self.options.name,
                want=size_bits,
                specified=self.options.size_bits,
            )

        prefix = "fields." if not in_fields else ""
        return f"{prefix}{self.options.name}"


class StructType:
    def __init__(self, struct, multiples, expanded=False, ignored=False):
        self.struct = struct
        self.multiples = multiples
        self.ignored = ignored
        self.expanded = expanded

    def __repr__(self):
        return f"<Struct: {self.multiples}: {self.struct.name}>"

    def format(self, size_bits, in_fields=False, **kwargs):
        if size_bits % self.multiples != 0:
            raise errors.BadSizeBytes(
                "Expected size bytes to be divisible by multiple",
                multiple=self.multiples,
                size_bits=size_bits,
            )
        size_bits = int(size_bits / self.multiples)

        if self.ignored:
            return f"T.Bytes({size_bits} * {self.multiples})"

        typ = f"T.Bytes({size_bits})"
        prefix = "" if in_fields else "fields."
        if self.struct.multi_name.startswith("lambda"):
            prefix = ""
        return f"{typ}.multiple({self.multiples}, kls={prefix}{self.struct.multi_name})"

    def expand_fields(self, chain=None, prefix=None, expand_structs=False):
        if chain is None:
            chain = []

        if prefix is None:
            prefix = []

        if self.struct.full_name in chain:
            raise errors.CyclicPacketField(chain=chain)

        chain.append(self.struct.full_name)

        for field in self.struct.item_fields:
            if getattr(field.type, "expanded", False):
                yield from field.expand_fields(
                    chain=chain, prefix=prefix, expand_structs=expand_structs
                )
            else:
                yield field.with_prefix(prefix)


class PacketType:
    def __init__(self, packet, multiples):
        self.packet = packet
        self.expanded = True
        if multiples != 1:
            raise errors.NonsensicalMultiplier(
                "If you want multiples of a struct, make it not a packet type", wanted=multiples
            )

    def __repr__(self):
        return f"<Packet: {self.packet.name}>"

    def format(self, size_bits, **kwargs):
        raise errors.GeneratorError(
            "Packet types are meant to be already resolved before formats are called",
            packet=self.packet,
        )

    def expand_fields(self, chain=None, prefix=None, expand_structs=False):
        if chain is None:
            chain = []

        if prefix is None:
            prefix = []

        if self.packet.full_name in chain:
            raise errors.CyclicPacketField(chain=chain)

        chain.append(self.packet.full_name)

        for field in self.packet.item_fields:
            should_expand = getattr(field.type, "expanded", False)
            should_expand = should_expand or (expand_structs and isinstance(field.type, StructType))
            if should_expand:
                yield from field.expand_fields(chain=chain, prefix=prefix, expand_structs=True)
            else:
                yield field.with_prefix(prefix)


class UnionType:
    def __init__(self, union, multiples, *, switch_field):
        self.union = union
        self.switch_field = switch_field
        self.expanded = True
        if multiples != 1:
            raise errors.NonsensicalMultiplier(
                "If you want multiples of a struct, make it not a union type", wanted=multiples
            )

    def __repr__(self):
        return f"<Union: {self.union.name}>"

    def format(self, size_bits, **kwargs):
        return f"T.Bytes({size_bits//8} * 8).dynamic(lambda pkt: fields.{self.union.dynamic_function_name}(pkt.{self.switch_field}))"


class OverrideType:
    def __init__(self, override):
        self.override = override

    def __repr__(self):
        return f"<Override {self.override}>"

    def format(self, size_bits, **kwargs):
        return self.override
