from typing import Union, Iterable

from gi.repository import Gtk


TreePathType = Union[
    Gtk.TreePath,
    str,
    Iterable[int]
]

ModelKeyType = Union[
    TreePathType,
    Gtk.TreeIter,
    int
]