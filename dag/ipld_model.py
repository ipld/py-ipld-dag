"""IPLD Data Model - the universal representation layer.

The IPLD Data Model defines the following *kinds* of values that can
appear in any IPLD node:

    Null, Bool, Int, Float, String, Bytes, List, Map, Link

A *Link* is a CID (Content IDentifier) that points to another block.

This module provides:
- ``Kind`` enum for type discrimination
- Helper predicates for checking values
- Type alias ``IPLDNode`` for type-annotated IPLD data

Reference: https://ipld.io/docs/data-model/
"""

from __future__ import annotations

import enum
from typing import Any, Union

from cid import CIDv0, CIDv1, make_cid
from cid import from_bytes as cid_from_bytes


class Kind(enum.Enum):
    """IPLD Data Model kinds.

    Every value in the IPLD Data Model belongs to exactly one kind.
    """

    NULL = "null"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BYTES = "bytes"
    LIST = "list"
    MAP = "map"
    LINK = "link"


CID = Union[CIDv0, CIDv1]
"""A Content IDentifier - either CIDv0 or CIDv1."""

IPLDNode = Union[
    None,
    bool,
    int,
    float,
    str,
    bytes,
    list["IPLDNode"],
    dict[str, "IPLDNode"],
    CID,
]
"""Any value conforming to the IPLD Data Model.

- ``None``  → Null
- ``bool``  → Bool
- ``int``   → Int
- ``float`` → Float
- ``str``   → String
- ``bytes`` → Bytes
- ``list``  → List
- ``dict``  → Map  (keys must be strings)
- ``CID``   → Link
"""


def kind_of(value: Any) -> Kind:
    """Return the IPLD ``Kind`` of *value*.

    Raises ``TypeError`` if the value is not representable in the IPLD
    Data Model.
    """
    if value is None:
        return Kind.NULL
    if isinstance(value, bool):
        return Kind.BOOL
    if isinstance(value, int):
        return Kind.INT
    if isinstance(value, float):
        return Kind.FLOAT
    if isinstance(value, str):
        return Kind.STRING
    if isinstance(value, (bytes, bytearray)):
        return Kind.BYTES
    if isinstance(value, (CIDv0, CIDv1)):
        return Kind.LINK
    if isinstance(value, list):
        return Kind.LIST
    if isinstance(value, dict):
        return Kind.MAP
    raise TypeError(f"Value {value!r} ({type(value).__name__}) is not an IPLD kind")


def is_cid(value: Any) -> bool:
    """Return ``True`` if *value* is a CID (IPLD Link)."""
    return isinstance(value, (CIDv0, CIDv1))


def decode_cid_bytes(raw_bytes: bytes) -> CID:
    """Decode raw CID bytes into a ``CIDv0`` or ``CIDv1`` object.

    CIDv1 bytes start with a version byte (``0x01``).
    CIDv0 bytes are just a raw multihash (starting with the hash
    function code, e.g. ``0x12`` for sha2-256).

    The py-cid ``from_bytes`` works for CIDv1 (which has a leading
    version byte 0 or 1). For CIDv0 raw multihash bytes we need
    to construct the CID directly.

    .. note:: Version assumption

       Currently only CIDv0 and CIDv1 exist.  Any first byte that
       is not ``0x01`` (CIDv1) is treated as a raw multihash and
       wrapped as CIDv0 (``dag-pb``).  If a CIDv2 is ever
       introduced this logic will need to be revisited.  The
       identity hash function code (``0x00``) is *not* a valid
       CIDv0 multihash prefix in practice (CIDv0 always uses
       sha2-256, code ``0x12``), so the current heuristic is safe
       for all real-world data.
    """
    if len(raw_bytes) < 2:
        raise ValueError("CID bytes too short")

    # CIDv1: first byte is the version marker 0x01
    if raw_bytes[0] == 0x01:
        return cid_from_bytes(raw_bytes)

    # CIDv0: raw multihash bytes (no version prefix).  CIDv0 is
    # always dag-pb with sha2-256, so the first byte should be 0x12.
    return make_cid(0, "dag-pb", raw_bytes)


def validate_string_map_keys(mapping: dict[Any, Any], *, context: str = "IPLD map") -> None:
    """Raise ``TypeError`` if *mapping* has any non-string key.

    DAG-CBOR and DAG-JSON require string map keys.
    """
    for key in mapping:
        if not isinstance(key, str):
            raise TypeError(f"{context} keys must be strings, got {type(key).__name__}: {key!r}")


def is_ipld_value(value: Any) -> bool:
    """Return ``True`` if *value* is representable in the IPLD Data Model."""
    try:
        kind_of(value)
        return True
    except TypeError:
        return False
