# -*- coding: utf-8 -*-

"""Main module."""
import base58
import multihash
from copy import deepcopy

from morphys import ensure_bytes

from .utils import node_to_link


# Design plan:
# Separate serialization from the node creation, serialization is
# dependent on the algorithm and the data, that can be either provided
# directly, or be implemented in a subclass
# If implementing in a subclass, then


# @TODO: if I can use immutable data structures, we can actually
# @TODO: get over all the data copying overhead involved
class Node(object):
    def __init__(self, data, links, serialized, multihash):
        self._data = ensure_bytes(data)

        if isinstance(multihash, bytes):
            self._multihash = base58.b58decode(multihash)
        else:
            raise TypeError('multihash should be either a str or bytes object')

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
    def create(cls, data, links=None, hash_algorithm='sha2-256', serializer=None):
        links = [l for l in links if isinstance(l, Link)] if links is not None else []
        serialized = ensure_bytes(serializer({'data': data, 'links': links}))
        mh = multihash.digest(serialized, hash_algorithm).encode('base58')

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
            link
            for link in node.links
            if not (node.name == name_or_multihash or node.multihash == name_or_multihash)
        ]

        # @TODO: specify other creation parameters from the given node
        return cls.create(node.data, node.links)

    def clone(self):
        return deepcopy(self)

    def __str__(self):
        pass

    def __repr__(self):
        return '{class_}("{multihash}", data="{data}", links={links}, size={size})'.format(
            class_=self.__class__.__name__,
            multihash=base58.b58encode(self._multihash),
            data=self._data[:20] + '..' if len(self._data) > 20 else '',
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


class Link(object):
    def __init__(self, name, size, multihash):
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
