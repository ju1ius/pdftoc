import sys
from typing import Tuple, List

from gi.repository import GObject, GLib, Gtk, Gdk, Gio

from pdftoc.metadata.model import OutlineStore
from .cell_renderers import ActivatableCellRendererText
from.sidebar import TOCSidebar
from.context_menu import TOCContextMenu
from .edit_form import EditForm


class TOCController(GObject.GObject):

    def __init__(self, app, builder):
        super().__init__()
        self.container = builder.get_object('toc_container')
        self.scrolled_window = builder.get_object('toc_scrolledwindow')
        self.view = builder.get_object('toc_treeview')

        self.actions = Gio.SimpleActionGroup()
        self.actions.add_action_entries([
            ('add-row', self._on_action_add_row),
            ('edit-row', self._on_action_edit_row),
            ('create-row', self._on_action_create_row, 's'),
            ('move-row', self._on_action_move_row, 's'),
            ('delete-row', self._on_action_remove_row),
        ])
        self.container.get_toplevel().insert_action_group('toc', self.actions)

        self.sidebar = TOCSidebar(builder, self.actions)

        title_cell = ActivatableCellRendererText()
        column = Gtk.TreeViewColumn('Title', title_cell, text=0)
        column.set_property('expand', True)
        self.view.append_column(column)

        page_cell = ActivatableCellRendererText()
        column = Gtk.TreeViewColumn('Page', page_cell, text=1)
        self.view.append_column(column)

        self.view.connect('row-activated', self._on_row_activated)
        self.view.connect('button-release-event', self._on_button_release_event)
        self.view.connect('popup-menu', self._on_popup_menu)
        self.view.get_selection().connect('changed', self._on_selection_changed)

        self.edit_form = EditForm(builder)
        self.edit_form.connect('submit', self._on_edit_form_submit)

        self.context_menu = TOCContextMenu()
        self.context_menu.attach_to_widget(self.view)

    def get_model(self):
        return self.view.get_model()

    def set_model(self, model):
        self.view.set_model(model)

    model = property(get_model, set_model)

    def _on_action_add_row(self, *args):
        it = self.model.append(None, ('', 1))
        self.start_editing(it)

    def _on_action_edit_row(self, *args):
        model, paths = self._get_selected_rows()
        if paths:
            self.start_editing(model.get_iter(paths[0]))

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
        self.view.set_cursor(path, None, False)
        self.view.grab_focus()
        self.view.row_activated(path, self.view.get_column(col))

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

    def _on_selection_changed(self, selection: Gtk.TreeSelection):
        model, paths = selection.get_selected_rows()
        length = len(paths)
        self.actions.lookup_action('add-row').set_enabled(length == 0)
        self.actions.lookup_action('edit-row').set_enabled(length == 1)
        self.actions.lookup_action('create-row').set_enabled(length == 1)
        self.actions.lookup_action('delete-row').set_enabled(length >= 1)
        self.actions.lookup_action('move-row').set_enabled(length >= 1)

    def _on_row_activated(self, treeview, path, col):
        renderer = col.get_cells()[0]
        coords = renderer.get_activated_cell_coords()
        coords.y += coords.height
        model = self.view.get_model()
        self.edit_form.set_values(model.get_title(path), model.get_page(path))
        self.edit_form.show(coords)

    def _on_edit_form_submit(self, form, title, page):
        model, paths = self._get_selected_rows()
        if paths:
            model.set_title(paths[0], title)
            model.set_page(paths[0], page)

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
        self.context_menu.popup_at_rect(
            self.view.get_bin_window(),
            rect,
            Gdk.Gravity.SOUTH, Gdk.Gravity.NORTH_WEST,
            None
        )

    def _set_selected_paths(self, paths):
        sel = self.view.get_selection()
        sel.unselect_all()
        for path in paths:
            sel.select_path(path)

    def _get_selected_rows(self):
        return self.view.get_selection().get_selected_rows()

    def _get_selected_refs(self) -> Tuple[OutlineStore, List[Gtk.TreeRowReference]]:
        model, selected_paths = self.view.get_selection().get_selected_rows()
        refs = [Gtk.TreeRowReference(model, path) for path in selected_paths]
        return model, refs
