"""DAG-JSON codec - deterministic JSON with IPLD CID links.

Multicodec code: ``0x0129``

DAG-JSON is JSON with special representations for IPLD types that
JSON cannot natively express:

1. **CID links** are encoded as ``{"/": "<cid-multibase-string>"}``
2. **Bytes** are encoded as ``{"/": {"bytes": "<base64-string>"}}``
3. Map keys are sorted lexicographically (by UTF-8 bytes).
4. No whitespace between tokens.

The ``{"/": ...}`` namespace is reserved:
- ``{"/": "<string>"}``      → CID link
- ``{"/": {"bytes": "..."}}`` → bytes value
- Any other ``{"/": ...}`` is an error in strict mode.

Reference implementations:
- https://github.com/ipld/js-dag-json
- https://ipld.io/specs/codecs/dag-json/spec/
"""

from __future__ import annotations

import base64
import json
from typing import Any

from cid import make_cid

from ..codec import BlockCodec, register_codec
from ..ipld_model import CID, IPLDNode, is_cid, validate_string_map_keys
from ..multicodec_codes import DAG_JSON_CODE, DAG_JSON_NAME

_LINK_KEY = "/"


class DagJsonCodec(BlockCodec):
    """DAG-JSON codec (``0x0129``).

    Encodes IPLD data-model values into deterministic JSON with
    CID links as ``{"/": "bafy..."}`` and bytes as
    ``{"/": {"bytes": "..."}}``.
    """

    @property
    def name(self) -> str:
        return DAG_JSON_NAME

    @property
    def code(self) -> int:
        return DAG_JSON_CODE

    def encode(self, node: IPLDNode) -> bytes:
        """Encode an IPLD value to DAG-JSON bytes.

        - CIDs → ``{"/": "<cid-string>"}``
        - bytes → ``{"/": {"bytes": "<base64-no-pad>"}}``
        - Map keys are sorted.
        - No whitespace.
        """
        prepared = _prepare_for_json(node)
        return json.dumps(prepared, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def decode(self, data: bytes) -> IPLDNode:
        """Decode DAG-JSON bytes into an IPLD value.

        Recognizes ``{"/": ...}`` sentinel objects and converts them
        back to CID or bytes values.
        """
        raw = json.loads(data)
        return _restore_from_json(raw)


def _base64_encode_no_pad(data: bytes) -> str:
    """Base64-encode *data* without padding (``=``) characters.

    DAG-JSON uses unpadded base64 for bytes representation.
    """
    return base64.b64encode(data).rstrip(b"=").decode("ascii")


def _prepare_for_json(node: Any) -> Any:
    """Recursively convert IPLD values for JSON serialization."""
    if is_cid(node):
        return {_LINK_KEY: str(node)}

    if isinstance(node, (bytes, bytearray)):
        return {_LINK_KEY: {"bytes": _base64_encode_no_pad(bytes(node))}}

    if isinstance(node, dict):
        validate_string_map_keys(node, context="DAG-JSON map")
        result = {}
        for k, v in node.items():
            result[k] = _prepare_for_json(v)
        return result

    if isinstance(node, list):
        return [_prepare_for_json(item) for item in node]

    return node


def _base64_decode_no_pad(s: str) -> bytes:
    """Decode an unpadded base64 string."""
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s += "=" * padding
    return base64.b64decode(s)


def _restore_from_json(node: Any) -> Any:
    """Recursively restore IPLD values from parsed JSON."""
    if isinstance(node, dict):
        if len(node) == 1 and _LINK_KEY in node:
            link_value = node[_LINK_KEY]

            if isinstance(link_value, str):
                return _parse_cid_string(link_value)

            if isinstance(link_value, dict) and len(link_value) == 1 and "bytes" in link_value:
                return _base64_decode_no_pad(link_value["bytes"])

        return {k: _restore_from_json(v) for k, v in node.items()}

    if isinstance(node, list):
        return [_restore_from_json(item) for item in node]

    return node


def _parse_cid_string(s: str) -> CID:
    """Parse a CID string into a CID object."""
    return make_cid(s)


codec = DagJsonCodec()
"""Module-level singleton codec instance."""

name = codec.name
code = codec.code
encode = codec.encode
decode = codec.decode

register_codec(codec)
