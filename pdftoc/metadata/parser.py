import re
import datetime
from typing import Optional, Iterable, Tuple

from .model import Document
from ..utils import local_timezone


PDFTK_DATE_RE = re.compile(r'''
^
    D:
    (?P<year>  \d{4})
    (?P<month> \d{2})
    (?P<day>   \d{2})
    (?P<hour>  \d{2})
    (?P<min>   \d{2})
    (?P<sec>   \d{2})
    (?:
        (?P<tzh> [+-]\d{2}) '(?P<tzm> \d{2})'
        | Z
    )?
$
''', re.X)

INFO_KEYS = {
    'Title': 'title',
    'Subject': 'subject',
    'Author': 'author',
    'Creator': 'creator',
    'Producer': 'producer',
    'CreationDate': 'creation_date',
    'ModDate': 'modification_date',
}

VALID_KEYS = {
    'bookmark': ('BookmarkTitle', 'BookmarkPageNumber', 'BookmarkLevel'),
    'page_media': ('PageMediaNumber', 'PageMediaRotation', 'PageMediaRect', 'PageMediaDimensions'),
}


class ParseError(Exception):
    pass


class EOF(Exception):
    pass


class BookmarkParsingState:
    def __init__(self):
        self.previous = None
        self.stack = []


class Parser:

    def __init__(self):
        self.lines: list = []
        self.curline: int = -1
        self.num_lines: int = 0

    def parse(self, text: str, doc: Document) -> Document:
        self.lines = text.splitlines()
        self.curline = -1
        self.num_lines = len(self.lines)
        state = BookmarkParsingState()

        while True:
            try:
                line = self._next()
            except EOF:
                break
            if line.startswith('NumberOfPages'):
                k, v = self._split_pair(line)
                doc.num_pages = int(v)
            elif line == 'InfoBegin':
                self._parse_info(doc)
            elif line == 'BookmarkBegin':
                self._parse_bookmark(doc, state)
            elif line == 'PageMediaBegin':
                self._parse_page_media(doc)
            else:
                doc.unknown.append(line)

        return doc

    def _parse_info(self, doc: Document):
        key = self._next_value('InfoKey')
        value = self._next_value('InfoValue')
        if key in INFO_KEYS:
            setattr(doc, INFO_KEYS[key], self._parse_info_value(value))
        else:
            doc.infos[key] = value

    def _parse_bookmark(self, doc: Document, state: BookmarkParsingState):
        stack, prev = state.stack, state.previous
        parent, title, page, level = None, None, None, None
        while True:
            try:
                k, v = self._next_pair(VALID_KEYS['bookmark'])
            except EOF:
                break
            except ParseError:
                self._recede()
                break
            if k == 'BookmarkTitle':
                title = v
            elif k == 'BookmarkPageNumber':
                page = int(v)
            elif k == 'BookmarkLevel':
                level = int(v)
        if not title or not page or not level:
            raise ParseError('Invalid Bookmark')
        if not prev:
            pass
        elif level > prev['level']:
            # previous bookmark is the parent
            stack.append(prev['iter'])
        elif level < prev['level']:
            # rewind the stack to the right level
            for n in range(level, prev['level']):
                stack.pop()
        if level > 1:
            # level is 1-indexed
            parent = stack[level - 1 - 1]
        it = doc.bookmarks.append(parent, row=(title, page))
        state.previous = {'iter': it, 'level': level}

    def _parse_page_media(self, doc: Document):
        media = {}
        while True:
            try:
                k, v = self._next_pair(VALID_KEYS['page_media'])
            except EOF:
                break
            except ParseError:
                self._recede()
                break
            k = k.replace('PageMedia', '').lower()
            media[k] = v
        doc.page_medias.append(media)

    def _advance(self, n: int = 1):
        self.curline += n

    def _recede(self, n: int = 1):
        self.curline -= n

    def _current(self) -> str:
        try:
            return self.lines[self.curline]
        except IndexError:
            raise EOF()

    def _next(self) -> str:
        self._advance()
        return self._current()

    def _next_pair(self, valid_keys: Optional[Iterable[str]] = None) -> Tuple[str, str]:
        line = self._next()
        k, v = self._split_pair(line)
        if valid_keys and k not in valid_keys:
            expected = ', '.join(valid_keys)
            raise ParseError('Expected <{}> but got <{}>'.format(expected, k))
        return k, v

    def _next_value(self, valid_key: str) -> str:
        k, v = self._next_pair(valid_keys=(valid_key,))
        return v

    def _split_pair(self, string: str) -> Tuple[str, str]:
        try:
            k, v = string.split(':', 1)
            return k.strip(), v.strip()
        except ValueError:
            raise ParseError('Expected key-value pair, got <{}>'.format(string))

    def _parse_info_value(self, value: str):
        m = PDFTK_DATE_RE.match(value)
        if m:
            tz = local_timezone()
            if m.group('tzh'):
                hours = int(m.group('tzh'))
                minutes = int(m.group('tzm'))
                tz = datetime.timezone(datetime.timedelta(hours=hours, minutes=minutes))
            return datetime.datetime(
                int(m.group('year')),
                int(m.group('month')),
                int(m.group('day')),
                hour=int(m.group('hour')),
                minute=int(m.group('min')),
                second=int(m.group('sec')),
                tzinfo=tz
            )

        return value
