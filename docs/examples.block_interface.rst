Block Interface Example
=======================

This example demonstrates the core ``Block`` workflow with ``dag-cbor``:

- encode a Python value into block bytes + CID,
- decode block bytes back into a value,
- re-create a block from known pieces (CID + bytes + value),
- verify all resulting CIDs are equivalent.

Run it with:

.. code:: bash

    python -m examples.block_interface.block_interface
    python -m examples.block_interface.block_interface --json

Expected result:

- a printed CID for the encoded block,
- boolean checks confirming decoded/recreated blocks match the original CID.

.. literalinclude:: ../examples/block_interface/block_interface.py
    :language: python
    :linenos:
