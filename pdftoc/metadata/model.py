import sys
from collections import deque

from gi.repository import GObject, Gtk


class Document(GObject.GObject):

    num_pages = GObject.property(type=int, default=1)
    title = GObject.property(type=str, default='')
    subject = GObject.property(type=str, default='')
    author = GObject.property(type=str, default='')
    creator = GObject.property(type=str, default='')
    creation_date = GObject.property(type=object, default=None)

    def __init__(self, path=None):
        super().__init__()
        self.path = path
        self.bookmarks = BookmarkStore()
        self.page_medias = []
        # Read-only values
        self.modification_date = None
        self.producer = None
        # Unknown key-value pairs
        self.infos = {}
        # Unknown lines
        self.unknown = []


class BookmarkStore(Gtk.TreeStore):

    (
        COLUMN_TITLE,
        COLUMN_PAGE
    ) = range(2)

    COLUMNS = (str, int)

    def __init__(self):
        super().__init__(*self.COLUMNS)

    def get_last_chapter_page(self, it):
        last_page = self[it][self.COLUMN_PAGE]
        it = self.iter_children(it)
        while it is not None:
            page = self.get_last_chapter_page(it)
            if page > last_page:
                last_page = page
            it = self.iter_next(it)
        return last_page
