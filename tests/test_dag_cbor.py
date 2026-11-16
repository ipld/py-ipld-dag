#!/usr/bin/env python3
"""Comprehensive tests for the DAG-CBOR codec."""

import multihash
import pytest
from cid import make_cid

from dag import Block, is_cid
from dag.codecs.dag_cbor import DagCborCodec, codec, decode, encode


class DagCborBasicTestCase:
    """Basic DAG-CBOR encoding/decoding tests."""

    def test_codec_name(self):
        assert codec.name == "dag-cbor"

    def test_codec_code(self):
        assert codec.code == 0x71

    def test_encode_simple_map(self):
        val = {"hello": "world"}
        result = encode(val)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_decode_simple_map(self):
        val = {"hello": "world"}
        encoded = encode(val)
        decoded = decode(encoded)
        assert decoded == val

    def test_roundtrip_string(self):
        val = "hello world"
        assert decode(encode(val)) == val

    def test_roundtrip_int(self):
        val = 42
        assert decode(encode(val)) == val

    def test_roundtrip_negative_int(self):
        val = -100
        assert decode(encode(val)) == val

    def test_roundtrip_float(self):
        val = 3.14
        result = decode(encode(val))
        assert abs(result - val) < 1e-10

    def test_roundtrip_bool_true(self):
        assert decode(encode(True)) is True

    def test_roundtrip_bool_false(self):
        assert decode(encode(False)) is False

    def test_roundtrip_null(self):
        assert decode(encode(None)) is None

    def test_roundtrip_bytes(self):
        val = b"\xde\xad\xbe\xef"
        assert decode(encode(val)) == val

    def test_roundtrip_empty_bytes(self):
        val = b""
        assert decode(encode(val)) == val

    def test_roundtrip_list(self):
        val = [1, "two", 3.0, True, None]
        assert decode(encode(val)) == val

    def test_roundtrip_empty_list(self):
        assert decode(encode([])) == []

    def test_roundtrip_nested_map(self):
        val = {"a": {"b": {"c": "deep"}}}
        assert decode(encode(val)) == val

    def test_roundtrip_complex_structure(self):
        val = {
            "name": "test",
            "version": 1,
            "tags": ["a", "b", "c"],
            "metadata": {
                "created": 1234567890,
                "active": True,
                "description": None,
            },
        }
        assert decode(encode(val)) == val

    def test_roundtrip_empty_map(self):
        assert decode(encode({})) == {}

    def test_roundtrip_large_int(self):
        val = 2**53
        assert decode(encode(val)) == val


class DagCborCidTestCase:
    """Tests for CID handling in DAG-CBOR."""

    @pytest.fixture
    def sample_cid(self):
        mh = multihash.digest(b"test data", "sha2-256")
        return make_cid(1, "dag-cbor", mh.encode())

    def test_encode_decode_cid(self, sample_cid):
        val = {"link": sample_cid}
        encoded = encode(val)
        decoded = decode(encoded)
        assert is_cid(decoded["link"])
        assert str(decoded["link"]) == str(sample_cid)

    def test_cid_in_list(self, sample_cid):
        val = [sample_cid, "text", sample_cid]
        decoded = decode(encode(val))
        assert is_cid(decoded[0])
        assert is_cid(decoded[2])
        assert decoded[1] == "text"

    def test_nested_cid(self, sample_cid):
        val = {"outer": {"inner": sample_cid}}
        decoded = decode(encode(val))
        assert is_cid(decoded["outer"]["inner"])

    def test_multiple_cids(self, sample_cid):
        mh2 = multihash.digest(b"other data", "sha2-256")
        cid2 = make_cid(1, "dag-cbor", mh2.encode())

        val = {"link1": sample_cid, "link2": cid2}
        decoded = decode(encode(val))
        assert is_cid(decoded["link1"])
        assert is_cid(decoded["link2"])
        assert str(decoded["link1"]) != str(decoded["link2"])

    def test_cid_v0(self):
        mh = multihash.digest(b"test data", "sha2-256")
        cid_v0 = make_cid(0, "dag-pb", mh.encode())
        val = {"link": cid_v0}
        decoded = decode(encode(val))
        assert is_cid(decoded["link"])


class DagCborValidationTestCase:
    """Tests for DAG-CBOR encode validation."""

    def test_rejects_non_string_map_keys(self):
        with pytest.raises(TypeError, match="DAG-CBOR map keys must be strings"):
            encode({1: "bad"})

    def test_rejects_nested_non_string_map_keys(self):
        with pytest.raises(TypeError, match="DAG-CBOR map keys must be strings"):
            encode({"ok": {b"x": 1}})


class DagCborDeterminismTestCase:
    """Tests for deterministic encoding."""

    def test_map_key_order_doesnt_matter(self):
        # Different insertion orders should produce same bytes
        val1 = {"b": 2, "a": 1, "c": 3}
        val2 = {"a": 1, "c": 3, "b": 2}
        assert encode(val1) == encode(val2)

    def test_same_value_same_bytes(self):
        val = {"hello": "world", "num": 42}
        assert encode(val) == encode(val)

    def test_encode_is_deterministic_across_instances(self):
        codec1 = DagCborCodec()
        codec2 = DagCborCodec()
        val = {"key": [1, 2, 3]}
        assert codec1.encode(val) == codec2.encode(val)


class DagCborBlockTestCase:
    """Tests for Block integration with DAG-CBOR."""

    def test_block_encode(self):
        val = {"hello": "world"}
        block = Block.encode(value=val, codec=codec)
        assert block.value == val
        assert len(block.bytes) > 0
        assert block.cid is not None

    def test_block_decode(self):
        val = {"hello": "world"}
        block = Block.encode(value=val, codec=codec)
        decoded = Block.decode(data=block.bytes, codec=codec)
        assert decoded.value == val

    def test_block_cid_consistency(self):
        val = {"test": True}
        block1 = Block.encode(value=val, codec=codec)
        block2 = Block.encode(value=val, codec=codec)
        assert str(block1.cid) == str(block2.cid)

    def test_block_with_links(self):
        inner = Block.encode(value={"inner": True}, codec=codec)
        outer = Block.encode(
            value={"link": inner.cid, "data": "outer"},
            codec=codec,
        )
        links = list(outer.links())
        assert len(links) == 1
        assert links[0][0] == "link"
        assert str(links[0][1]) == str(inner.cid)

    def test_block_encode_by_code(self):
        val = {"test": 123}
        block = Block.encode(value=val, codec=0x71)
        assert block.value == val
        assert block.cid is not None


class DagCborFloatTestCase:
    """DAG-CBOR floats: always 64-bit, no NaN/Infinity (spec "Strictness" 4-5)."""

    @pytest.mark.parametrize(
        "val, expected",
        [
            (1.5, "fb3ff8000000000000"),  # fits in half precision
            (0.0, "fb0000000000000000"),
            (100000.0, "fb40f86a0000000000"),  # fits in single precision
            (0.1, "fb3fb999999999999a"),
        ],
    )
    def test_float_encoded_as_64_bit(self, val, expected):
        assert encode(val).hex() == expected

    def test_nested_float_encoded_as_64_bit(self):
        assert encode({"f": [1.0]}).hex() == "a1616681fb3ff0000000000000"

    def test_bool_and_int_unaffected(self):
        assert encode([True, 1]).hex() == "82f501"

    @pytest.mark.parametrize("val", [float("nan"), float("inf"), float("-inf")])
    def test_rejects_non_finite_float(self, val):
        with pytest.raises(ValueError):
            encode({"x": [val]})

    def test_decode_accepts_half_precision(self):
        # Decoders may relax float width (spec "Decode strictness").
        assert decode(bytes.fromhex("f93e00")) == 1.5
