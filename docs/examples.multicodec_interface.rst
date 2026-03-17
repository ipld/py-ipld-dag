Multicodec Interface Example
============================

This example demonstrates custom codec registration and lookup:

- define a ``BlockCodec`` implementation (``JsonCodec``),
- register it in the codec registry,
- look it up by name,
- use it with ``Block.encode`` and ``Block.decode`` for round-trip verification.

Run it with:

.. code:: bash

    python -m examples.multicodec_interface.multicodec_interface

Expected result:

- the registered codec name/code is printed,
- a block CID is produced,
- a final boolean confirms decoded value equals the input value.

.. literalinclude:: ../examples/multicodec_interface/multicodec_interface.py
    :language: python
    :linenos:
