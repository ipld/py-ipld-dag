import json
import warnings
from copy import deepcopy

import base58
import multihash

from .utils import node_to_link


def _ensure_bytes(value):
    """Convert a value to bytes.

    Accepts bytes, bytearray, memoryview, or str (encoded as UTF-8).
    Replaces the removed ``morphys.ensure_bytes`` dependency.
    """
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    raise TypeError(f"Cannot convert {type(value).__name__} to bytes")


# Design plan:
# Separate serialization from the node creation, serialization is
# dependent on the algorithm and the data, that can be either provided
# directly, or be implemented in a subclass
# If implementing in a subclass, then


# @TODO: if I can use immutable data structures, we can actually
# @TODO: get over all the data copying overhead involved
class Node:
    """Legacy MerkleDAG node.

    .. deprecated::
        Use :class:`dag.block.Block` and the codec API instead.
    """

    def __init__(self, data, links, serialized, multihash):
        warnings.warn(
            "dag.dag.Node is deprecated; use dag.Block and codecs instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._data = _ensure_bytes(data)

        if isinstance(multihash, bytes):
            self._multihash = base58.b58decode(multihash)
        else:
            raise TypeError("multihash should be either a str or bytes object")

        self._serialized = serialized
        self._links = [] if links is None else links
        self._size = sum((link.size for link in self._links), len(self._serialized))

    @property
    def data(self):
        return self._data

    @property
    def multihash(self):
        return self._multihash

    @property
    def serialized(self):
        return self._serialized

    @property
    def links(self):
        return self._links

    @property
    def size(self):
        return self._size

    @classmethod
    def create(cls, data, links=None, hash_algorithm="sha2-256", serializer=json.dumps):
        links = [link for link in links if isinstance(link, Link)] if links is not None else []
        serialized = _ensure_bytes(serializer({"data": data, "links": links}))
        mh = multihash.digest(serialized, hash_algorithm).encode("base58")

        return Node(data, links, serialized, mh)

    # @TODO: should not be a class method
    @classmethod
    def add_link(cls, node, link):
        node = deepcopy(node)

        if isinstance(link, Node):
            link = node_to_link(link)

        node.links.append(link)

        # @TODO: specify other creation parameters from the given node
        return cls.create(node.data, node.links)

    # @TODO: should not be a class method
    @classmethod
    def remove_link(cls, node, name_or_multihash):
        node = deepcopy(node)

        node.links = [
            link for link in node.links if not (node.name == name_or_multihash or node.multihash == name_or_multihash)
        ]

        # @TODO: specify other creation parameters from the given node
        return cls.create(node.data, node.links)

    def clone(self):
        return deepcopy(self)

    def __repr__(self):
        return '{class_}("{multihash}", data="{data}", links={links}, size={size})'.format(
            class_=self.__class__.__name__,
            multihash=base58.b58encode(self._multihash),
            data=self._data[:20] + ".." if len(self._data) > 20 else "",  # pyrefly: ignore
            links=len(self._links),
            size=self._size,
        )

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def __len__(self):
        return self._size


class Link:
    """Legacy MerkleDAG link.

    .. deprecated::
        Use CID links in the Block/codec API instead.
    """

    def __init__(self, name, size, multihash):
        warnings.warn(
            "dag.dag.Link is deprecated; use CID links via dag.Block instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._name = name
        self._size = size
        self._multihash = multihash

    def serialize(self):
        pass

    def __repr__(self):
        return '{class_}(name="{name}", size={size}, multihash="{multihash}"'.format(
            class_=self.__class__.__name__,
            name=self._name,
            size=self._size,
            multihash=self._multihash,
        )

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result
