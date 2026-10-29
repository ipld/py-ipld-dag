#!/usr/bin/env python3
"""Tests for the Block class."""

import pytest

from dag import Block, is_cid
from dag.codecs import dag_cbor, dag_pb


class BlockEncodeTestCase:
    """Tests for Block.encode()."""

    def test_encode_returns_block(self):
        block = Block.encode(value={"test": True}, codec=dag_cbor.codec)
        assert isinstance(block, Block)

    def test_encode_has_cid(self):
        block = Block.encode(value={"test": True}, codec=dag_cbor.codec)
        assert block.cid is not None

    def test_encode_has_bytes(self):
        block = Block.encode(value={"test": True}, codec=dag_cbor.codec)
        assert isinstance(block.bytes, bytes)
        assert len(block.bytes) > 0

    def test_encode_has_value(self):
        val = {"test": True}
        block = Block.encode(value=val, codec=dag_cbor.codec)
        assert block.value == val

    def test_encode_has_codec(self):
        block = Block.encode(value={"test": True}, codec=dag_cbor.codec)
        assert block.codec is dag_cbor.codec

    def test_encode_by_int_code(self):
        block = Block.encode(value={"test": True}, codec=0x71)
        assert block.cid is not None

    def test_encode_deterministic_cid(self):
        val = {"a": 1, "b": 2}
        block1 = Block.encode(value=val, codec=dag_cbor.codec)
        block2 = Block.encode(value=val, codec=dag_cbor.codec)
        assert str(block1.cid) == str(block2.cid)
        assert block1.bytes == block2.bytes

    def test_encode_cidv0_requires_dag_pb(self):
        with pytest.raises(ValueError, match="CIDv0 requires the dag-pb codec"):
            Block.encode(value={"hello": True}, codec=dag_cbor.codec, version=0)

    def test_encode_cidv0_requires_sha2_256(self):
        with pytest.raises(ValueError, match="CIDv0 requires the sha2-256 hasher"):
            Block.encode(
                value={"Data": b"x", "Links": []},
                codec=dag_pb.codec,
                version=0,
                hasher="sha2-512",
            )

    def test_encode_cidv0_dag_pb_ok(self):
        block = Block.encode(
            value={"Data": b"hello", "Links": []},
            codec=dag_pb.codec,
            version=0,
        )
        assert block.cid.version == 0


class BlockDecodeTestCase:
    """Tests for Block.decode()."""

    def test_decode_returns_block(self):
        block = Block.encode(value={"hello": "world"}, codec=dag_cbor.codec)
        decoded = Block.decode(data=block.bytes, codec=dag_cbor.codec)
        assert isinstance(decoded, Block)

    def test_decode_value_matches(self):
        val = {"hello": "world", "num": 42}
        block = Block.encode(value=val, codec=dag_cbor.codec)
        decoded = Block.decode(data=block.bytes, codec=dag_cbor.codec)
        assert decoded.value == val

    def test_decode_cid_matches(self):
        val = {"hello": "world"}
        block = Block.encode(value=val, codec=dag_cbor.codec)
        decoded = Block.decode(data=block.bytes, codec=dag_cbor.codec)
        assert str(decoded.cid) == str(block.cid)


class BlockCreateTestCase:
    """Tests for Block.create()."""

    def test_create_from_parts(self):
        val = {"test": True}
        block = Block.encode(value=val, codec=dag_cbor.codec)
        created = Block.create(
            data=block.bytes,
            cid=block.cid,
            value=val,
        )
        assert str(created.cid) == str(block.cid)
        assert created.bytes == block.bytes
        assert created.value == val


class BlockTraversalTestCase:
    """Tests for Block traversal methods."""

    @pytest.fixture
    def inner_block(self):
        return Block.encode(value={"inner": True}, codec=dag_cbor.codec)

    def test_links_empty(self):
        block = Block.encode(value={"no": "links"}, codec=dag_cbor.codec)
        assert list(block.links()) == []

    def test_links_one(self, inner_block):
        block = Block.encode(
            value={"link": inner_block.cid},
            codec=dag_cbor.codec,
        )
        links = list(block.links())
        assert len(links) == 1
        assert links[0][0] == "link"
        assert is_cid(links[0][1])

    def test_links_nested(self, inner_block):
        block = Block.encode(
            value={
                "a": {"b": inner_block.cid},
                "c": [inner_block.cid],
            },
            codec=dag_cbor.codec,
        )
        links = list(block.links())
        assert len(links) == 2

    def test_tree(self, inner_block):
        block = Block.encode(
            value={"a": 1, "b": {"c": 2}},
            codec=dag_cbor.codec,
        )
        paths = list(block.tree())
        assert "a" in paths
        assert "b" in paths
        assert "b/c" in paths

    def test_get_map_key(self):
        block = Block.encode(
            value={"hello": "world"},
            codec=dag_cbor.codec,
        )
        assert block.get("hello") == "world"

    def test_get_nested(self):
        block = Block.encode(
            value={"a": {"b": {"c": 42}}},
            codec=dag_cbor.codec,
        )
        assert block.get("a/b/c") == 42

    def test_get_list_index(self):
        block = Block.encode(
            value={"items": [10, 20, 30]},
            codec=dag_cbor.codec,
        )
        assert block.get("items/1") == 20

    def test_get_invalid_key(self):
        block = Block.encode(
            value={"hello": "world"},
            codec=dag_cbor.codec,
        )
        with pytest.raises(KeyError):
            block.get("nonexistent")


class BlockEqualityTestCase:
    """Tests for Block equality and hashing."""

    def test_equal_blocks(self):
        val = {"test": True}
        block1 = Block.encode(value=val, codec=dag_cbor.codec)
        block2 = Block.encode(value=val, codec=dag_cbor.codec)
        assert block1 == block2

    def test_unequal_blocks(self):
        block1 = Block.encode(value={"a": 1}, codec=dag_cbor.codec)
        block2 = Block.encode(value={"b": 2}, codec=dag_cbor.codec)
        assert block1 != block2

    def test_block_hash(self):
        val = {"test": True}
        block1 = Block.encode(value=val, codec=dag_cbor.codec)
        block2 = Block.encode(value=val, codec=dag_cbor.codec)
        assert hash(block1) == hash(block2)

    def test_block_in_set(self):
        val = {"test": True}
        block1 = Block.encode(value=val, codec=dag_cbor.codec)
        block2 = Block.encode(value=val, codec=dag_cbor.codec)
        s = {block1, block2}
        assert len(s) == 1

    def test_block_len(self):
        block = Block.encode(value={"hello": "world"}, codec=dag_cbor.codec)
        assert len(block) == len(block.bytes)

    def test_block_repr(self):
        block = Block.encode(value={"hello": "world"}, codec=dag_cbor.codec)
        r = repr(block)
        assert "Block" in r
        assert "size=" in r
