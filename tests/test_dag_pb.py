#!/usr/bin/env python3
"""Comprehensive tests for the DAG-PB codec."""

import multihash
import pytest
from cid import make_cid

from dag import Block, is_cid
from dag.codecs.dag_pb import (
    PBLink,
    PBNode,
    codec,
    decode,
    encode,
)


class DagPbBasicTestCase:
    """Basic DAG-PB encoding/decoding tests."""

    def test_codec_name(self):
        assert codec.name == "dag-pb"

    def test_codec_code(self):
        assert codec.code == 0x70

    def test_encode_data_only(self):
        val = {"Data": b"hello", "Links": []}
        result = encode(val)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_decode_data_only(self):
        val = {"Data": b"hello", "Links": []}
        encoded = encode(val)
        decoded = decode(encoded)
        assert decoded["Data"] == b"hello"
        assert decoded["Links"] == []

    def test_roundtrip_data(self):
        val = {"Data": b"hello dag-pb world", "Links": []}
        decoded = decode(encode(val))
        assert decoded["Data"] == b"hello dag-pb world"

    def test_empty_data(self):
        val = {"Data": b"", "Links": []}
        decoded = decode(encode(val))
        assert decoded["Data"] == b""

    def test_no_data(self):
        val = {"Data": None, "Links": []}
        decoded = decode(encode(val))
        assert decoded["Data"] is None

    def test_encode_pbnode_object(self):
        node = PBNode(data=b"test data")
        result = encode(node)
        decoded = decode(result)
        assert decoded["Data"] == b"test data"


class DagPbLinksTestCase:
    """Tests for link handling in DAG-PB."""

    @pytest.fixture
    def sample_cid(self):
        mh = multihash.digest(b"test data", "sha2-256")
        return make_cid(1, "dag-cbor", mh.encode())

    def test_link_with_all_fields(self, sample_cid):
        val = {
            "Data": b"parent",
            "Links": [
                {"Hash": sample_cid, "Name": "child", "Tsize": 100},
            ],
        }
        decoded = decode(encode(val))
        link = decoded["Links"][0]
        assert is_cid(link["Hash"])
        assert str(link["Hash"]) == str(sample_cid)
        assert link["Name"] == "child"
        assert link["Tsize"] == 100

    def test_link_hash_only(self, sample_cid):
        val = {
            "Data": None,
            "Links": [{"Hash": sample_cid}],
        }
        decoded = decode(encode(val))
        link = decoded["Links"][0]
        assert is_cid(link["Hash"])

    def test_multiple_links(self, sample_cid):
        mh2 = multihash.digest(b"other", "sha2-256")
        cid2 = make_cid(1, "dag-cbor", mh2.encode())

        val = {
            "Data": b"parent",
            "Links": [
                {"Hash": sample_cid, "Name": "a", "Tsize": 10},
                {"Hash": cid2, "Name": "b", "Tsize": 20},
            ],
        }
        decoded = decode(encode(val))
        assert len(decoded["Links"]) == 2
        assert decoded["Links"][0]["Name"] == "a"
        assert decoded["Links"][1]["Name"] == "b"

    def test_links_sorted_by_name_for_canonical_encode(self, sample_cid):
        mh2 = multihash.digest(b"other", "sha2-256")
        cid2 = make_cid(1, "dag-cbor", mh2.encode())
        mh3 = multihash.digest(b"unnamed", "sha2-256")
        cid3 = make_cid(1, "dag-cbor", mh3.encode())

        ordered = {
            "Data": b"parent",
            "Links": [
                {"Hash": sample_cid, "Name": "alpha", "Tsize": 1},
                {"Hash": cid2, "Name": "beta", "Tsize": 2},
                {"Hash": cid3, "Tsize": 3},
            ],
        }
        reversed_named = {
            "Data": b"parent",
            "Links": [
                {"Hash": cid3, "Tsize": 3},
                {"Hash": cid2, "Name": "beta", "Tsize": 2},
                {"Hash": sample_cid, "Name": "alpha", "Tsize": 1},
            ],
        }
        assert encode(ordered) == encode(reversed_named)
        decoded = decode(encode(reversed_named))
        assert [link.get("Name") for link in decoded["Links"]] == [
            "alpha",
            "beta",
            None,
        ]

    def test_link_without_name(self, sample_cid):
        val = {
            "Data": b"data",
            "Links": [{"Hash": sample_cid, "Tsize": 50}],
        }
        decoded = decode(encode(val))
        link = decoded["Links"][0]
        assert link.get("Name") is None
        assert link["Tsize"] == 50

    def test_link_without_tsize(self, sample_cid):
        val = {
            "Data": b"data",
            "Links": [{"Hash": sample_cid, "Name": "x"}],
        }
        decoded = decode(encode(val))
        link = decoded["Links"][0]
        assert link["Name"] == "x"
        assert link.get("Tsize") is None

    def test_empty_links(self):
        val = {"Data": b"leaf", "Links": []}
        decoded = decode(encode(val))
        assert decoded["Links"] == []

    def test_pblink_object(self, sample_cid):
        link = PBLink(hash=sample_cid, name="test", tsize=42)
        node = PBNode(data=b"hello", links=[link])
        decoded = decode(encode(node))
        assert decoded["Links"][0]["Name"] == "test"


class DagPbValidationTestCase:
    """Tests for input validation in DAG-PB."""

    def test_invalid_input_type(self):
        with pytest.raises(TypeError):
            encode("not a valid input")

    def test_invalid_data_type(self):
        with pytest.raises(TypeError):
            encode({"Data": "string not bytes", "Links": []})

    def test_invalid_link_hash_type(self):
        with pytest.raises(TypeError):
            encode(
                {
                    "Data": b"test",
                    "Links": [{"Hash": "not a cid"}],
                }
            )


class DagPbBlockTestCase:
    """Tests for Block integration with DAG-PB."""

    @pytest.fixture
    def sample_cid(self):
        mh = multihash.digest(b"child data", "sha2-256")
        return make_cid(1, "dag-cbor", mh.encode())

    def test_block_encode(self):
        val = {"Data": b"hello", "Links": []}
        block = Block.encode(value=val, codec=codec)
        assert block.cid is not None
        assert len(block.bytes) > 0

    def test_block_decode(self):
        val = {"Data": b"hello", "Links": []}
        block = Block.encode(value=val, codec=codec)
        decoded = Block.decode(data=block.bytes, codec=codec)
        assert decoded.value["Data"] == b"hello"

    def test_block_with_links(self, sample_cid):
        val = {
            "Data": b"parent",
            "Links": [
                {"Hash": sample_cid, "Name": "child", "Tsize": 42},
            ],
        }
        block = Block.encode(value=val, codec=codec)
        decoded = Block.decode(data=block.bytes, codec=codec)
        assert decoded.value["Links"][0]["Name"] == "child"

    def test_block_encode_by_code(self):
        val = {"Data": b"test", "Links": []}
        block = Block.encode(value=val, codec=0x70)
        assert block.value == val
