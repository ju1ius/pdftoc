import sys

from gi.repository import GObject, Gtk, Gdk


class EditForm(GObject.GObject):

    __gsignals__ = {
        'submit': (GObject.SIGNAL_RUN_FIRST, None, (str, int)),
    }

    def __init__(self, builder):
        super().__init__()
        self.popover = builder.get_object('toc_edit_popover')
        self.popover.connect('key-release-event', self._on_key_press)

        self.title_entry = builder.get_object('toc_edit_title_entry')

        self.page_entry = builder.get_object('toc_edit_page_entry')
        self.page_entry.set_adjustment(Gtk.Adjustment(lower=1, upper=sys.maxsize, step_increment=1))

        self.submit_btn = builder.get_object('toc_edit_submit_btn')
        self.submit_btn.connect('clicked', self._on_submit_btn_clicked)

    def show(self, coords: Gdk.Rectangle):
        self.popover.set_pointing_to(coords)
        self.popover.popup()

    def set_values(self, title, page):
        self.title_entry.set_text(title)
        self.page_entry.set_value(page)

    def submit(self):
        title = self.title_entry.get_text()
        page = self.page_entry.get_value_as_int()
        self.emit('submit', title, page)
        self.popover.popdown()

    def _on_key_press(self, widget, event: Gdk.EventKey):
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.submit()

    def _on_submit_btn_clicked(self, widget, *rest):
        self.submit()
