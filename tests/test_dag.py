#!/usr/bin/env python3
"""Tests for the legacy dag module (backward compatibility)."""

import warnings

import base58
import pytest


def _sample_multihash() -> bytes:
    return base58.b58encode(b"\x12\x20" + b"\x00" * 32)


class LegacyImportTestCase:
    """Verify the legacy dag module still imports."""

    def test_import_node_class(self):
        from dag.dag import Node

        assert Node is not None

    def test_import_link_class(self):
        from dag.dag import Link

        assert Link is not None

    def test_node_emits_deprecation_warning(self):
        from dag.dag import Node

        with pytest.warns(DeprecationWarning, match="Node is deprecated"):
            Node(b"data", [], b"{}", _sample_multihash())

    def test_link_emits_deprecation_warning(self):
        from dag.dag import Link

        with pytest.warns(DeprecationWarning, match="Link is deprecated"):
            Link("name", 1, _sample_multihash())

    def test_node_to_link_emits_deprecation_warning(self):
        from dag.utils import node_to_link

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from dag.dag import Node

            node = Node(b"data", [], b"{}", _sample_multihash())

        with pytest.warns(DeprecationWarning, match="node_to_link"):
            node_to_link(node)
