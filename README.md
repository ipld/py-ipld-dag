# py-ipld-dag

[![PyPI version](https://img.shields.io/pypi/v/py-ipld-dag.svg)](https://pypi.python.org/pypi/py-ipld-dag)
[![Documentation](https://readthedocs.org/projects/dag/badge/?version=latest)](https://py-ipld-dag.readthedocs.io/en/latest/?badge=latest)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**IPLD DAG implementation for Python** — codecs for DAG-CBOR, DAG-JSON, DAG-PB, and Raw, aligned with the [js-multiformats](https://github.com/multiformats/js-multiformats) ecosystem.

Provides:

- **DAG-CBOR** (`0x71`) – Deterministic CBOR with CID links (CBOR tag 42)
- **DAG-JSON** (`0x0129`) – Deterministic JSON with CID links (`{"/": "bafy..."}`)
- **DAG-PB** (`0x70`) – Protobuf-based Merkle DAG nodes (legacy IPFS/UnixFS)
- **Raw** (`0x55`) – Identity codec for raw binary data
- **Block API** – `Block.encode()` / `Block.decode()` / `Block.create()`
- **Codec registry** – Pluggable codec architecture with auto-registration
- **IPLD Data Model** – Full support for Null, Bool, Int, Float, String, Bytes, List, Map, Link kinds
- **CID integration** – Seamless use of [py-cid](https://github.com/ipld/py-cid) for content addressing

Read more in the [documentation on ReadTheDocs](https://py-ipld-dag.readthedocs.io/en/latest/). [View the release notes](https://py-ipld-dag.readthedocs.io/en/latest/release_notes.html).

## Quick Start

```python
from dag import Block
from dag.codecs import dag_cbor, dag_json, dag_pb, raw

block = Block.encode(value={"hello": "world", "n": 42}, codec=dag_cbor.codec)
print(block.cid)
print(block.bytes)

restored = Block.decode(data=block.bytes, codec=dag_cbor.codec)
assert restored.value == {"hello": "world", "n": 42}

child = Block.encode(value={"child": True}, codec=dag_cbor.codec)
parent = Block.encode(
    value={"link": child.cid, "type": "parent"},
    codec=dag_cbor.codec,
)

for path, cid in parent.links():
    print(f"{path} -> {cid}")

json_block = Block.encode(
    value={"ref": child.cid, "data": b"\xde\xad"},
    codec=dag_json.codec,
)

pb_block = Block.encode(
    value={
        "Data": b"hello UnixFS",
        "Links": [{"Hash": child.cid, "Name": "child", "Tsize": 10}],
    },
    codec=dag_pb.codec,
)

raw_block = Block.encode(value=b"raw binary", codec=raw.codec)
```

## Examples

Example scripts are available in [`examples/`](examples/), including
Python equivalents of `js-multiformats` interface demos:

- `examples/block_interface/block_interface.py`
- `examples/cid_interface/cid_interface.py`
- `examples/multicodec_interface/multicodec_interface.py`
- `examples/multihash_interface/multihash_interface.py`

Run them from the repository root:

```bash
source venv/bin/activate
python -m examples.block_interface.block_interface
python -m examples.cid_interface.cid_interface
python -m examples.multicodec_interface.multicodec_interface
python -m examples.multihash_interface.multihash_interface
```

## Installation and usage

Installation (venv, pip/uv, stable and development) and usage are documented in the [docs](https://py-ipld-dag.readthedocs.io/en/latest/) — see **Installation** and **Usage** in the table of contents.

## Installation

**From PyPI (stable):**

```bash
pip install py-ipld-dag
```

**From source (development):**

Same as in [CONTRIBUTING.md](CONTRIBUTING.md). With **uv** (recommended):

```bash
git clone https://github.com/ipld/py-ipld-dag.git
cd py-ipld-dag
uv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
uv pip install --upgrade pip
uv pip install --group dev -e .
pre-commit install
```

With **pip** (requires pip >= 25.1):

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install --group dev -e .
pre-commit install
```

Or run **`make install-dev`** after activating a venv (uses uv).

Full usage, API reference, and examples: **[Documentation](https://dag.readthedocs.io/)**.

## Development

- **Tests:** `pytest` or `make test`
- **Lint:** `make lint` or `pre-commit run --all-files`
- **Docs:** `make docs-ci` (build docs with Sphinx)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and pull request guidelines.

## Release notes

Changelog and release notes are generated from [newsfragments](newsfragments/README.md) with [Towncrier](https://towncrier.readthedocs.io/) and published in the docs: [Release notes](https://py-ipld-dag.readthedocs.io/en/latest/release_notes.html).
