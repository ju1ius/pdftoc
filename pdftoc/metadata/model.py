from typing import Optional, List, Dict

from gi.repository import GObject, Gtk

from pdftoc.toc.types import ModelKeyType
from pdftoc.toc.tree_store import TreeStore


class Document(GObject.GObject):

    num_pages: int = GObject.property(type=int, default=1)
    title: str = GObject.property(type=str, default='')
    subject: str = GObject.property(type=str, default='')
    author: str = GObject.property(type=str, default='')
    creator: str = GObject.property(type=str, default='')
    creation_date = GObject.property(type=object, default=None)

    def __init__(self, path: Optional[str] = None):
        super().__init__()
        self.path = path
        self.bookmarks: BookmarkStore = BookmarkStore()
        self.page_medias = []
        # Read-only values
        self.modification_date = None
        self.producer = None
        # Unknown key-value pairs
        self.infos: Dict[str, str] = {}
        # Unknown lines
        self.unknown: List[str] = []


class BookmarkStore(TreeStore):

    (
        COLUMN_TITLE,
        COLUMN_PAGE
    ) = range(2)

    COLUMNS = (str, int)

    def __init__(self):
        super().__init__(*self.COLUMNS)

    def get_title(self, key: ModelKeyType):
        return self[key][self.COLUMN_TITLE]

    def get_page(self, key: ModelKeyType):
        return self[key][self.COLUMN_PAGE]

    def get_last_chapter_page(self, key: ModelKeyType) -> int:
        return max(row[self.COLUMN_PAGE] for row in self.descendants(key))
