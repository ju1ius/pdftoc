import sys

from gi.repository import GObject, Gtk, Gdk, Gio


class TOCActions(Gio.SimpleActionGroup):

    def __init__(self):
        super().__init__()
        for name in ('delete', 'append-child', 'prepend-child', 'insert-after', 'insert-before'):
            action = Gio.SimpleAction.new(name, None)
            self.add_action(action)
            setattr(self, name.replace('-', '_'), action)


class TOCController:

    def __init__(self, builder):
        self.container = builder.get_object('toc_container')
        self.scrolled_window = builder.get_object('toc_scrolledwindow')
        self.view = builder.get_object('toc_treeview')

        self.actions = TOCActions()
        self.actions.delete.connect('activate', lambda *x: self.remove())
        self.actions.append_child.connect('activate', lambda *x: self.append())
        self.actions.prepend_child.connect('activate', lambda *x: self.prepend())
        self.actions.insert_before.connect('activate', lambda *x: self.insert_before())
        self.actions.insert_after.connect('activate', lambda *x: self.insert_after())

        self.container.insert_action_group('toc', self.actions)

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
            parent = model.get_iter(refs[-1].get_path())
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

    def _get_selected_refs(self):
        model, selected_paths = self.view.get_selection().get_selected_rows()
        refs = [Gtk.TreeRowReference(model, path) for path in selected_paths]
        return model, refs


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
        self.append_item.set_label('Add Child' if not selection_length else 'Append Child')
        self.append_item.set_visible(selection_length < 2)
        self.prepend_item.set_visible(selection_length == 1)
        self.insert_before_item.set_visible(selection_length == 1)
        self.insert_after_item.set_visible(selection_length == 1)
        self.delete_item.set_visible(selection_length > 0)
