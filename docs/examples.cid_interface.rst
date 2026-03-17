CID Interface Example
=====================

This example shows common CID operations for JSON-encoded content:

- create a CIDv1 from deterministic JSON bytes,
- encode CID strings in base32 and base64,
- parse CIDs back from strings,
- round-trip CID bytes back to a CID object,
- compare outputs against values documented in the JS reference example.

Run it with:

.. code:: bash

    python -m examples.cid_interface.cid_interface
    python -m examples.cid_interface.cid_interface --json

Expected result:

- printed CID string/codec/version information,
- booleans showing string/bytes round-trips are equivalent to the original CID.

.. literalinclude:: ../examples/cid_interface/cid_interface.py
    :language: python
    :linenos:
