"""Codec interface definitions for IPLD.

This module defines the abstract interfaces that every IPLD codec must
implement, following the same pattern as the JS ``@ipld/interface``
(``BlockEncoder`` / ``BlockDecoder`` / ``BlockCodec``).

A **codec** is identified by:
- ``name`` - a human-readable string (e.g. ``"dag-cbor"``)
- ``code`` - the multicodec code (e.g. ``0x71``)

And provides ``encode`` / ``decode`` (bytes) plus ``encode_to_stream`` /
``decode_from_stream`` (``BinaryIO``; Go Encoder/Decoder-shaped call sites).
"""

from __future__ import annotations

import abc
import io
from typing import BinaryIO

from .ipld_model import IPLDNode


class BlockEncoder(abc.ABC):
    """Abstract encoder - turns an IPLD node into bytes."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable codec name (e.g. ``'dag-cbor'``)."""

    @property
    @abc.abstractmethod
    def code(self) -> int:
        """Multicodec code (e.g. ``0x71``)."""

    @abc.abstractmethod
    def encode(self, node: IPLDNode) -> bytes:
        """Encode an IPLD data model value into bytes."""


class BlockDecoder(abc.ABC):
    """Abstract decoder - turns bytes into an IPLD node."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable codec name."""

    @property
    @abc.abstractmethod
    def code(self) -> int:
        """Multicodec code."""

    @abc.abstractmethod
    def decode(self, data: bytes) -> IPLDNode:
        """Decode bytes into an IPLD data model value."""


class BlockCodec(BlockEncoder, BlockDecoder):
    """A codec that can both encode and decode.

    Concrete implementations should subclass this and provide
    ``name``, ``code``, ``encode``, and ``decode``.

    Built-in codecs also override ``encode_to_stream`` /
    ``decode_from_stream`` to write/read wire bytes via ``BinaryIO``
    without requiring an intermediate full ``bytes`` blob. Default
    stream methods buffer via ``encode``/``decode`` for third-party
    codecs that only implement the bytes API.

    The IPLD value itself is still fully materialized in memory; stream
    methods improve the *wire* path (similar call shape to go-ipld-prime
    ``codec.Encoder`` / ``codec.Decoder``).
    """

    def encode_to_stream(self, node: IPLDNode, stream: BinaryIO) -> int:
        """Encode *node* into *stream*.

        Returns the number of bytes written. The default implementation
        encodes to ``bytes`` then writes; subclasses may override to
        stream the wire form directly (e.g. ``cbor2.dump``).
        """
        data = self.encode(node)
        return stream.write(data)

    def decode_from_stream(self, stream: BinaryIO) -> IPLDNode:
        """Decode an IPLD value from *stream*.

        The default implementation reads all remaining bytes then
        decodes; subclasses may override to parse from the stream
        incrementally (e.g. ``cbor2.load``).
        """
        data = stream.read()
        return self.decode(data)


class CountingWriter(io.RawIOBase):
    """Wrap a binary stream and count bytes written.

    Subclasses ``RawIOBase`` so callers like ``cbor2.dump`` accept it.
    """

    def __init__(self, stream: BinaryIO) -> None:
        super().__init__()
        self._stream = stream
        self.written = 0

    def writable(self) -> bool:
        return True

    def readable(self) -> bool:
        return False

    def seekable(self) -> bool:
        return False

    def write(self, data: bytes | bytearray | memoryview | None) -> int:  # type: ignore[override]
        if data is None:
            return 0
        payload = data.tobytes() if isinstance(data, memoryview) else bytes(data)
        n = self._stream.write(payload)
        if n is None:
            n = len(payload)
        self.written += n
        return n

    def flush(self) -> None:
        flush = getattr(self._stream, "flush", None)
        if flush is None:
            return
        try:
            flush()
        except ValueError:
            # Underlying stream may already be closed during finalization.
            pass

    def close(self) -> None:
        # Do not close the wrapped stream; callers own its lifetime.
        if not self.closed:
            io.RawIOBase.close(self)


_codec_registry: dict[int, BlockCodec] = {}


def register_codec(codec: BlockCodec) -> None:
    """Register a codec so it can be looked up by code."""
    _codec_registry[codec.code] = codec


def get_codec(code: int) -> BlockCodec:
    """Look up a registered codec by its multicodec code.

    Raises ``KeyError`` if no codec is registered for *code*.
    """
    if code not in _codec_registry:
        raise KeyError(
            f"No codec registered for code 0x{code:x}. Registered: {sorted(f'0x{c:x}' for c in _codec_registry)}"
        )
    return _codec_registry[code]


def registered_codecs() -> dict[int, BlockCodec]:
    """Return a copy of all registered codecs."""
    return dict(_codec_registry)


def lookup_codec(name_or_code: str | int) -> BlockCodec:
    """Look up a codec by name or code.

    Raises ``KeyError`` if not found.
    """
    if isinstance(name_or_code, int):
        return get_codec(name_or_code)

    for codec in _codec_registry.values():
        if codec.name == name_or_code:
            return codec
    raise KeyError(f"No codec registered with name {name_or_code!r}")
