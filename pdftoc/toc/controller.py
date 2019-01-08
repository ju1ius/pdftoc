import sys
from typing import Tuple, List

from gi.repository import GObject, GLib, Gtk, Gdk, Gio

from pdftoc.metadata.model import BookmarkStore
from.action_bar import TOCActionBar
from.context_menu import TOCContextMenu


class TOCController(GObject.GObject):

    def __init__(self, app, builder):
        super().__init__()
        self.container = builder.get_object('toc_container')
        self.scrolled_window = builder.get_object('toc_scrolledwindow')
        self.view = builder.get_object('toc_treeview')

        self.actions = Gio.SimpleActionGroup()
        self.actions.add_action_entries([
            ('add-row', self._on_action_add_row),
            ('create-row', self._on_action_create_row, 's'),
            ('move-row', self._on_action_move_row, 's'),
            ('delete-row', self._on_action_remove_row),
        ])
        self.container.get_toplevel().insert_action_group('toc', self.actions)

        self.actionbar = TOCActionBar(builder.get_object('toc_actionbar'))
        self.context_menu = TOCContextMenu()
        self.context_menu.attach_to_widget(self.view)

        title_cell = Gtk.CellRendererText()
        title_cell.set_property('editable', True)
        title_cell.connect('edited', self._on_title_cell_edited)
        column = Gtk.TreeViewColumn('Title', title_cell, text=0)
        column.set_property('expand', True)
        self.view.append_column(column)

        page_cell = Gtk.CellRendererSpin()
        page_cell.set_property('adjustment', Gtk.Adjustment(lower=0, upper=sys.maxsize, step_increment=1))
        page_cell.set_property('editable', True)
        page_cell.connect('editing-started', self._on_page_cell_editing_started)
        page_cell.connect('edited', self._on_page_cell_edited)
        column = Gtk.TreeViewColumn('Page', page_cell, text=1)
        self.view.append_column(column)

        self.view.connect('button-release-event', self._on_button_release_event)
        self.view.connect('popup-menu', self._on_popup_menu)
        self.view.get_selection().connect('changed', self._on_selection_changed)

    def get_model(self):
        return self.view.get_model()

    def set_model(self, model):
        self.view.set_model(model)

    model = property(get_model, set_model)

    def _on_action_add_row(self):
        self.model.append(None, ('', 1))

    def _on_action_remove_row(self, action: Gio.Action, param: GLib.Variant, arg):
        model, refs = self._get_selected_refs()
        for ref in refs:
            if not ref.valid():
                continue
            it = model.get_iter(ref.get_path())
            model.remove(it)

    def _on_action_create_row(self, action: Gio.Action, param: GLib.Variant, arg):
        where = param.get_string()
        model, refs = self._get_selected_refs()
        selected_iter = model.get_iter(refs[0].get_path())
        if where == 'first-child':
            row = ('', model.get_page(selected_iter))
            it = model.prepend(selected_iter, row)
        elif where == 'last-child':
            row = ('', model.get_last_chapter_page(selected_iter))
            it = model.append(selected_iter, row)
        elif where == 'previous-sibling':
            row = ('', model.get_page(selected_iter))
            it = model.insert_before(None, selected_iter, row)
        elif where == 'next-sibling':
            row = ('', model.get_last_chapter_page(selected_iter))
            it = model.insert_after(None, selected_iter, row)
        else:
            raise ValueError(where)
        self.start_editing(it)

    def start_editing(self, treeiter, col=0):
        path = self.model.get_path(treeiter)
        self.view.expand_to_path(path)
        self.view.grab_focus()
        self.view.set_cursor(path, self.view.get_column(col), True)

    def _on_action_move_row(self, action: Gio.Action, param: GLib.Variant, *args):
        model, refs = self._get_selected_refs()
        if not refs:
            return
        move_row = getattr(model, f'move_row_{param.get_string()}')
        paths = []
        for ref in refs:
            it = move_row(model.get_iter(ref.get_path()))
            paths.append(model.get_path(it))
        self._set_selected_paths(paths)

    def _on_page_cell_editing_started(self, renderer, widget, path, data=None):
        widget.set_numeric(True)

    def _on_page_cell_edited(self, widget, path, value):
        try:
            value = int(value)
        except ValueError:
            return
        self.model[path][1] = value

    def _on_title_cell_edited(self, widget, path, value):
        value = value.strip()
        if not value:
            return
        self.model[path][0] = value

    def _on_selection_changed(self, selection: Gtk.TreeSelection):
        model, paths = selection.get_selected_rows()
        length = len(paths)
        self.actions.lookup_action('add-row').set_enabled(length == 0)
        self.actions.lookup_action('delete-row').set_enabled(length >= 1)
        self.actions.lookup_action('create-row').set_enabled(length == 1)
        self.actions.lookup_action('move-row').set_enabled(length >= 1)

    def _on_button_release_event(self, treeview, event):
        if event.button == 3:
            # right click on a row: show a context menu
            self._show_row_context_menu(event)

    def _on_popup_menu(self, treeview, user_data=None):
        self._show_row_context_menu()

    def _show_row_context_menu(self, event=None):
        sel = self.view.get_selection()
        num_selected = sel.count_selected_rows()
        self.context_menu.toggle_items(num_selected)
        if event:
            self.context_menu.popup_at_pointer(event)
            return
        if not num_selected:
            self.context_menu.popup_at_widget(self.view)
            return
        model, selected_paths = sel.get_selected_rows()
        rect = self.view.get_cell_area(selected_paths[0])
        #TODO: coords are wrong when scrolled
        self.context_menu.popup_at_rect(
            self.view.get_bin_window(),
            rect,
            Gdk.Gravity.SOUTH, Gdk.Gravity.NORTH_WEST,
            None
        )

    def _get_selected_paths(self) -> List[Gtk.TreePath]:
        _, paths = self.view.get_selection().get_selected_rows()
        return paths

    def _set_selected_paths(self, paths):
        sel = self.view.get_selection()
        sel.unselect_all()
        for path in paths:
            sel.select_path(path)

    def _get_selected_refs(self) -> Tuple[BookmarkStore, List[Gtk.TreeRowReference]]:
        model, selected_paths = self.view.get_selection().get_selected_rows()
        refs = [Gtk.TreeRowReference(model, path) for path in selected_paths]
        return model, refs

    def _get_deepest_path(self, refs, reverse=False):
        refs = sorted(refs, key=lambda r: r.get_path().get_depth(), reverse=reverse)
        return refs[-1]
