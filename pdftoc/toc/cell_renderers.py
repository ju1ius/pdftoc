from gi.repository import GObject, Gtk, Gdk


class ActivatableCellRendererText(Gtk.CellRendererText):
    """
    Activatable CellRenderer that tracks the coordinates of the activated cell
    """

    def __init__(self):
        super().__init__()
        self.set_property('mode', Gtk.CellRendererMode.ACTIVATABLE)
        self._activated_cell_coords = Gdk.Rectangle()

    def get_activated_cell_coords(self) -> Gdk.Rectangle:
        return self._activated_cell_coords

    def do_activate(
        self,
        event: Gdk.Event,
        widget: Gtk.TreeView,
        path: str,
        background_area: Gdk.Rectangle,
        cell_area: Gdk.Rectangle,
        flags: Gtk.CellRendererState
    ):
        self._activated_cell_coords = background_area
