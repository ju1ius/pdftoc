import datetime

class Serializer:

    def serialize(self, doc):
        out = []
        out.append('NumberOfPages: {}'.format(doc.num_pages))
        if doc.title:
            out.append(self._serialize_info('Title', doc.title))
        if doc.subject:
            out.append(self._serialize_info('Subject', doc.subject))
        if doc.author:
            out.append(self._serialize_info('Author', doc.author))
        if doc.creation_date:
            out.append(self._serialize_info('CreationDate', doc.creation_date))
        if doc.modification_date:
            out.append(self._serialize_info('ModDate', doc.modification_date))
        if doc.producer:
            out.append(self._serialize_info('Producer', doc.producer))

        out.append(self._serialize_bookmarks(doc.bookmarks))

        # for pm in doc.page_medias:
            # out.append(self._serialize_page_media(pm))

        out.extend(doc.unknown)

        return "\n".join(out)

    def _serialize_info(self, k, v):
        if isinstance(v, datetime.datetime):
            v = v.strftime('D:%Y%m%d%H%M%S')
            #TODO: timezone
        return (
            "InfoBegin\n"
            "InfoKey: {}\n"
            "InfoValue: {}"
        ).format(k, v)

    def _serialize_bookmarks(self, store, it=None, level=1):
        if not it:
            it = store.get_iter_first()
            level = 1
        out = []
        while it is not None:
            title, page = store[it][:]
            out.append((
                "BookmarkBegin\n"
                "BookmarkTitle: {}\n"
                "BookmarkPageNumber: {}\n"
                "BookmarkLevel: {}"
            ).format(title, page, level))
            if store.iter_has_child(it):
                child_it = store.iter_children(it)
                children = self._serialize_bookmarks(store, child_it, level + 1)
                out.append(children)
            it = store.iter_next(it)
        return "\n".join(out)

    def _serialize_page_media(self, pm):
        out = ['PageMediaBegin']
        for k, v in pm.items():
            out.append('PageMedia{}: {}'.format(k, v))
        return "\n".join(out)
