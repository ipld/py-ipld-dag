#!/usr/bin/env python3

import pytest

from dag import dag, utils

TEST_NODE_DATA = "hello!"


@pytest.fixture
def node():
    """
    A Node object fixture
    """
    print('dag: ', dag)
    node = dag.Node.create(TEST_NODE_DATA)

    return node


def test_node_to_link(node):

    link = utils.node_to_link(node)

    # Sanity test
    assert isinstance(link, dag.Link)

    # Ensure correct member transfer
    assert link._size == node.size
    assert link._name == ''
    assert link._multihash == node.multihash
