from typing import Optional, Union, Iterable, Generator

from gi.repository import Gtk

from .types import TreePathType, ModelKeyType


def coerce_path(path: TreePathType) -> Gtk.TreePath:
    if isinstance(path, Gtk.TreePath):
        return path
    return Gtk.TreePath(path)


class TreeStore(Gtk.TreeStore):

    def __str__(self):
        def print_node(model, path, it, buf):
            data = tuple(model[it])
            buf.append(f'{path} => {data}')
        buf = []
        self.foreach(print_node, buf)
        return '\n'.join(buf)

    def descendants(self, key: ModelKeyType = None) -> Generator[Gtk.TreeModelRow, None, None]:
        if not key:
            for row in self:
                yield from self.descendants(row.iter)
        else:
            row: Gtk.TreeModelRow = self[key]
            yield row
            for child in row.iterchildren():
                yield from self.descendants(child.iter)

    def duplicate_row(self, src: Gtk.TreeIter) -> Optional[Gtk.TreeIter]:
        dest = self.insert_after(None, src, self[src][:])
        if dest and self.iter_has_child(src):
            self._copy_descendants(src, dest)
        return dest

    def copy_row(self, src_iter: Gtk.TreeIter, dest_path: TreePathType) -> Optional[Gtk.TreeIter]:
        return self._copy_row(src_iter, coerce_path(dest_path))

    def move_row(self, src_iter: Gtk.TreeIter, dest_path: TreePathType) -> Optional[Gtk.TreeIter]:
        dest_iter = self.copy_row(src_iter, dest_path)
        if dest_iter:
            self.remove(src_iter)
        return dest_iter

    def move_row_up(self, src_iter: Gtk.TreeIter) -> Gtk.TreeIter:
        prev = self.iter_previous(src_iter)
        if prev:
            # simple case, just move the row before its previous sibling
            self.swap(src_iter, prev)
            return src_iter
        # Move the row before its parent
        parent = self.iter_parent(src_iter)
        if not parent:
            return src_iter
        return self.move_row(src_iter, self.get_path(parent))

    def move_row_down(self, src_iter: Gtk.TreeIter) -> Gtk.TreeIter:
        next = self.iter_next(src_iter)
        if next:
            self.swap(src_iter, next)
        return src_iter

    def move_row_left(self, src_iter: Gtk.TreeIter) -> Gtk.TreeIter:
        parent = self.iter_parent(src_iter)
        if not parent:
            return src_iter
        dest_path = self.get_path(parent)
        dest_path.next()
        return self.move_row(src_iter, dest_path)

    def move_row_right(self, src_iter: Gtk.TreeIter) -> Gtk.TreeIter:
        prev = self.iter_previous(src_iter)
        if not prev:
            return src_iter
        dest_path = self.get_path(prev)
        dest_path.append_index(self.iter_n_children(prev))
        return self.move_row(src_iter, dest_path)

    def _copy_row(self, src_iter: Gtk.TreeIter, dest_path: Gtk.TreePath) -> Optional[Gtk.TreeIter]:
        # Logic ported from `gtk_tree_store_drag_data_received()`
        # @see https://github.com/GNOME/gtk/blob/master/gtk/gtktreestore.c
        src_row = self[src_iter]
        dest_iter = None
        # Get the path to insert _after_ (dest_path is the path to insert _before_)
        prev_path = dest_path.copy()
        if not prev_path.prev():
            # dest_path was the first spot at the current depth,
            # which means we are supposed to prepend

            # Get the parent (None if parent is the root)
            parent_iter = None
            parent_path = dest_path.copy()
            if parent_path.up() and parent_path.get_depth() > 0:
                parent_iter = self.get_iter(parent_path)
            dest_iter = self.prepend(parent_iter, src_row[:])
        else:
            try:
                dest_iter = self.get_iter(prev_path)
            except ValueError:
                return
            dest_iter = self.insert_after(None, dest_iter, src_row[:])

        # If we succeeded in creating dest_iter,
        # walk src_iter tree branch, duplicating it below dest_iter.
        if dest_iter and self.iter_has_child(src_iter):
            self._copy_descendants(src_iter, dest_iter)

        return dest_iter

    def _copy_descendants(self, parent_src: Gtk.TreeIter, parent_dest: Gtk.TreeIter):
        """
        Recursively copies descendants of `parent_src` into `parent_dest`
        """
        child_src = self.iter_children(parent_src)
        while child_src:
            child_dest = self.append(parent_dest, self[child_src][:])
            self._copy_descendants(child_src, child_dest)
            child_src = self.iter_next(child_src)
