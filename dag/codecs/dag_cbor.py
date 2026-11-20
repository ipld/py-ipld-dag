"""DAG-CBOR codec - deterministic CBOR with IPLD CID links.

Multicodec code: ``0x71``

DAG-CBOR is CBOR (RFC 8949) with additional constraints:

1. **Deterministic encoding**: map keys sorted by byte length then
   lexicographically (RFC 7049 §3.9 canonical ordering), smallest
   possible integer representations, no indefinite-length items,
   floats always 64-bit, no NaN or Infinity.
2. **CID links**: CIDs are encoded using CBOR tag 42 wrapping the
   CID bytes prefixed with a ``0x00`` identity multibase byte.
3. **No additional CBOR tags** are allowed (only tag 42).

Reference implementations:
- https://github.com/ipld/js-dag-cbor
- https://ipld.io/specs/codecs/dag-cbor/spec/
"""

from __future__ import annotations

import io
import math
import struct
from typing import Any, BinaryIO, cast

import cbor2

from ..codec import BlockCodec, CountingWriter, register_codec
from ..ipld_model import IPLDNode, decode_cid_bytes, is_cid, validate_string_map_keys
from ..multicodec_codes import DAG_CBOR_CODE, DAG_CBOR_NAME

_CID_CBOR_TAG = 42

_MULTIBASE_IDENTITY = b"\x00"


class DagCborCodec(BlockCodec):
    """DAG-CBOR codec (``0x71``).

    Encodes IPLD data-model values into deterministic CBOR with
    CID links represented as CBOR tag 42.
    """

    @property
    def name(self) -> str:
        return DAG_CBOR_NAME

    @property
    def code(self) -> int:
        return DAG_CBOR_CODE

    def encode_to_stream(self, node: IPLDNode, stream: BinaryIO) -> int:
        """Encode an IPLD value to DAG-CBOR via ``cbor2.dump``.

        CIDs are encoded as ``Tag(42, 0x00 || cid_bytes)``.
        Map keys are sorted using canonical CBOR ordering.
        """
        prepared = _prepare_for_cbor(node)
        counter = CountingWriter(stream)
        cbor2.dump(
            prepared,
            cast(BinaryIO, counter),
            canonical=True,
            encoders={float: _encode_float64},
        )
        return counter.written

    def decode_from_stream(self, stream: BinaryIO) -> IPLDNode:
        """Decode DAG-CBOR from a binary stream via ``cbor2.load``.

        CBOR tag 42 values are converted back into CID objects.
        """
        raw = cbor2.load(stream, tag_hook=_tag_hook)
        return _restore_from_cbor(raw)

    def encode(self, node: IPLDNode) -> bytes:
        """Encode an IPLD value to DAG-CBOR bytes."""
        buf = io.BytesIO()
        self.encode_to_stream(node, buf)
        return buf.getvalue()

    def decode(self, data: bytes) -> IPLDNode:
        """Decode DAG-CBOR bytes into an IPLD value."""
        return self.decode_from_stream(io.BytesIO(data))


def _prepare_for_cbor(node: Any) -> Any:
    """Recursively convert IPLD values for cbor2 serialization.

    - CIDs → ``CBORTag(42, b'\\x00' + cid_bytes)``
    - Dicts/lists are traversed recursively.
    - Other scalars pass through unchanged.
    """
    if is_cid(node):
        cid_bytes = node.buffer
        return cbor2.CBORTag(_CID_CBOR_TAG, _MULTIBASE_IDENTITY + cid_bytes)

    if isinstance(node, dict):
        validate_string_map_keys(node, context="DAG-CBOR map")
        return {k: _prepare_for_cbor(v) for k, v in node.items()}

    if isinstance(node, list):
        return [_prepare_for_cbor(item) for item in node]

    if isinstance(node, (bytes, bytearray)):
        return bytes(node)

    return node


def _encode_float64(encoder: cbor2.CBOREncoder, value: float) -> None:
    """Encode a float as a 64-bit double; reject NaN and Infinity.

    DAG-CBOR requires floats in 64-bit form even when a shorter form is
    exact, and forbids IEEE 754 special values. cbor2's canonical mode
    would otherwise shrink floats to half or single precision.
    """
    if not math.isfinite(value):
        raise ValueError(f"DAG-CBOR does not support {value!r} floats")
    encoder.write(b"\xfb" + struct.pack(">d", value))


def _tag_hook(tag: cbor2.CBORTag, _ignore_tag_errors: bool = False) -> Any:
    """Handle CBOR tags during decoding.

    Only tag 42 (CID) is supported in DAG-CBOR.

    Signature matches ``cbor2`` 6.x: ``(tag, ignore_tag_errors)``.
    """
    if tag.tag == _CID_CBOR_TAG:
        cid_bytes = tag.value
        if isinstance(cid_bytes, bytes) and cid_bytes[:1] == _MULTIBASE_IDENTITY:
            cid_bytes = cid_bytes[1:]
        return decode_cid_bytes(cid_bytes)
    raise ValueError(f"Unsupported CBOR tag {tag.tag} in DAG-CBOR (only tag 42 is allowed)")


def _restore_from_cbor(node: Any) -> Any:
    """Recursively restore IPLD values after cbor2 decoding.

    - CID objects are left as-is (already decoded by tag_hook).
    - Dicts/lists are traversed recursively.
    """
    if is_cid(node):
        return node

    if isinstance(node, dict):
        return {k: _restore_from_cbor(v) for k, v in node.items()}

    if isinstance(node, list):
        return [_restore_from_cbor(item) for item in node]

    return node


codec = DagCborCodec()
"""Module-level singleton codec instance."""

name = codec.name
code = codec.code
encode = codec.encode
decode = codec.decode

register_codec(codec)
