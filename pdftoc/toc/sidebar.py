from gi.repository import GObject, Gio, Gtk


class TOCSidebar:

    def __init__(self, builder: Gtk.Builder, actions: Gio.ActionMap):
        edit_box = builder.get_object('toc_edit_button_box')
        edit_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        add_box = builder.get_object('toc_add_button_box')
        add_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        move_box = builder.get_object('toc_move_button_box')
        move_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        view_box = builder.get_object('toc_view_button_box')
        view_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)

        for prop, action, icon, css in (
            ('add_btn', 'toc.add-row', 'add-symbolic', 'suggested-action'),
            ('edit_btn', 'toc.edit-row', 'document-edit-symbolic', 'suggested-action'),
            ('delete_btn', 'toc.delete-row', 'user-trash-symbolic', 'destructive-action'),
        ):
            btn = self._create_button(prop, edit_box, action, icon=icon, css_class=css)

        for prop, action, icon in (
            ('insert_before_btn', 'toc.create-row::previous-sibling', 'go-up-symbolic'),
            ('insert_after_btn', 'toc.create-row::next-sibling', 'go-down-symbolic'),
            ('prepend_btn', 'toc.create-row::first-child', 'go-up-symbolic'),
            ('append_btn', 'toc.create-row::last-child', 'go-down-symbolic'),
        ):
            btn = self._create_button(prop, add_box, action, icon=icon)

        for prop, action, icon in (
            ('move_up_btn', 'toc.move-row::up', 'go-up-symbolic'),
            ('move_down_btn', 'toc.move-row::down', 'go-down-symbolic'),
            ('move_left_btn', 'toc.move-row::left', 'format-indent-less-symbolic'),
            ('move_right_btn', 'toc.move-row::right', 'format-indent-more-symbolic'),
        ):
            btn = self._create_button(prop, move_box, action, icon=icon)

        add_row = actions.lookup_action('add-row')
        add_row.bind_property('enabled', self.add_btn, 'visible', GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE)
        edit_row = actions.lookup_action('edit-row')
        edit_row.bind_property('enabled', self.edit_btn, 'visible', GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE)

    def _create_button(self, prop, to, action, label=None, icon=None, emblem=None, css_class=None):
        btn = Gtk.Button()
        btn.set_detailed_action_name(action)
        if label:
            btn.set_label(label)
        if css_class:
            btn.get_style_context().add_class(css_class)
        if icon:
            icon = Gio.ThemedIcon.new(icon)
            if emblem:
                emblem = Gio.ThemedIcon.new(emblem)
                icon = Gio.EmblemedIcon.new(icon, Gio.Emblem.new(emblem))
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            btn.set_image(image)

        btn.set_name(f'toc_{prop}')
        to.add(btn)
        setattr(self, prop, btn)
        return btn
