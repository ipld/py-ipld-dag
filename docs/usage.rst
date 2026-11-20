=====
Usage
=====

To use py-ipld-dag in a project::

    from dag import Block
    from dag.codecs import dag_cbor

    block = Block.encode(value={"hello": "world"}, codec=dag_cbor.codec)
    restored = Block.decode(data=block.bytes, codec=dag_cbor.codec)
    assert restored.value == {"hello": "world"}

Codecs also support stream-shaped I/O (similar call sites to go-ipld-prime
``Encoder`` / ``Decoder``)::

    import io
    from dag.codecs import dag_cbor

    buf = io.BytesIO()
    dag_cbor.codec.encode_to_stream({"hello": "world"}, buf)
    value = dag_cbor.codec.decode_from_stream(io.BytesIO(buf.getvalue()))
    assert value == {"hello": "world"}

The decoded/encoded IPLD value is still fully materialized in memory; stream
methods target the wire path (``BinaryIO``) rather than constant-memory graphs.
