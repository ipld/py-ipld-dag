=====
Usage
=====

To use py-ipld-dag in a project::

    from dag import Block
    from dag.codecs import dag_cbor

    block = Block.encode(value={"hello": "world"}, codec=dag_cbor.codec)
    restored = Block.decode(data=block.bytes, codec=dag_cbor.codec)
    assert restored.value == {"hello": "world"}
