"""Raw codec - identity codec for raw binary data.

Multicodec code: ``0x55``

The raw codec performs no transformation: ``encode`` returns the bytes
as-is, and ``decode`` returns the bytes as-is. It is used when the
block content is opaque binary data with no internal structure.

Reference: https://github.com/multiformats/js-multiformats
"""

from __future__ import annotations

import io
from typing import BinaryIO

from ..codec import BlockCodec, register_codec
from ..ipld_model import IPLDNode
from ..multicodec_codes import RAW_CODE, RAW_NAME


class RawCodec(BlockCodec):
    """Raw binary codec (``0x55``).

    Passes bytes through unchanged.
    """

    @property
    def name(self) -> str:
        return RAW_NAME

    @property
    def code(self) -> int:
        return RAW_CODE

    def encode_to_stream(self, node: IPLDNode, stream: BinaryIO) -> int:
        """Write raw bytes to *stream* (identity)."""
        if not isinstance(node, (bytes, bytearray)):
            raise TypeError(f"Raw codec can only encode bytes, got {type(node).__name__}")
        return stream.write(bytes(node))

    def decode_from_stream(self, stream: BinaryIO) -> IPLDNode:
        """Read raw bytes from *stream* (identity)."""
        return stream.read()

    def encode(self, node: IPLDNode) -> bytes:
        """Encode raw bytes (identity operation).

        *node* must be a ``bytes`` or ``bytearray`` instance.
        """
        buf = io.BytesIO()
        self.encode_to_stream(node, buf)
        return buf.getvalue()

    def decode(self, data: bytes) -> IPLDNode:
        """Decode raw bytes (identity operation).

        Returns the bytes unchanged.
        """
        return self.decode_from_stream(io.BytesIO(data))


codec = RawCodec()
"""Module-level singleton codec instance."""

name = codec.name
code = codec.code
encode = codec.encode
decode = codec.decode

register_codec(codec)
