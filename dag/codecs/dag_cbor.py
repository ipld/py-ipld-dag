"""DAG-CBOR codec - deterministic CBOR with IPLD CID links.

Multicodec code: ``0x71``

DAG-CBOR is CBOR (RFC 8949) with additional constraints:

1. **Deterministic encoding**: map keys sorted by byte length then
   lexicographically (RFC 7049 §3.9 canonical ordering), smallest
   possible integer representations, no indefinite-length items.
2. **CID links**: CIDs are encoded using CBOR tag 42 wrapping the
   CID bytes prefixed with a ``0x00`` identity multibase byte.
3. **No additional CBOR tags** are allowed (only tag 42).

Reference implementations:
- https://github.com/ipld/js-dag-cbor
- https://ipld.io/specs/codecs/dag-cbor/spec/
"""

from __future__ import annotations

from typing import Any

import cbor2
from cid import from_bytes as cid_from_bytes
from cid import make_cid

from ..codec import BlockCodec, register_codec
from ..ipld_model import CID, IPLDNode, is_cid, validate_string_map_keys
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

    def encode(self, node: IPLDNode) -> bytes:
        """Encode an IPLD value to DAG-CBOR bytes.

        CIDs are encoded as ``Tag(42, 0x00 || cid_bytes)``.
        Map keys are sorted using canonical CBOR ordering.
        """
        prepared = _prepare_for_cbor(node)
        return cbor2.dumps(
            prepared,
            canonical=True,
        )

    def decode(self, data: bytes) -> IPLDNode:
        """Decode DAG-CBOR bytes into an IPLD value.

        CBOR tag 42 values are converted back into CID objects.
        """
        raw = cbor2.loads(data, tag_hook=_tag_hook)
        return _restore_from_cbor(raw)


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


def _tag_hook(tag: cbor2.CBORTag, _ignore_tag_errors: bool = False) -> Any:
    """Handle CBOR tags during decoding.

    Only tag 42 (CID) is supported in DAG-CBOR.

    Signature matches ``cbor2`` 6.x: ``(tag, ignore_tag_errors)``.
    """
    if tag.tag == _CID_CBOR_TAG:
        cid_bytes = tag.value
        if isinstance(cid_bytes, bytes) and cid_bytes[:1] == _MULTIBASE_IDENTITY:
            cid_bytes = cid_bytes[1:]
        return _decode_cid_bytes(cid_bytes)
    raise ValueError(f"Unsupported CBOR tag {tag.tag} in DAG-CBOR (only tag 42 is allowed)")


def _decode_cid_bytes(raw_bytes: bytes) -> CID:
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
