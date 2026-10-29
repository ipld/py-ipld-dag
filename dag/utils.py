"""Utility functions for py-ipld-dag.

Provides helpers for working with IPLD blocks, CIDs, and codecs.
"""

from __future__ import annotations

from typing import Any

import multihash as _multihash
from cid import from_bytes as cid_from_bytes
from cid import make_cid

from .ipld_model import CID


def create_cid(
    data: bytes,
    codec: str = "dag-cbor",
    hasher: str = "sha2-256",
    version: int = 1,
) -> CID:
    """Create a CID from raw encoded bytes.

    Parameters
    ----------
    data:
        The encoded bytes to hash.
    codec:
        The codec name (e.g. ``"dag-cbor"``).
    hasher:
        The multihash algorithm (e.g. ``"sha2-256"``).
    version:
        CID version (``0`` or ``1``).

    Returns
    -------
    CID
        A new CID object.
    """
    mh = _multihash.digest(data, hasher)
    return make_cid(version, codec, mh.encode())


def cid_to_bytes(cid_obj: CID) -> bytes:
    """Convert a CID object to its binary representation."""
    return cid_obj.buffer


def bytes_to_cid(raw: bytes) -> CID:
    """Parse a CID from its binary representation."""
    return cid_from_bytes(raw)


def cid_to_string(cid_obj: CID) -> str:
    """Convert a CID to its string representation."""
    return str(cid_obj)


def string_to_cid(s: str) -> CID:
    """Parse a CID from a string."""
    return make_cid(s)


def node_to_link(node: Any) -> Any:
    """Convert a legacy Node to a legacy Link.

    .. deprecated::
        This function is retained for backward compatibility only.
        Use the codec/block API instead.
    """
    import warnings

    warnings.warn(
        "node_to_link() is deprecated; use dag.Block and codecs instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from .dag import Link, Node

    if not isinstance(node, Node):
        raise TypeError("node should be an instance of type Node")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return Link("", node.size, node.multihash)


def collect_links(value: Any) -> list[tuple[str, CID]]:
    """Collect all CID links from an IPLD data-model value.

    Returns a list of ``(path, cid)`` tuples.

    Uses :func:`dag.block.walk_links` internally to avoid
    duplicating the recursive traversal logic.
    """
    from .block import walk_links

    return list(walk_links(value))
