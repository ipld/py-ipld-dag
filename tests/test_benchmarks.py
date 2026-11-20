"""Codec and Block encode/decode microbenchmarks (pytest-benchmark)."""

from __future__ import annotations

import pytest

from dag import Block
from dag.codecs import dag_cbor, dag_json, dag_pb, raw

BENCH_MAP = {"key": "value", "number": 42, "list": [1, 2, 3]}
BENCH_PB = {"Data": b"bench", "Links": []}
BENCH_RAW = b"benchmark-raw-payload"

BENCH_CBOR_BYTES = dag_cbor.encode(BENCH_MAP)
BENCH_JSON_BYTES = dag_json.encode(BENCH_MAP)
BENCH_PB_BYTES = dag_pb.encode(BENCH_PB)
BENCH_RAW_BYTES = raw.encode(BENCH_RAW)


@pytest.mark.benchmark
def test_bench_dag_cbor_encode(benchmark):
    benchmark(dag_cbor.encode, BENCH_MAP)


@pytest.mark.benchmark
def test_bench_dag_cbor_decode(benchmark):
    benchmark(dag_cbor.decode, BENCH_CBOR_BYTES)


@pytest.mark.benchmark
def test_bench_dag_json_encode(benchmark):
    benchmark(dag_json.encode, BENCH_MAP)


@pytest.mark.benchmark
def test_bench_dag_json_decode(benchmark):
    benchmark(dag_json.decode, BENCH_JSON_BYTES)


@pytest.mark.benchmark
def test_bench_dag_pb_encode(benchmark):
    benchmark(dag_pb.encode, BENCH_PB)


@pytest.mark.benchmark
def test_bench_dag_pb_decode(benchmark):
    benchmark(dag_pb.decode, BENCH_PB_BYTES)


@pytest.mark.benchmark
def test_bench_raw_encode(benchmark):
    benchmark(raw.encode, BENCH_RAW)


@pytest.mark.benchmark
def test_bench_raw_decode(benchmark):
    benchmark(raw.decode, BENCH_RAW_BYTES)


@pytest.mark.benchmark
def test_bench_block_encode(benchmark):
    benchmark(lambda: Block.encode(value=BENCH_MAP, codec=dag_cbor.codec))


@pytest.mark.benchmark
def test_bench_block_decode(benchmark):
    benchmark(lambda: Block.decode(data=BENCH_CBOR_BYTES, codec=dag_cbor.codec))
