def node_to_link(node):
    from .dag import Link, Node

    if not isinstance(node, Node):
        raise TypeError('node should be an instance of type Node')

    return Link('', node.size, node.multihash)
