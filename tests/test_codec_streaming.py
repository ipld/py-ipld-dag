"""Stream encode/decode parity tests for built-in codecs."""

from __future__ import annotations

import io
from unittest.mock import patch

import cbor2
import pytest
from cid import make_cid

from dag.codecs import dag_cbor, dag_json, dag_pb, raw


class CodecStreamingTestCase:
    """BytesIO round-trips match encode/decode for every built-in codec."""

    def test_dag_cbor_stream_roundtrip(self):
        value = {"key": "value", "n": 42, "list": [1, 2, 3]}
        buf = io.BytesIO()
        n = dag_cbor.codec.encode_to_stream(value, buf)
        encoded = dag_cbor.encode(value)
        assert n == len(encoded)
        assert buf.getvalue() == encoded
        assert dag_cbor.codec.decode_from_stream(io.BytesIO(encoded)) == value
        assert dag_cbor.decode(encoded) == value

    def test_dag_cbor_stream_with_cid(self):
        cid = make_cid("bafkqabiaaebagba")
        value = {"link": cid, "data": b"hi"}
        encoded = dag_cbor.encode(value)
        buf = io.BytesIO()
        assert dag_cbor.codec.encode_to_stream(value, buf) == len(encoded)
        assert buf.getvalue() == encoded
        decoded = dag_cbor.codec.decode_from_stream(io.BytesIO(encoded))
        assert decoded["data"] == b"hi"
        assert str(decoded["link"]) == str(cid)

    def test_dag_cbor_encode_to_stream_uses_cbor2_dump(self):
        value = {"a": 1}
        with patch.object(cbor2, "dump", wraps=cbor2.dump) as dump_spy:
            buf = io.BytesIO()
            dag_cbor.codec.encode_to_stream(value, buf)
            dump_spy.assert_called()
        with patch.object(dag_cbor.codec, "encode") as encode_spy:
            buf = io.BytesIO()
            dag_cbor.codec.encode_to_stream(value, buf)
            encode_spy.assert_not_called()

    def test_dag_json_stream_roundtrip(self):
        value = {"key": "value", "n": 42, "list": [1, 2, 3]}
        buf = io.BytesIO()
        n = dag_json.codec.encode_to_stream(value, buf)
        encoded = dag_json.encode(value)
        assert n == len(encoded)
        assert buf.getvalue() == encoded
        assert dag_json.codec.decode_from_stream(io.BytesIO(encoded)) == value

    def test_dag_json_stream_with_cid(self):
        cid = make_cid("bafkqabiaaebagba")
        value = {"link": cid}
        encoded = dag_json.encode(value)
        buf = io.BytesIO()
        assert dag_json.codec.encode_to_stream(value, buf) == len(encoded)
        assert buf.getvalue() == encoded
        decoded = dag_json.codec.decode_from_stream(io.BytesIO(encoded))
        assert str(decoded["link"]) == str(cid)

    def test_dag_pb_stream_roundtrip(self):
        value = {"Data": b"bench", "Links": []}
        buf = io.BytesIO()
        n = dag_pb.codec.encode_to_stream(value, buf)
        encoded = dag_pb.encode(value)
        assert n == len(encoded)
        assert buf.getvalue() == encoded
        assert dag_pb.codec.decode_from_stream(io.BytesIO(encoded)) == value

    def test_raw_stream_roundtrip(self):
        value = b"benchmark-raw-payload"
        buf = io.BytesIO()
        n = raw.codec.encode_to_stream(value, buf)
        encoded = raw.encode(value)
        assert n == len(encoded)
        assert buf.getvalue() == encoded
        assert raw.codec.decode_from_stream(io.BytesIO(encoded)) == value

    def test_raw_encode_rejects_non_bytes(self):
        with pytest.raises(TypeError):
            raw.codec.encode_to_stream({"not": "bytes"}, io.BytesIO())
