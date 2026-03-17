Multihash Interface Example
===========================

This example focuses on hash function choice and CID outcomes:

- hash the same payload with ``sha2-256``,
- build a CID from the resulting multihash,
- build a second CID using the JS-example-compatible ``sha3-512``-style path,
- compare digest lengths and CID strings to documented JS expected values.

Run it with:

.. code:: bash

    python -m examples.multihash_interface.multihash_interface
    python -m examples.multihash_interface.multihash_interface --json

Expected result:

- printed digest lengths for both hash paths,
- printed CIDs,
- booleans indicating whether output matches the JS reference comments.

.. literalinclude:: ../examples/multihash_interface/multihash_interface.py
    :language: python
    :linenos:
