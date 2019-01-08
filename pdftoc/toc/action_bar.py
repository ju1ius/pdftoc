"""
We need this class since glade does not allows to set the action-target property on widgets.
see: https://gitlab.gnome.org/GNOME/glade/issues/330
"""

from gi.repository import GObject, Gtk, Gio


class TOCActionBar(GObject.GObject):

    def __init__(self, actionbar):
        super().__init__()
        self.actionbar = actionbar

        box = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self.actionbar.pack_start(box)

        for prop, action, label, icon in (
            ('add_btn', 'toc.add-row', 'Add', None),
            ('prepend_btn', 'toc.create-row::first-child', 'Prepend Child', None),
            ('append_btn', 'toc.create-row::last-child', 'Append Child', None),
            ('insert_before_btn', 'toc.create-row::previous-sibling', 'Insert Before', None),
            ('insert_after_btn', 'toc.create-row::next-sibling', 'Insert After', None),
            ('delete_btn', 'toc.delete-row', 'Remove', None),
        ):
            btn = self._create_button(action, label=label, icon=icon)
            box.add(btn)
            setattr(self, prop, btn)

        self.delete_btn.get_style_context().add_class('destructive-action')
        box.set_child_secondary(self.delete_btn, True)
        box.set_child_non_homogeneous(self.delete_btn, True)

        box = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self.actionbar.pack_end(box)
        for prop, action, icon in (
            ('move_up_btn', 'toc.move-row::up', 'go-up'),
            ('move_down_btn', 'toc.move-row::down', 'go-down'),
            ('move_left_btn', 'toc.move-row::left', 'go-previous'),
            ('move_right_btn', 'toc.move-row::right', 'go-next'),
        ):
            btn = self._create_button(action, icon=icon)
            box.add(btn)
            setattr(self, prop, btn)

    def toggle_buttons(self, selection_length):
        self.add_btn.set_visible(not selection_length)
        self.append_btn.set_visible(selection_length < 2)
        self.prepend_btn.set_visible(selection_length == 1)
        self.insert_before_btn.set_visible(selection_length == 1)
        self.insert_after_btn.set_visible(selection_length == 1)
        self.delete_btn.set_visible(selection_length > 0)

    def _create_button(self, action, label=None, icon=None, emblem=None):
        btn = Gtk.Button()
        btn.set_detailed_action_name(action)
        if label:
            btn.set_label(label)
        if icon:
            icon = Gio.ThemedIcon.new(icon)
            if emblem:
                emblem = Gio.ThemedIcon.new(emblem)
                icon = Gio.EmblemedIcon.new(icon, Gio.Emblem.new(emblem))
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            btn.set_image(image)
        return btn
