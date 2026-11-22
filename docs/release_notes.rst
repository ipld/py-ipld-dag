Release notes
=============

.. towncrier release notes start

py-ipld-dag v0.3.0 (2026-11-22)
-------------------------------

Bugfixes
~~~~~~~~

- Sort DAG-PB links by Name during encode for canonical bytes. (`#23 <https://github.com/ipld/py-ipld-dag/issues/23>`__)
- Reject non-string map keys when encoding DAG-CBOR. (`#24 <https://github.com/ipld/py-ipld-dag/issues/24>`__)
- Reject non-string map keys when encoding DAG-JSON. (`#25 <https://github.com/ipld/py-ipld-dag/issues/25>`__)
- Validate that CIDv0 encoding requires dag-pb and sha2-256. (`#26 <https://github.com/ipld/py-ipld-dag/issues/26>`__)
- Raise ``LinkBoundaryError`` when ``Block.get`` would traverse a CID link. (`#27 <https://github.com/ipld/py-ipld-dag/issues/27>`__)
- Strictly validate DAG-JSON ``{"/": ...}`` forms on decode. (`#35 <https://github.com/ipld/py-ipld-dag/issues/35>`__)
- Fix DAG-CBOR CID decoding for ``cbor2`` 6.x ``tag_hook`` signature. (`#36 <https://github.com/ipld/py-ipld-dag/issues/36>`__)
- Decode DAG-PB links whose Hash is a CIDv0 (bare multihash) instead of raising. (`#47 <https://github.com/ipld/py-ipld-dag/issues/47>`__)
- Encode CIDv1 links in DAG-JSON as base32 strings, per the DAG-JSON spec, instead of base58btc. DAG-JSON bytes and CIDs change for values with CIDv1 links. (`#48 <https://github.com/ipld/py-ipld-dag/issues/48>`__)
- Sort DAG-PB links with a missing Name first, as empty strings, per the DAG-PB spec. DAG-PB bytes and CIDs change for nodes mixing named and unnamed links. (`#49 <https://github.com/ipld/py-ipld-dag/issues/49>`__)
- Encode DAG-CBOR floats as 64-bit doubles and reject NaN and Infinity in DAG-CBOR and DAG-JSON. DAG-CBOR bytes and CIDs change for values containing floats. (`#50 <https://github.com/ipld/py-ipld-dag/issues/50>`__)
- Write non-ASCII characters in DAG-JSON as raw UTF-8 instead of escaping them, matching other implementations. DAG-JSON bytes and CIDs change for values with non-ASCII text. (`#55 <https://github.com/ipld/py-ipld-dag/issues/55>`__)
- Omit Data from the decoded DAG-PB value when the block has none, instead of returning None. Code reading decoded["Data"] should use .get("Data"). (`#56 <https://github.com/ipld/py-ipld-dag/issues/56>`__)


Deprecations
~~~~~~~~~~~~

- Deprecate legacy ``Node``/``Link`` and ``node_to_link()`` in favor of ``Block``. (`#30 <https://github.com/ipld/py-ipld-dag/issues/30>`__)


Features
~~~~~~~~

- Add an optional ``depth`` limit to ``Block.tree()``. (`#28 <https://github.com/ipld/py-ipld-dag/issues/28>`__)
- Add ``encode_to_stream`` / ``decode_from_stream`` on codecs (``BinaryIO``), using ``cbor2``/``json`` dump-load for DAG-CBOR/JSON. The IPLD value is still fully materialized; the wire form can be written/read without an extra full intermediate ``bytes`` copy on the stream API. (`#32 <https://github.com/ipld/py-ipld-dag/issues/32>`__)


Internal Changes - for py-ipld-dag Contributors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Expose ``walk_links`` as a public helper instead of a private import. (`#31 <https://github.com/ipld/py-ipld-dag/issues/31>`__)


Miscellaneous Changes
~~~~~~~~~~~~~~~~~~~~~

- `#62 <https://github.com/ipld/py-ipld-dag/issues/62>`__


Performance Improvements
~~~~~~~~~~~~~~~~~~~~~~~~

- Add pytest-benchmark encode/decode microbenchmarks for DAG-CBOR, DAG-JSON, DAG-PB, raw, and ``Block``. (`#34 <https://github.com/ipld/py-ipld-dag/issues/34>`__)


py-ipld-dag v0.2.1 (2026-03-17)
-------------------------------

Improved Documentation
~~~~~~~~~~~~~~~~~~~~~~

- Fix documentation: all ReadTheDocs links and badge now point to ``py-ipld-dag.readthedocs.io``.
  Contributor docs now list only ``make`` as a system prerequisite (removed incorrect CMake, pkg-config, and GMP requirements). (`#21 <https://github.com/ipld/py-ipld-dag/issues/21>`__)


py-ipld-dag v0.2.0 (2026-03-15)
-------------------------------

Improved Documentation
~~~~~~~~~~~~~~~~~~~~~~

- Added Examples to docs. (`#20 <https://github.com/ipld/py-ipld-dag/issues/20>`__)


Features
~~~~~~~~

- Add Block API, IPLD data-model layer, multicodec registry, and four codec implementations (DAG-CBOR, DAG-JSON, DAG-PB, raw). The new design mirrors the JS multiformats ecosystem with encode/decode/create class methods, CID-based addressing, and pluggable codec registration. (`#17 <https://github.com/ipld/py-ipld-dag/issues/17>`__)


Internal Changes - for py-ipld-dag Contributors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Migrate from the legacy setup.cfg to modern pyproject.toml and add pre-commit hooks. Remove Travis CI with GitHub actions.
  Add new make commands and improve the project infrastructure. All changes are internal and does not affect the core modules. (`#12 <https://github.com/ipld/py-ipld-dag/issues/12>`__)
- Align the project's Pull Request workflow with ``py-libp2p`` by requiring a
  corresponding issue for every PR. Updated ``CONTRIBUTING.md``,
  ``newsfragments/README.md``, and the validation script to mandate that all
  newsfragments use numeric issue numbers. (`#18 <https://github.com/ipld/py-ipld-dag/issues/18>`__)
