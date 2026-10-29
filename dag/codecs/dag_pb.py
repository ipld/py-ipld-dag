"""DAG-PB codec - Protobuf-based Merkle DAG nodes.

Multicodec code: ``0x70``

DAG-PB uses Protocol Buffers for encoding. It is the codec used by
legacy IPFS (UnixFS). A DAG-PB node (``PBNode``) consists of:

- ``Data``  - optional raw bytes payload
- ``Links`` - a list of ``PBLink`` entries, each containing:
  - ``Hash``  - a CID (as raw bytes)
  - ``Name``  - an optional UTF-8 string name
  - ``Tsize`` - an optional integer (total cumulative size)

**Protobuf schema** (proto2)::

    message PBLink {
        optional bytes  Hash  = 1;
        optional string Name  = 2;
        optional uint64 Tsize = 3;
    }

    message PBNode {
        optional bytes   Data  = 1;
        repeated PBLink  Links = 2;
    }

**Wire format field tags**:
- PBLink.Hash:  field 1, wire type 2 (length-delimited) → tag byte ``0x0a``
- PBLink.Name:  field 2, wire type 2 (length-delimited) → tag byte ``0x12``
- PBLink.Tsize: field 3, wire type 0 (varint)           → tag byte ``0x18``
- PBNode.Data:  field 1, wire type 2 (length-delimited) → tag byte ``0x0a``
- PBNode.Links: field 2, wire type 2 (length-delimited) → tag byte ``0x12``

Links MUST be sorted: first by Name (bytes), then by those without names.
Encoding is done right-to-left to match the reference implementation.

Reference implementations:
- https://github.com/ipld/js-dag-pb
- https://ipld.io/specs/codecs/dag-pb/spec/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cid import from_bytes as cid_from_bytes

from ..codec import BlockCodec, register_codec
from ..ipld_model import CID, IPLDNode, is_cid
from ..multicodec_codes import DAG_PB_CODE, DAG_PB_NAME


@dataclass
class PBLink:
    """A link within a DAG-PB node.

    Attributes
    ----------
    hash:
        The CID that this link points to.
    name:
        Optional name for the link.
    tsize:
        Optional total cumulative size of the target DAG.
    """

    hash: CID | None = None
    name: str | None = None
    tsize: int | None = None


@dataclass
class PBNode:
    """A DAG-PB node.

    Attributes
    ----------
    data:
        Optional raw bytes payload.
    links:
        List of links to other nodes.
    """

    data: bytes | None = None
    links: list[PBLink] = field(default_factory=list)


_WIRE_VARINT = 0
_WIRE_LENGTH_DELIMITED = 2


def _encode_varint(value: int) -> bytes:
    """Encode an unsigned integer as a protobuf varint."""
    if value < 0:
        raise ValueError("Varint must be non-negative")
    parts = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value & 0x7F)
    return bytes(parts)


_MAX_VARINT_BYTES = 10


def _decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    """Decode a varint from *data* at *offset*.

    Returns ``(value, new_offset)``.

    Raises ``ValueError`` if the varint exceeds 10 bytes (the maximum
    needed for a 64-bit value), which guards against malformed input
    causing unbounded iteration.
    """
    result = 0
    shift = 0
    bytes_read = 0
    while True:
        if offset >= len(data):
            raise ValueError("Unexpected end of data while reading varint")
        byte = data[offset]
        result |= (byte & 0x7F) << shift
        offset += 1
        bytes_read += 1
        if not (byte & 0x80):
            break
        shift += 7
        if bytes_read >= _MAX_VARINT_BYTES:
            raise ValueError(f"Varint exceeds {_MAX_VARINT_BYTES} bytes, input is malformed")
    return result, offset


def _encode_tag(field_number: int, wire_type: int) -> bytes:
    """Encode a protobuf field tag."""
    return _encode_varint((field_number << 3) | wire_type)


def _encode_length_delimited(field_number: int, data: bytes) -> bytes:
    """Encode a length-delimited protobuf field."""
    tag = _encode_tag(field_number, _WIRE_LENGTH_DELIMITED)
    length = _encode_varint(len(data))
    return tag + length + data


def _encode_varint_field(field_number: int, value: int) -> bytes:
    """Encode a varint protobuf field."""
    tag = _encode_tag(field_number, _WIRE_VARINT)
    return tag + _encode_varint(value)


def _encode_pb_link(link: PBLink) -> bytes:
    """Encode a single PBLink to protobuf bytes.

    Fields are written in order: Hash (1), Name (2), Tsize (3).
    """
    parts: list[bytes] = []

    if link.hash is not None:
        cid_bytes = link.hash.buffer
        parts.append(_encode_length_delimited(1, cid_bytes))

    if link.name is not None:
        parts.append(_encode_length_delimited(2, link.name.encode("utf-8")))

    if link.tsize is not None:
        parts.append(_encode_varint_field(3, link.tsize))

    return b"".join(parts)


def _decode_pb_link(data: bytes) -> PBLink:
    """Decode a PBLink from protobuf bytes."""
    link = PBLink()
    offset = 0

    while offset < len(data):
        tag_value, offset = _decode_varint(data, offset)
        field_number = tag_value >> 3
        wire_type = tag_value & 0x07

        if wire_type == _WIRE_LENGTH_DELIMITED:
            length, offset = _decode_varint(data, offset)
            field_data = data[offset : offset + length]
            offset += length

            if field_number == 1:
                # Hash → CID bytes
                link.hash = cid_from_bytes(field_data)
            elif field_number == 2:
                # Name
                link.name = field_data.decode("utf-8")
            else:
                pass  # skip unknown fields

        elif wire_type == _WIRE_VARINT:
            value, offset = _decode_varint(data, offset)
            if field_number == 3:
                link.tsize = value
        else:
            raise ValueError(f"Unsupported wire type {wire_type} in PBLink")

    return link


def _link_sort_key(link: PBLink) -> tuple[int, bytes]:
    """Sort key for DAG-PB links: named (by UTF-8 name), then unnamed."""
    if link.name is not None:
        return (0, link.name.encode("utf-8"))
    return (1, b"")


def _encode_pb_node(node: PBNode) -> bytes:
    """Encode a PBNode to protobuf bytes.

    Links (field 2) are encoded first, then Data (field 1).
    Links are sorted by Name (byte-wise); unnamed links come last.
    """
    parts: list[bytes] = []

    for link in sorted(node.links, key=_link_sort_key):
        link_bytes = _encode_pb_link(link)
        parts.append(_encode_length_delimited(2, link_bytes))

    if node.data is not None:
        parts.append(_encode_length_delimited(1, node.data))

    return b"".join(parts)


def _decode_pb_node(data: bytes) -> PBNode:
    """Decode a PBNode from protobuf bytes."""
    node = PBNode()
    offset = 0

    while offset < len(data):
        tag_value, offset = _decode_varint(data, offset)
        field_number = tag_value >> 3
        wire_type = tag_value & 0x07

        if wire_type == _WIRE_LENGTH_DELIMITED:
            length, offset = _decode_varint(data, offset)
            field_data = data[offset : offset + length]
            offset += length

            if field_number == 1:
                node.data = field_data
            elif field_number == 2:
                node.links.append(_decode_pb_link(field_data))
            else:
                pass

        elif wire_type == _WIRE_VARINT:
            _, offset = _decode_varint(data, offset)
        else:
            raise ValueError(f"Unsupported wire type {wire_type} in PBNode")

    return node


def _prepare_node(value: Any) -> PBNode:
    """Convert an IPLD data-model value into a ``PBNode``.

    Accepts either a ``PBNode`` directly or a dict with the shape::

        {
            "Data": b"...",           # optional
            "Links": [                # optional
                {
                    "Hash": <CID>,
                    "Name": "...",    # optional
                    "Tsize": 123,     # optional
                },
                ...
            ]
        }
    """
    if isinstance(value, PBNode):
        return value

    if not isinstance(value, dict):
        raise TypeError(f"DAG-PB encode expects a PBNode or dict, got {type(value).__name__}")

    data = value.get("Data")
    if data is not None and not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"PBNode.Data must be bytes, got {type(data).__name__}")

    raw_links = value.get("Links", [])
    links: list[PBLink] = []

    for raw_link in raw_links:
        if isinstance(raw_link, PBLink):
            links.append(raw_link)
        elif isinstance(raw_link, dict):
            link_hash = raw_link.get("Hash")
            if link_hash is not None and not is_cid(link_hash):
                raise TypeError(f"PBLink.Hash must be a CID, got {type(link_hash).__name__}")
            links.append(
                PBLink(
                    hash=link_hash,
                    name=raw_link.get("Name"),
                    tsize=raw_link.get("Tsize"),
                )
            )
        else:
            raise TypeError(f"Link must be a PBLink or dict, got {type(raw_link).__name__}")

    return PBNode(data=data if data is None else bytes(data), links=links)


def _validate_node(node: PBNode) -> None:
    """Validate a PBNode for encoding."""
    if node.data is not None and not isinstance(node.data, bytes):
        raise TypeError(f"PBNode.Data must be bytes, got {type(node.data).__name__}")

    for link in node.links:
        if link.hash is not None and not is_cid(link.hash):
            raise TypeError(f"PBLink.Hash must be a CID, got {type(link.hash).__name__}")
        if link.name is not None and not isinstance(link.name, str):
            raise TypeError(f"PBLink.Name must be str, got {type(link.name).__name__}")
        if link.tsize is not None and not isinstance(link.tsize, int):
            raise TypeError(f"PBLink.Tsize must be int, got {type(link.tsize).__name__}")


def _node_to_dict(node: PBNode) -> dict[str, Any]:
    """Convert a PBNode back to a dict representation."""
    result: dict[str, Any] = {}

    if node.links:
        links_list = []
        for link in node.links:
            link_dict: dict[str, Any] = {}
            if link.hash is not None:
                link_dict["Hash"] = link.hash
            if link.name is not None:
                link_dict["Name"] = link.name
            if link.tsize is not None:
                link_dict["Tsize"] = link.tsize
            links_list.append(link_dict)
        result["Links"] = links_list
    else:
        result["Links"] = []

    if node.data is not None:
        result["Data"] = node.data
    else:
        result["Data"] = None

    return result


class DagPbCodec(BlockCodec):
    """DAG-PB codec (``0x70``).

    Encodes/decodes ``PBNode`` structures to/from Protocol Buffers
    wire format.
    """

    @property
    def name(self) -> str:
        return DAG_PB_NAME

    @property
    def code(self) -> int:
        return DAG_PB_CODE

    def encode(self, node: IPLDNode) -> bytes:
        """Encode a PBNode (or equivalent dict) to DAG-PB bytes."""
        pb_node = _prepare_node(node)
        _validate_node(pb_node)
        return _encode_pb_node(pb_node)

    def decode(self, data: bytes) -> IPLDNode:
        """Decode DAG-PB bytes into a dict with ``Data`` and ``Links`` keys."""
        pb_node = _decode_pb_node(data)
        return _node_to_dict(pb_node)


codec = DagPbCodec()
"""Module-level singleton codec instance."""

name = codec.name
code = codec.code
encode = codec.encode
decode = codec.decode

register_codec(codec)

__all__ = ["DagPbCodec", "PBLink", "PBNode", "codec", "decode", "encode"]
