from typing import List

import gi
gi.require_version('Gtk', '3.0')

from pdftoc.toc.tree_store import TreeStore


class Node:
    def __init__(self, text: str, children: List['Node'] = None):
        self.text = text
        self.children = children or []

    def __iter__(self):
        return iter(self.children)

    def __eq__(self, other):
        return self.text == other.text and self.children == other.children

    def append(self, node):
        self.children.append(node)


N = Node


def populate_store(node: Node, store: TreeStore, parent=None):
    for child in node.children:
        it = store.append(parent, row=(child.text,))
        if child.children:
            populate_store(child, store, it)


def create_store(node: Node) -> TreeStore:
    store = TreeStore(str)
    populate_store(node, store)
    return store


def get_node(store: TreeStore, parent_iter=None, parent_node=None) -> Node:
    if not parent_node:
        parent_node = Node('')
    it = store.iter_children(parent_iter)
    while it:
        child = Node(store[it][0])
        parent_node.children.append(child)
        get_node(store, it, child)
        it = store.iter_next(it)
    return parent_node


def print_node(node, depth=0):
    buf = []
    if depth:
        buf.append(f'{"--" * depth} {node.text}')
    for child in node:
        buf.append(print_node(child, depth + 1))
    return '\n'.join(buf)


def test_node_equal():
    assert N('0') == N('0')
    assert N('0') != N('1')
    assert N('0', [N('0.0')]) == N('0', [N('0.0')])
    assert N('0', [N('0.0')]) != N('0', [N('foo')])
    assert N('0', [N('0.0', [N('0.0.0')])]) == N('0', [N('0.0', [N('0.0.0')])])
    assert N('0', [N('0.0', [N('0.0.0')])]) != N('0', [N('0.0', [N('bar')])])


def test_copy_row_copies_shallow_rows():
    store = create_store(N('', [
        N('0'),
    ]))
    it = store.copy_row(store.get_iter('0'), '1')
    assert get_node(store) == N('', [
        N('0'),
        N('0'),
    ])
    assert str(store.get_path(it)) == '1'


def test_copy_row_copies_deep_rows():
    store = create_store(N('', [
        N('0', [
            N('0.0', [N('0.0.0')]),
        ])
    ]))
    it = store.copy_row(store.get_iter('0'), '1')
    assert get_node(store) == N('', [
        N('0', [
            N('0.0', [N('0.0.0')]),
        ]),
        N('0', [
            N('0.0', [N('0.0.0')]),
        ])
    ])
    assert str(store.get_path(it)) == '1'


def test_move_row_moves_shallow_rows():
    store = create_store(N('', [
        N('0'),
        N('1'),
    ]))
    it = store.move_row(store.get_iter('0'), '2')
    assert get_node(store) == N('', [
        N('1'),
        N('0'),
    ])
    assert str(store.get_path(it)) == '1'


def test_move_row_moves_deep_rows():
    store = create_store(N('', [
        N('0', [
            N('0.0', [
                N('0.0.0', [
                    N('0.0.1')
                ])
            ])
        ]),
        N('1'),
    ]))
    it = store.move_row(store.get_iter('0'), '2')
    assert get_node(store) == N('', [
        N('1'),
        N('0', [
            N('0.0', [
                N('0.0.0', [
                    N('0.0.1')
                ])
            ])
        ]),
    ])
    assert str(store.get_path(it)) == '1'


def test_move_row_up_same_depth():
    store = create_store(N('', [
        N('0', [
            N('0.0'),
            N('0.1'),
            N('0.2', [N('0.2.0')]),
        ]),
    ]))
    it = store.move_row_up(store.get_iter('0:2'))
    assert get_node(store) == N('', [
        N('0', [
            N('0.0'),
            N('0.2', [N('0.2.0')]),
            N('0.1'),
        ]),
    ])
    assert str(store.get_path(it)) == '0:1'


def test_move_row_up_cross_depth():
    store = create_store(N('', [
        N('0'),
        N('1', [
            N('1.0')
        ])
    ]))
    it = store.move_row_up(store.get_iter('1:0'))
    assert get_node(store) == N('', [
        N('0'),
        N('1.0'),
        N('1'),
    ])
    assert str(store.get_path(it)) == '1'


def test_move_row_down_same_depth():
    store = create_store(N('', [
        N('0', [
            N('0.0'),
            N('0.1', [N('0.1.0')]),
            N('0.2'),
        ]),
    ]))
    it = store.move_row_down(store.get_iter('0:1'))
    assert get_node(store) == N('', [
        N('0', [
            N('0.0'),
            N('0.2'),
            N('0.1', [N('0.1.0')]),
        ]),
    ])
    assert str(store.get_path(it)) == '0:2'
