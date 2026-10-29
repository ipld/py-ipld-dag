"""Block - the fundamental unit of data in IPLD.

A **Block** binds together three things:
1. The raw encoded ``bytes``
2. A ``CID`` that addresses those bytes (hash + codec)
3. The decoded ``value`` (an IPLD data-model node)

This mirrors the JS ``@ipld/block`` design:
- ``Block.encode({ value, codec, hasher })`` → Block
- ``Block.decode({ bytes, codec, hasher })`` → Block
- ``Block.create({ bytes, cid, value, codec })`` → Block

Reference: https://github.com/multiformats/js-multiformats
"""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

import multihash as _multihash
from cid import make_cid

from .codec import BlockCodec, get_codec
from .ipld_model import CID, IPLDNode, is_cid


class Block:
    """An immutable IPLD block: ``CID`` + ``bytes`` + ``value``.

    Use the class methods ``encode``, ``decode``, or ``create``
    rather than calling ``__init__`` directly.
    """

    __slots__ = ("_bytes", "_cid", "_codec", "_value")

    def __init__(
        self,
        *,
        cid: CID,
        data: builtins.bytes,
        value: IPLDNode,
        codec: BlockCodec | None = None,
    ) -> None:
        self._cid = cid
        self._bytes = data
        self._value = value
        self._codec = codec

    @property
    def cid(self) -> CID:
        """The content identifier for this block."""
        return self._cid

    @property
    def bytes(self) -> bytes:
        """The raw encoded bytes."""
        return self._bytes

    @property
    def value(self) -> IPLDNode:
        """The decoded IPLD data-model value."""
        return self._value

    @property
    def codec(self) -> BlockCodec | None:
        """The codec used to create this block (if known)."""
        return self._codec

    @classmethod
    def encode(
        cls,
        *,
        value: IPLDNode,
        codec: BlockCodec | int,
        hasher: str = "sha2-256",
        version: int = 1,
    ) -> Block:
        """Encode an IPLD value into a new Block.

        Parameters
        ----------
        value:
            The IPLD data-model value to encode.
        codec:
            A ``BlockCodec`` instance or a multicodec code (int).
        hasher:
            Multihash algorithm name (default ``"sha2-256"``).
        version:
            CID version (default ``1``).  Use ``0`` only for dag-pb
            with sha2-256.
        """
        if isinstance(codec, int):
            codec = get_codec(codec)

        if version == 0:
            if codec.name != "dag-pb":
                raise ValueError(f"CIDv0 requires the dag-pb codec, got {codec.name!r}")
            if hasher != "sha2-256":
                raise ValueError(f"CIDv0 requires the sha2-256 hasher, got {hasher!r}")

        encoded = codec.encode(value)
        mh = _multihash.digest(encoded, hasher)
        cid = make_cid(version, codec.name, mh.encode())
        return cls(cid=cid, data=encoded, value=value, codec=codec)

    @classmethod
    def decode(
        cls,
        *,
        data: builtins.bytes,
        codec: BlockCodec | int,
        hasher: str = "sha2-256",
        version: int = 1,
    ) -> Block:
        """Decode raw bytes into a Block.

        Parameters
        ----------
        data:
            The raw encoded bytes.
        codec:
            A ``BlockCodec`` instance or a multicodec code (int).
        hasher:
            Multihash algorithm name (default ``"sha2-256"``).
        version:
            CID version (default ``1``).
        """
        if isinstance(codec, int):
            codec = get_codec(codec)

        if version == 0:
            if codec.name != "dag-pb":
                raise ValueError(f"CIDv0 requires the dag-pb codec, got {codec.name!r}")
            if hasher != "sha2-256":
                raise ValueError(f"CIDv0 requires the sha2-256 hasher, got {hasher!r}")

        value = codec.decode(data)
        mh = _multihash.digest(data, hasher)
        cid = make_cid(version, codec.name, mh.encode())
        return cls(cid=cid, data=data, value=value, codec=codec)

    @classmethod
    def create(
        cls,
        *,
        data: builtins.bytes,
        cid: CID,
        value: IPLDNode,
        codec: BlockCodec | None = None,
    ) -> Block:
        """Create a Block from pre-computed parts.

        No encoding, decoding, or hashing is performed.
        """
        return cls(cid=cid, data=data, value=value, codec=codec)

    def links(self) -> Iterator[tuple[str, CID]]:
        """Yield ``(path, cid)`` for every CID link in this block's value."""
        yield from walk_links(self._value, "")

    def tree(self) -> Iterator[str]:
        """Yield every path segment in this block's value (depth-first)."""
        yield from _walk_tree(self._value, "")

    def get(self, path: str) -> Any:
        """Resolve a ``/``-separated path into this block's value.

        Returns the value at that path, or raises ``KeyError`` /
        ``IndexError`` if the path is invalid.
        """
        segments = [s for s in path.split("/") if s]
        current: Any = self._value
        for seg in segments:
            if isinstance(current, dict):
                current = current[seg]
            elif isinstance(current, list):
                current = current[int(seg)]
            else:
                raise KeyError(f"Cannot traverse into {type(current).__name__} with {seg!r}")
        return current

    def __repr__(self) -> str:
        return f"Block(cid={self._cid!s}, size={len(self._bytes)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Block):
            return NotImplemented
        return self._cid.buffer == other._cid.buffer

    def __hash__(self) -> int:
        return hash(self._cid.buffer)

    def __len__(self) -> int:
        return len(self._bytes)


def walk_links(node: Any, prefix: str = "") -> Iterator[tuple[str, CID]]:
    """Recursively yield ``(path, cid)`` from an IPLD data-model value."""
    if is_cid(node):
        yield (prefix, node)
    elif isinstance(node, dict):
        for k, v in node.items():
            child = f"{prefix}/{k}" if prefix else k
            yield from walk_links(v, child)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            child = f"{prefix}/{i}" if prefix else str(i)
            yield from walk_links(v, child)


def _walk_tree(node: Any, prefix: str) -> Iterator[str]:
    """Recursively yield every path in an IPLD data-model value."""
    if isinstance(node, dict):
        for k, v in node.items():
            child = f"{prefix}/{k}" if prefix else k
            yield child
            yield from _walk_tree(v, child)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            child = f"{prefix}/{i}" if prefix else str(i)
            yield child
            yield from _walk_tree(v, child)
