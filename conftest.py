from pdftoc.toc.tree_store_test import Node, print_node


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Node) and isinstance(right, Node) and op == "==":
        return [
            'Node instances are equal:',
            '>>>>>',
            *(print_node(left).splitlines()),
            '<<<<<',
            *(print_node(right).splitlines()),
        ]
