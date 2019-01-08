"""
We need this class since glade does not allows to set the action-target property on widgets.
see: https://gitlab.gnome.org/GNOME/glade/issues/330
"""
from gi.repository import Gtk


class TOCContextMenu(Gtk.Menu):

    def __init__(self):
        super().__init__()

        for prop, label, action in (
            ('move_up_item', 'Move Up', 'toc.move-row::up'),
            ('move_down_item', 'Move Down', 'toc.move-row::down'),
            ('move_left_item', 'Move Left', 'toc.move-row::left'),
            ('move_right_item', 'Move Right', 'toc.move-row::right'),
            (None, None, None),
            ('add_item', 'Add', 'toc.add-row'),
            ('prepend_item', 'Prepend Child', 'toc.create-row::first-child'),
            ('append_item', 'Append Child', 'toc.create-row::last-child'),
            ('insert_before_item', 'Insert Before', 'toc.create-row::previous-sibling'),
            ('insert_after_item', 'Insert After', 'toc.create-row::next-sibling'),
            (None, None, None),
            ('delete_item', 'Remove', 'toc.delete-row')
        ):
            if not prop:
                self.append(Gtk.SeparatorMenuItem())
                continue
            item = Gtk.MenuItem(label=label)
            item.set_detailed_action_name(action)
            self.append(item)
            setattr(self, prop, item)

        self.delete_item.get_style_context().add_class('destructive-action')

    def toggle_items(self, selection_length):
        has_selection = selection_length > 0
        is_single = selection_length == 1

        self.add_item.set_visible(not has_selection)
        self.append_item.set_visible(is_single)
        self.prepend_item.set_visible(is_single)
        self.insert_before_item.set_visible(is_single)
        self.insert_after_item.set_visible(is_single)

        self.delete_item.set_visible(has_selection)

        self.move_up_item.set_visible(has_selection)
        self.move_down_item.set_visible(has_selection)
        self.move_left_item.set_visible(has_selection)
        self.move_right_item.set_visible(has_selection)
