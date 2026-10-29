#!/usr/bin/env python3
"""Comprehensive tests for the DAG-JSON codec."""

import json

import multihash
import pytest
from cid import make_cid

from dag import Block, is_cid
from dag.codecs.dag_json import codec, decode, encode


class DagJsonBasicTestCase:
    """Basic DAG-JSON encoding/decoding tests."""

    def test_codec_name(self):
        assert codec.name == "dag-json"

    def test_codec_code(self):
        assert codec.code == 0x0129

    def test_encode_simple_map(self):
        val = {"hello": "world"}
        result = encode(val)
        assert isinstance(result, bytes)
        parsed = json.loads(result)
        assert parsed == {"hello": "world"}

    def test_decode_simple_map(self):
        val = {"hello": "world"}
        encoded = encode(val)
        decoded = decode(encoded)
        assert decoded == val

    def test_roundtrip_string(self):
        val = "hello world"
        assert decode(encode(val)) == val

    def test_roundtrip_int(self):
        assert decode(encode(42)) == 42

    def test_roundtrip_float(self):
        result = decode(encode(3.14))
        assert abs(result - 3.14) < 1e-10

    def test_roundtrip_bool(self):
        assert decode(encode(True)) is True
        assert decode(encode(False)) is False

    def test_roundtrip_null(self):
        assert decode(encode(None)) is None

    def test_roundtrip_list(self):
        val = [1, "two", 3.0, True, None]
        assert decode(encode(val)) == val

    def test_roundtrip_nested(self):
        val = {"a": {"b": [1, {"c": "d"}]}}
        assert decode(encode(val)) == val

    def test_roundtrip_empty_map(self):
        assert decode(encode({})) == {}

    def test_roundtrip_empty_list(self):
        assert decode(encode([])) == []


class DagJsonBytesTestCase:
    """Tests for bytes handling in DAG-JSON."""

    def test_bytes_encoding_format(self):
        val = {"raw": b"\xde\xad\xbe\xef"}
        encoded = encode(val)
        parsed = json.loads(encoded)
        assert "/" in parsed["raw"]
        assert "bytes" in parsed["raw"]["/"]

    def test_bytes_roundtrip(self):
        val = {"raw": b"\xde\xad\xbe\xef"}
        decoded = decode(encode(val))
        assert decoded["raw"] == b"\xde\xad\xbe\xef"

    def test_empty_bytes_roundtrip(self):
        val = {"empty": b""}
        decoded = decode(encode(val))
        assert decoded["empty"] == b""

    def test_bytes_in_list(self):
        val = [b"\x01\x02", "text", b"\x03\x04"]
        decoded = decode(encode(val))
        assert decoded[0] == b"\x01\x02"
        assert decoded[1] == "text"
        assert decoded[2] == b"\x03\x04"


class DagJsonCidTestCase:
    """Tests for CID link handling in DAG-JSON."""

    @pytest.fixture
    def sample_cid(self):
        mh = multihash.digest(b"test data", "sha2-256")
        return make_cid(1, "dag-cbor", mh.encode())

    def test_cid_encoding_format(self, sample_cid):
        val = {"link": sample_cid}
        encoded = encode(val)
        parsed = json.loads(encoded)
        assert "/" in parsed["link"]
        assert isinstance(parsed["link"]["/"], str)

    def test_cid_roundtrip(self, sample_cid):
        val = {"link": sample_cid}
        decoded = decode(encode(val))
        assert is_cid(decoded["link"])
        assert str(decoded["link"]) == str(sample_cid)

    def test_cid_in_list(self, sample_cid):
        val = [sample_cid, "text"]
        decoded = decode(encode(val))
        assert is_cid(decoded[0])
        assert decoded[1] == "text"

    def test_nested_cid(self, sample_cid):
        val = {"outer": {"inner": sample_cid}}
        decoded = decode(encode(val))
        assert is_cid(decoded["outer"]["inner"])

    def test_cid_and_bytes_together(self, sample_cid):
        val = {"link": sample_cid, "data": b"\x01\x02\x03"}
        decoded = decode(encode(val))
        assert is_cid(decoded["link"])
        assert decoded["data"] == b"\x01\x02\x03"


class DagJsonValidationTestCase:
    """Tests for DAG-JSON encode validation."""

    def test_rejects_non_string_map_keys(self):
        with pytest.raises(TypeError, match="DAG-JSON map keys must be strings"):
            encode({1: "bad"})

    def test_rejects_nested_non_string_map_keys(self):
        with pytest.raises(TypeError, match="DAG-JSON map keys must be strings"):
            encode({"ok": {b"x": 1}})


class DagJsonDeterminismTestCase:
    """Tests for deterministic encoding."""

    def test_sorted_keys(self):
        val = {"z": 1, "a": 2, "m": 3}
        encoded = encode(val)
        parsed = json.loads(encoded)
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    def test_no_whitespace(self):
        val = {"hello": "world", "num": 42}
        encoded = encode(val).decode("utf-8")
        assert " " not in encoded
        assert "\n" not in encoded

    def test_deterministic_encoding(self):
        val1 = {"b": 2, "a": 1}
        val2 = {"a": 1, "b": 2}
        assert encode(val1) == encode(val2)


class DagJsonBlockTestCase:
    """Tests for Block integration with DAG-JSON."""

    def test_block_encode(self):
        val = {"hello": "world"}
        block = Block.encode(value=val, codec=codec)
        assert block.value == val
        assert block.cid is not None

    def test_block_decode(self):
        val = {"test": [1, 2, 3]}
        block = Block.encode(value=val, codec=codec)
        decoded = Block.decode(data=block.bytes, codec=codec)
        assert decoded.value == val

    def test_block_encode_by_code(self):
        val = {"test": 123}
        block = Block.encode(value=val, codec=0x0129)
        assert block.value == val
