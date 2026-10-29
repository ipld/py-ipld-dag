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

from cid import CIDv0, CIDv1


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
