import sys
from typing import Tuple, List

from gi.repository import GObject, Gtk, Gdk, Gio

from .utils import all_equal


class TOCController:

    def __init__(self, app, builder):
        self.container = builder.get_object('toc_container')
        self.scrolled_window = builder.get_object('toc_scrolledwindow')
        self.view = builder.get_object('toc_treeview')

        actions = [
            ('delete', lambda *x: self.remove(), '<Alt>d'),
            ('append-child', lambda *x: self.append(), '<Alt>j'),
            ('prepend-child', lambda *x: self.prepend(), '<Alt>k'),
            ('insert-before', lambda *x: self.insert_before(), '<Alt>l'),
            ('insert-after', lambda *x: self.insert_after(), '<Alt>h'),
            ('move-up', lambda *x: self.move_up(), '<Alt>KP_8'),
            ('move-down', lambda *x: self.move_down(), '<Alt>KP_2'),
            ('move-left', lambda *x: self.move_left(), '<Alt>KP_4'),
            ('move-right', lambda *x: self.move_right(), '<Alt>KP_6'),
        ]
        group = Gio.SimpleActionGroup()
        group.add_action_entries([(a, b) for a, b, _ in actions])
        self.container.get_toplevel().insert_action_group('toc', group)
        for a, _, c in actions:
            app.set_accels_for_action(f'toc.{a}', [c])

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

    def remove(self):
        model, refs = self._get_selected_refs()
        for ref in refs:
            if not ref.valid():
                continue
            it = model.get_iter(ref.get_path())
            model.remove(it)

    def append(self):
        model, refs = self._get_selected_refs()
        parent, row = None, ('', 1)
        if refs:
            parent = model.get_iter(refs[-1].get_path())
            row = ('', model.get_last_chapter_page(parent))
        it = model.append(parent, row)
        self.start_editing(it)

    def prepend(self):
        model, refs = self._get_selected_refs()
        parent, row = None, ('', 1)
        if refs:
            parent = model.get_iter(refs[0].get_path())
            row = ('', model[parent][model.COLUMN_PAGE])
        it = model.prepend(parent, row)
        self.start_editing(it)

    def insert_before(self):
        model, refs = self._get_selected_refs()
        sibling = model.get_iter(refs[-1].get_path())
        row = ('', model[sibling][model.COLUMN_PAGE])
        it = model.insert_before(None, sibling, row=row)
        self.start_editing(it)

    def insert_after(self):
        model, refs = self._get_selected_refs()
        sibling = model.get_iter(refs[-1].get_path())
        row = ('', model.get_last_chapter_page(sibling))
        it = model.insert_after(None, sibling, row=row)
        self.start_editing(it)

    def start_editing(self, treeiter, col=0):
        path = self.model.get_path(treeiter)
        self.view.expand_to_path(path)
        self.view.grab_focus()
        self.view.set_cursor(path, self.view.get_column(col), True)

    def move_up(self):
        model, refs = self._get_selected_refs()
        if not refs:
            return
        if not all_equal(r.get_path().get_depth() for r in refs):
            return
        it = model.get_iter(refs[0].get_path())
        prev = model.iter_previous(it)
        if not prev:
            return
        for ref in refs:
            it = model.get_iter(ref.get_path())
            model.move_before(it, model.iter_previous(it))

    def move_down(self):
        model, refs = self._get_selected_refs()
        if not refs:
            return
        if not all_equal(r.get_path().get_depth() for r in refs):
            return
        it = model.get_iter(refs[-1].get_path())
        next = model.iter_next(it)
        if not next:
            return
        for ref in reversed(refs):
            it = model.get_iter(ref.get_path())
            model.move_after(it, model.iter_next(it))

    def move_left(self):
        model, refs = self._get_selected_refs()
        if not refs:
            return
        if not all_equal(r.get_path().get_depth() for r in refs):
            return
        for ref in refs:
            row = model[ref.get_path()][:]
            it = model.get_iter(ref.get_path())
            parent = model.iter_parent(it)
            if not parent:
                continue
            model.remove(it)
            model.insert_after(None, parent, row=row)

    def move_right(self):
        model, refs = self._get_selected_refs()
        if not refs:
            return
        if not all_equal(r.get_path().get_depth() for r in refs):
            return
        it = model.get_iter(self._get_deepest_path(refs))
        next = model.iter_

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

    def _on_selection_changed(self, selection):
        num_rows = selection.count_selected_rows()
        self.actionbar.toggle_buttons(num_rows)

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

    def _get_selected_paths(self) -> Tuple[Gtk.TreeStore, List[Gtk.TreePath]]:
        return self.view.get_selection().get_selected_rows()

    def _get_selected_refs(self) -> Tuple[Gtk.TreeStore, List[Gtk.TreeRowReference]]:
        model, selected_paths = self.view.get_selection().get_selected_rows()
        refs = [Gtk.TreeRowReference(model, path) for path in selected_paths]
        return model, refs

    def _get_deepest_path(self, refs, reverse=False):
        refs = sorted(refs, key=lambda r: r.get_path().get_depth(), reverse=reverse)
        return refs[-1]


class TOCActionBar(GObject.GObject):

    def __init__(self, actionbar):
        super().__init__()
        self.actionbar = actionbar

        box = Gtk.HButtonBox()
        box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self.actionbar.pack_start(box)

        self.append_btn = Gtk.Button(label='Append Child', action_name='toc.append-child')
        box.add(self.append_btn)

        self.prepend_btn = Gtk.Button(label='Prepend Child', action_name='toc.prepend-child')
        box.add(self.prepend_btn)

        self.insert_before_btn = Gtk.Button(label='Insert Before', action_name='toc.insert-before')
        box.add(self.insert_before_btn)

        self.insert_after_btn = Gtk.Button(label='Insert After', action_name='toc.insert-after')
        box.add(self.insert_after_btn)

        self.delete_btn = Gtk.Button(label='Remove', action_name='toc.delete')
        self.delete_btn.get_style_context().add_class('destructive-action')
        box.add(self.delete_btn)
        box.set_child_secondary(self.delete_btn, True)
        box.set_child_non_homogeneous(self.delete_btn, True)

    def toggle_buttons(self, selection_length):
        self.append_btn.set_label('Add Child' if not selection_length else 'Append Child')
        self.append_btn.set_visible(selection_length < 2)
        self.prepend_btn.set_visible(selection_length == 1)
        self.insert_before_btn.set_visible(selection_length == 1)
        self.insert_after_btn.set_visible(selection_length == 1)
        self.delete_btn.set_visible(selection_length > 0)


class TOCContextMenu(Gtk.Menu):

    def __init__(self):
        super().__init__()

        self.move_up_item = Gtk.MenuItem(label='Move Up', action_name='toc.move-up')
        self.append(self.move_up_item)
        self.move_down_item = Gtk.MenuItem(label='Move Down', action_name='toc.move-down')
        self.append(self.move_down_item)
        self.move_left_item = Gtk.MenuItem(label='Move left', action_name='toc.move-left')
        self.append(self.move_left_item)
        self.move_right_item = Gtk.MenuItem(label='Move right', action_name='toc.move-right')
        self.append(self.move_right_item)

        self.append(Gtk.SeparatorMenuItem())

        self.append_item = Gtk.MenuItem(label='Append Child', action_name='toc.append-child')
        self.append(self.append_item)
        self.prepend_item = Gtk.MenuItem(label='Prepend Child', action_name='toc.prepend-child')
        self.append(self.prepend_item)
        self.insert_before_item = Gtk.MenuItem(label='Insert Before', action_name='toc.insert-before')
        self.append(self.insert_before_item)
        self.insert_after_item = Gtk.MenuItem(label='Insert After', action_name='toc.insert-after')
        self.append(self.insert_after_item)

        self.append(Gtk.SeparatorMenuItem())

        self.delete_item = Gtk.MenuItem(label='Remove', action_name='toc.delete')
        self.delete_item.get_style_context().add_class('destructive-action')
        self.append(self.delete_item)

    def toggle_items(self, selection_length):
        has_selection = selection_length > 0
        is_single = selection_length == 1

        self.append_item.set_label('Append Child' if has_selection else 'Add Child')
        self.append_item.set_visible(selection_length < 2)
        self.prepend_item.set_visible(is_single)
        self.insert_before_item.set_visible(is_single)
        self.insert_after_item.set_visible(is_single)

        self.delete_item.set_visible(has_selection)

        self.move_up_item.set_visible(has_selection)
        self.move_down_item.set_visible(has_selection)
        self.move_left_item.set_visible(has_selection)
        self.move_right_item.set_visible(has_selection)
