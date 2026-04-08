"""Pure-Python Odin Serializer binary deserializer.

Implements just enough of Sirenix.Serialization.BinaryDataReader to walk a
saved object graph and produce nested Python dicts/lists. Field names are
inline, so we don't need any C# type definitions.

Format reference: dumps/sirenix/BinaryDataReader.cs (decompiled).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any


# BinaryEntryType enum (byte values, see Sirenix.Serialization.BinaryEntryType)
INVALID                            = 0
NAMED_START_OF_REF_NODE            = 1
UNNAMED_START_OF_REF_NODE          = 2
NAMED_START_OF_STRUCT_NODE         = 3
UNNAMED_START_OF_STRUCT_NODE       = 4
END_OF_NODE                        = 5
START_OF_ARRAY                     = 6
END_OF_ARRAY                       = 7
PRIMITIVE_ARRAY                    = 8
NAMED_INTERNAL_REF                 = 9
UNNAMED_INTERNAL_REF               = 10
NAMED_EXTERNAL_REF_BY_INDEX        = 11
UNNAMED_EXTERNAL_REF_BY_INDEX      = 12
NAMED_EXTERNAL_REF_BY_GUID         = 13
UNNAMED_EXTERNAL_REF_BY_GUID       = 14
NAMED_SBYTE                        = 15
UNNAMED_SBYTE                      = 16
NAMED_BYTE                         = 17
UNNAMED_BYTE                       = 18
NAMED_SHORT                        = 19
UNNAMED_SHORT                      = 20
NAMED_USHORT                       = 21
UNNAMED_USHORT                     = 22
NAMED_INT                          = 23
UNNAMED_INT                        = 24
NAMED_UINT                         = 25
UNNAMED_UINT                       = 26
NAMED_LONG                         = 27
UNNAMED_LONG                       = 28
NAMED_ULONG                        = 29
UNNAMED_ULONG                      = 30
NAMED_FLOAT                        = 31
UNNAMED_FLOAT                      = 32
NAMED_DOUBLE                       = 33
UNNAMED_DOUBLE                     = 34
NAMED_DECIMAL                      = 35
UNNAMED_DECIMAL                    = 36
NAMED_CHAR                         = 37
UNNAMED_CHAR                       = 38
NAMED_STRING                       = 39
UNNAMED_STRING                     = 40
NAMED_GUID                         = 41
UNNAMED_GUID                       = 42
NAMED_BOOLEAN                      = 43
UNNAMED_BOOLEAN                    = 44
NAMED_NULL                         = 45
UNNAMED_NULL                       = 46
TYPE_NAME                          = 47
TYPE_ID                            = 48
END_OF_STREAM                      = 49
NAMED_EXTERNAL_REF_BY_STRING       = 50
UNNAMED_EXTERNAL_REF_BY_STRING     = 51

# Sets used in branching
_NAMED_NODE_STARTS = {NAMED_START_OF_REF_NODE, NAMED_START_OF_STRUCT_NODE}
_UNNAMED_NODE_STARTS = {UNNAMED_START_OF_REF_NODE, UNNAMED_START_OF_STRUCT_NODE}
_REF_NODE_STARTS = {NAMED_START_OF_REF_NODE, UNNAMED_START_OF_REF_NODE}
_STRUCT_NODE_STARTS = {NAMED_START_OF_STRUCT_NODE, UNNAMED_START_OF_STRUCT_NODE}


class OdinReadError(Exception):
    pass


@dataclass
class Node:
    """A deserialized object graph node."""
    type_name: str | None = None
    type_id: int | None = None  # the registered Odin type id
    node_id: int | None = None  # the reference node id (for cycle resolution)
    fields: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, k):
        return self.fields[k]

    def get(self, k, default=None):
        return self.fields.get(k, default)

    def __contains__(self, k):
        return k in self.fields

    def __repr__(self):
        return f"Node({self.type_name!r}, fields={list(self.fields)})"


class BinaryReader:
    def __init__(self, data: bytes):
        self.buf = data
        self.pos = 0
        # Type ID registry, populated as we encounter TypeName entries.
        self.types: dict[int, str] = {}
        # Reference node registry by node_id (for resolving InternalReference).
        self.refs: dict[int, Node] = {}

    # ---- low level reads ----------------------------------------------------

    def _need(self, n):
        if self.pos + n > len(self.buf):
            raise OdinReadError(f"unexpected EOF at {self.pos} need {n}")

    def u8(self) -> int:
        self._need(1)
        v = self.buf[self.pos]
        self.pos += 1
        return v

    def i8(self) -> int:
        v = self.u8()
        return v - 256 if v >= 128 else v

    def u16(self) -> int:
        self._need(2)
        v = struct.unpack_from("<H", self.buf, self.pos)[0]
        self.pos += 2
        return v

    def i16(self) -> int:
        self._need(2)
        v = struct.unpack_from("<h", self.buf, self.pos)[0]
        self.pos += 2
        return v

    def u32(self) -> int:
        self._need(4)
        v = struct.unpack_from("<I", self.buf, self.pos)[0]
        self.pos += 4
        return v

    def i32(self) -> int:
        self._need(4)
        v = struct.unpack_from("<i", self.buf, self.pos)[0]
        self.pos += 4
        return v

    def u64(self) -> int:
        self._need(8)
        v = struct.unpack_from("<Q", self.buf, self.pos)[0]
        self.pos += 8
        return v

    def i64(self) -> int:
        self._need(8)
        v = struct.unpack_from("<q", self.buf, self.pos)[0]
        self.pos += 8
        return v

    def f32(self) -> float:
        self._need(4)
        v = struct.unpack_from("<f", self.buf, self.pos)[0]
        self.pos += 4
        return v

    def f64(self) -> float:
        self._need(8)
        v = struct.unpack_from("<d", self.buf, self.pos)[0]
        self.pos += 8
        return v

    def decimal(self) -> str:
        # 16 bytes; we don't need precise decimal math — return hex.
        self._need(16)
        b = self.buf[self.pos:self.pos+16]
        self.pos += 16
        return b.hex()

    def guid(self) -> str:
        self._need(16)
        b = self.buf[self.pos:self.pos+16]
        self.pos += 16
        return b.hex()

    def string(self) -> str:
        # Sirenix ReadStringValue: byte charSize + int32 length + chars
        char_size = self.u8()
        length = self.i32()
        if length < 0 or length > 1 << 28:
            raise OdinReadError(f"insane string length {length} at {self.pos}")
        if char_size == 0:
            self._need(length)
            # Each "char" is 1 byte copied into low byte of a UTF-16 char.
            # In practice this is Latin-1.
            s = self.buf[self.pos:self.pos+length].decode("latin-1")
            self.pos += length
        else:
            self._need(length * 2)
            s = self.buf[self.pos:self.pos+length*2].decode("utf-16-le")
            self.pos += length * 2
        return s

    # ---- type-entry reading -------------------------------------------------

    def read_type_entry(self) -> tuple[int | None, str | None]:
        """Read a TypeName/TypeID/UnnamedNull entry. Returns (type_id, type_name)."""
        b = self.u8()
        if b == TYPE_ID:
            tid = self.i32()
            return tid, self.types.get(tid)
        if b == TYPE_NAME:
            tid = self.i32()
            name = self.string()
            self.types[tid] = name
            return tid, name
        if b == UNNAMED_NULL:
            return None, None
        raise OdinReadError(
            f"expected TypeName/TypeID/UnnamedNull, got entry byte {b} at {self.pos-1}"
        )

    # ---- main walker --------------------------------------------------------

    def read(self) -> Any:
        """Parse the entire stream and return the root node (or list of roots)."""
        roots = []
        while self.pos < len(self.buf):
            entry, name, value = self._read_one()
            if entry == END_OF_STREAM:
                break
            roots.append((name, value))
        if len(roots) == 1:
            return roots[0][1]
        return roots

    def _read_one(self) -> tuple[int, str | None, Any]:
        """Read one entry. Returns (entry_byte, name_or_None, value)."""
        if self.pos >= len(self.buf):
            return END_OF_STREAM, None, None
        b = self.u8()

        if b == END_OF_STREAM:
            return b, None, None

        if b in (NAMED_START_OF_REF_NODE, NAMED_START_OF_STRUCT_NODE):
            name = self.string()
            return b, name, self._read_node_after_start(b)
        if b in (UNNAMED_START_OF_REF_NODE, UNNAMED_START_OF_STRUCT_NODE):
            return b, None, self._read_node_after_start(b)

        if b == END_OF_NODE:
            return b, None, None
        if b == END_OF_ARRAY:
            return b, None, None

        if b == START_OF_ARRAY:
            length = self.i64()
            arr = []
            for _ in range(length):
                while True:
                    e2, n2, v2 = self._read_one()
                    if e2 == END_OF_ARRAY or e2 == END_OF_STREAM:
                        # malformed but be permissive
                        break
                    arr.append(v2)
                    break
            # Consume EndOfArray
            if self.pos < len(self.buf) and self.buf[self.pos] == END_OF_ARRAY:
                self.pos += 1
            return b, None, arr

        if b == PRIMITIVE_ARRAY:
            elem_count = self.i32()
            elem_size = self.i32()
            total = elem_count * elem_size
            self._need(total)
            data = self.buf[self.pos:self.pos+total]
            self.pos += total
            # Heuristic decode by element size
            if elem_size == 1:
                arr = list(data)
            elif elem_size == 4:
                arr = list(struct.unpack_from(f"<{elem_count}i", data))
            elif elem_size == 8:
                arr = list(struct.unpack_from(f"<{elem_count}q", data))
            elif elem_size == 2:
                arr = list(struct.unpack_from(f"<{elem_count}h", data))
            else:
                arr = data.hex()
            return b, None, arr

        # ----- typed primitives -----
        if b == NAMED_SBYTE:   return b, self.string(), self.i8()
        if b == UNNAMED_SBYTE: return b, None, self.i8()
        if b == NAMED_BYTE:    return b, self.string(), self.u8()
        if b == UNNAMED_BYTE:  return b, None, self.u8()
        if b == NAMED_SHORT:   return b, self.string(), self.i16()
        if b == UNNAMED_SHORT: return b, None, self.i16()
        if b == NAMED_USHORT:  return b, self.string(), self.u16()
        if b == UNNAMED_USHORT:return b, None, self.u16()
        if b == NAMED_INT:     return b, self.string(), self.i32()
        if b == UNNAMED_INT:   return b, None, self.i32()
        if b == NAMED_UINT:    return b, self.string(), self.u32()
        if b == UNNAMED_UINT:  return b, None, self.u32()
        if b == NAMED_LONG:    return b, self.string(), self.i64()
        if b == UNNAMED_LONG:  return b, None, self.i64()
        if b == NAMED_ULONG:   return b, self.string(), self.u64()
        if b == UNNAMED_ULONG: return b, None, self.u64()
        if b == NAMED_FLOAT:   return b, self.string(), self.f32()
        if b == UNNAMED_FLOAT: return b, None, self.f32()
        if b == NAMED_DOUBLE:  return b, self.string(), self.f64()
        if b == UNNAMED_DOUBLE:return b, None, self.f64()
        if b == NAMED_DECIMAL: return b, self.string(), self.decimal()
        if b == UNNAMED_DECIMAL:return b, None, self.decimal()
        if b == NAMED_CHAR:    return b, self.string(), chr(self.u16())
        if b == UNNAMED_CHAR:  return b, None, chr(self.u16())
        if b == NAMED_STRING:  return b, self.string(), self.string()
        if b == UNNAMED_STRING:return b, None, self.string()
        if b == NAMED_GUID:    return b, self.string(), self.guid()
        if b == UNNAMED_GUID:  return b, None, self.guid()
        if b == NAMED_BOOLEAN: return b, self.string(), bool(self.u8())
        if b == UNNAMED_BOOLEAN:return b, None, bool(self.u8())
        if b == NAMED_NULL:    return b, self.string(), None
        if b == UNNAMED_NULL:  return b, None, None

        # References — we record the int but don't try to resolve here
        if b == NAMED_INTERNAL_REF:    return b, self.string(), {"$ref": self.i32()}
        if b == UNNAMED_INTERNAL_REF:  return b, None, {"$ref": self.i32()}
        if b == NAMED_EXTERNAL_REF_BY_INDEX:    return b, self.string(), {"$extIndex": self.i32()}
        if b == UNNAMED_EXTERNAL_REF_BY_INDEX:  return b, None, {"$extIndex": self.i32()}
        if b == NAMED_EXTERNAL_REF_BY_GUID:     return b, self.string(), {"$extGuid": self.guid()}
        if b == UNNAMED_EXTERNAL_REF_BY_GUID:   return b, None, {"$extGuid": self.guid()}
        if b == NAMED_EXTERNAL_REF_BY_STRING:   return b, self.string(), {"$extStr": self.string()}
        if b == UNNAMED_EXTERNAL_REF_BY_STRING: return b, None, {"$extStr": self.string()}

        raise OdinReadError(f"unknown entry byte {b} at {self.pos-1}")

    def _read_node_after_start(self, start_byte: int) -> Node:
        """We've already consumed the StartOf* byte (and the name if Named*).
        Read the type entry, optional reference id, then walk children until EndOfNode.
        """
        is_ref = start_byte in _REF_NODE_STARTS
        type_id, type_name = self.read_type_entry()
        node_id = None
        if is_ref:
            node_id = self.i32()

        node = Node(type_name=type_name, type_id=type_id, node_id=node_id)
        if node_id is not None:
            self.refs[node_id] = node

        # Children: read entries until we hit EndOfNode (or EndOfStream as a guard).
        while self.pos < len(self.buf):
            peek = self.buf[self.pos]
            if peek == END_OF_NODE:
                self.pos += 1
                break
            if peek == END_OF_STREAM:
                self.pos += 1
                break
            entry, name, value = self._read_one()
            if entry == END_OF_NODE or entry == END_OF_STREAM:
                break
            if name is None:
                # Unnamed value at field position; index it numerically.
                name = f"_unnamed_{len(node.fields)}"
            node.fields[name] = value
        return node


def parse(data: bytes) -> Any:
    return BinaryReader(data).read()


# ---- convenience: make Node trees JSON-serializable ------------------------

def to_jsonable(obj: Any, _seen: set | None = None) -> Any:
    if _seen is None:
        _seen = set()
    if isinstance(obj, Node):
        if id(obj) in _seen:
            return {"$cycle": obj.node_id}
        _seen.add(id(obj))
        out = {
            "$type": obj.type_name,
            "$id": obj.node_id,
            **{k: to_jsonable(v, _seen) for k, v in obj.fields.items()},
        }
        return out
    if isinstance(obj, list):
        return [to_jsonable(v, _seen) for v in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v, _seen) for k, v in obj.items()}
    if isinstance(obj, (bytes, bytearray)):
        return obj.hex()
    return obj
