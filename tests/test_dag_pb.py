#!/usr/bin/env python3
"""Comprehensive tests for the DAG-PB codec."""

import multihash
import pytest
from cid import make_cid

from dag import Block, is_cid, lookup_codec
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
        assert decoded == {"Links": []}

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
            None,
            "alpha",
            "beta",
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


class DagPbCidV0LinkTestCase:
    """Link Hash bytes holding a CIDv0 (a bare multihash, no version byte)."""

    # ipld/codec-fixtures fixtures/dagpb_1link
    FIXTURE_HEX = "12240a2212207521fe19c374a97759226dc5c0c8e674e73950e81b211f7dd3b6b30883a08a51"
    FIXTURE_CID = "bafybeihyivpglm6o6wrafbe36fp5l67abmewk7i2eob5wacdbhz7as5obe"
    LINK_CID = "QmWDtUQj38YLW8v3q4A6LwPn4vYKEbuKWpgSm6bjKW6Xfe"

    def test_decode_cidv0_link(self):
        value = decode(bytes.fromhex(self.FIXTURE_HEX))
        link_hash = value["Links"][0]["Hash"]
        assert link_hash.version == 0
        assert str(link_hash) == self.LINK_CID

    def test_cidv0_link_roundtrip(self):
        data = bytes.fromhex(self.FIXTURE_HEX)
        assert encode(decode(data)) == data

    def test_cidv0_link_block_cid(self):
        block = Block.decode(data=bytes.fromhex(self.FIXTURE_HEX), codec=codec)
        assert block.cid.buffer == make_cid(self.FIXTURE_CID).buffer


class DagPbLinkSortTestCase:
    """Link sorting per the DAG-PB spec: by Name bytes, missing Name == "", stable."""

    LINK = "bafkqabiaaebagba"

    def _link(self, name=None):
        link = {"Hash": make_cid(self.LINK)}
        if name is not None:
            link["Name"] = name
        return link

    def test_unnamed_sorts_first_fixture_simple_forms_2(self):
        # ipld/codec-fixtures fixtures/dagpb_simple_forms_2
        expected = bytes.fromhex(
            "120b0a0901550005000102030412100a09015500050001020304120362617212100a090155000500010203041203666f6f"
        )
        val = {"Links": [self._link("foo"), self._link("bar"), self._link()]}
        assert encode(val) == expected

    def test_duplicate_names_stable_fixture_simple_forms_3(self):
        # ipld/codec-fixtures fixtures/dagpb_simple_forms_3
        expected = bytes.fromhex(
            "120b0a09015500050001020304120e0a09015500050001020304120161120e0a09015500050001020304120161"
        )
        val = {"Links": [self._link("a"), self._link("a"), self._link()]}
        assert encode(val) == expected

    def test_missing_and_empty_name_keep_order(self):
        val = {"Links": [self._link(""), self._link(), self._link("a")]}
        names = [link.get("Name") for link in decode(encode(val))["Links"]]
        assert names == ["", None, "a"]

    def test_sort_is_bytewise_not_length_first(self):
        val = {"Links": [self._link("b"), self._link("aa"), self._link("a")]}
        names = [link.get("Name") for link in decode(encode(val))["Links"]]
        assert names == ["a", "aa", "b"]


class DagPbDataModelFormTestCase:
    """Decoded data-model form: absent Data is omitted, Links always present."""

    def test_empty_block_decodes_without_data(self):
        # ipld/codec-fixtures fixtures/dagpb_empty: data model is {"Links": []}
        assert decode(b"") == {"Links": []}

    def test_present_data_kept(self):
        # ipld/codec-fixtures fixtures/dagpb_Data_some
        assert decode(bytes.fromhex("0a050001020304")) == {"Data": b"\x00\x01\x02\x03\x04", "Links": []}

    @pytest.mark.parametrize(
        "codec_name, expected_cid",
        [
            ("dag-cbor", "bafyreihjsq5okmwdasf4hoiauwxv3vxjuwh2kuh4k5pgzzi3hanepxusjm"),
            ("dag-json", "baguqeera6mfu3g6n722vx7dbitpnbiyqnwah4ddy4b5c3rwzxc5pntqcupta"),
        ],
    )
    def test_empty_block_cross_codec_cid(self, codec_name, expected_cid):
        # Re-encoding the decoded dagpb_empty value must give the fixture CIDs.
        block = Block.encode(value=decode(b""), codec=lookup_codec(codec_name))
        assert block.cid.buffer == make_cid(expected_cid).buffer

    def test_decoded_value_re_encodes(self):
        assert encode(decode(b"")) == b""
