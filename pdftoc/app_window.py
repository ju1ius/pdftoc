import datetime
from os.path import abspath, dirname

from gi.repository import GObject, Gtk, Gio

from .metadata.model import Document
from .metadata import loader, writer
from .utils import local_timezone, local_now
from .toc.controller import TOCController


LOCAL_TZ = local_timezone()

BIND_DEFAULT = (GObject.BindingFlags.DEFAULT
                | GObject.BindingFlags.SYNC_CREATE)
BIND_BIDIRECTIONAL = (GObject.BindingFlags.BIDIRECTIONAL
                      | GObject.BindingFlags.SYNC_CREATE)


class AppWindowController:

    def __init__(self, app, builder):
        self._document = None

        self.window = builder.get_object('app_window')
        self.window.set_show_menubar(False)

        for action, handler in (
            ('close', self._handle_action_close),
            ('open', self._handle_action_open),
            ('save', self._handle_action_save),
            ('save-as', self._handle_action_save_as),
        ):
            action = Gio.SimpleAction.new(action, None)
            action.connect('activate', handler)
            self.window.add_action(action)

        self.header = builder.get_object('main_header')

        self.statusbar = builder.get_object('main_statusbar')
        self.message_contexts = {
            'io': self.statusbar.get_context_id('io')
        }

        self.menu_btn = builder.get_object('main_menu_btn')
        self.menu_btn.set_menu_model(builder.get_object('win-menu'))

        self.title_entry = builder.get_object('meta_title_entry')
        self.subject_entry = builder.get_object('meta_subject_entry')
        self.author_entry = builder.get_object('meta_author_entry')
        self.creator_entry = builder.get_object('meta_creator_entry')
        self.creation_entry = builder.get_object('meta_creation_date_entry')
        self.creation_entry.connect('day-selected', self._on_creation_date_changed)

        self.toc = TOCController(app, builder)

        # initialize with empty document to avoid errors when no file is loaded
        self.set_document(Document())

        self.window.show_all()

    def get_window_id(self):
        return self.window.get_id()

    def present(self):
        self.window.present()

    def set_document(self, doc):
        self._document = doc
        doc.bind_property('title', self.title_entry, 'text', BIND_BIDIRECTIONAL)
        doc.bind_property('title', self.header, 'title', BIND_DEFAULT)
        doc.bind_property('subject', self.subject_entry, 'text', BIND_BIDIRECTIONAL)
        doc.bind_property('author', self.author_entry, 'text', BIND_BIDIRECTIONAL)
        doc.bind_property('author', self.header, 'subtitle', BIND_DEFAULT)
        doc.bind_property('creator', self.creator_entry, 'text', BIND_BIDIRECTIONAL)
        if doc.creation_date:
            self.creation_entry.props.year = doc.creation_date.year
            self.creation_entry.props.month = doc.creation_date.month
            self.creation_entry.props.day = doc.creation_date.day
        self.toc.set_model(doc.outline)

    def get_document(self):
        return self._document

    def open_file(self, path):
        self.statusbar.push(self.message_contexts['io'], 'Loading: {}'.format(path))
        doc = Document(abspath(path))
        loader.load(doc, self._on_document_loaded, self._on_document_load_error)

    def save(self, path=None):
        if not self._document:
            return
        self.statusbar.push(self.message_contexts['io'], 'Saving: {}'.format(path or self._document.path))
        self._document.modification_date = local_now()
        writer.write(self._document, path, self._on_document_saved, self._on_document_save_error)

    def _on_document_loaded(self, loader, doc):
        self.set_document(doc)
        msg_ctx = self.message_contexts['io']
        self.statusbar.pop(msg_ctx)
        self.statusbar.push(msg_ctx, f'Loaded: {doc.path}')

    def _on_document_load_error(self, loader, error):
        msg_ctx = self.message_contexts['io']
        self.statusbar.pop(msg_ctx)
        self.statusbar.push(msg_ctx, f'Error: {error}')

    def _on_document_saved(self, writer, doc, newpath):
        doc.path = newpath
        msg_ctx = self.message_contexts['io']
        self.statusbar.pop(msg_ctx)
        self.statusbar.push(msg_ctx, f'Saved: {doc.path}')

    def _on_document_save_error(self, writer, error):
        msg_ctx = self.message_contexts['io']
        self.statusbar.pop(msg_ctx)
        self.statusbar.push(msg_ctx, f'Error: {error}')

    def _on_creation_date_changed(self, widget, data=None):
        if not self._document:
            return
        year, month, day = widget.get_date()
        date = datetime.datetime(year, month, day, tzinfo=LOCAL_TZ)
        self._document.creation_date = date

    def _handle_action_close(self, action, param):
        # TODO: Show a warning dialog if there are unsaved changes
        self.window.close()

    def _handle_action_open(self, action, param):
        dialog = Gtk.FileChooserDialog(
            'Open PDF',
            self.window,
            Gtk.FileChooserAction.OPEN,
            ('_Cancel', Gtk.ResponseType.CANCEL,
             '_Open', Gtk.ResponseType.OK)
        )
        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name('PDF Files')
        filter_pdf.add_mime_type('application/pdf')
        dialog.add_filter(filter_pdf)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.open_file(dialog.get_filename())
        dialog.destroy()

    def _handle_action_save(self, action, param):
        if not self._document:
            return
        self.save()

    def _handle_action_save_as(self, action, param):
        if not self._document:
            return
        dialog = Gtk.FileChooserDialog(
            'Save As',
            self.window,
            Gtk.FileChooserAction.SAVE,
            ('_Cancel', Gtk.ResponseType.CANCEL,
             'Save _As', Gtk.ResponseType.OK)
        )

        dialog.set_filename(self._document.path)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.save(dialog.get_filename())
        dialog.destroy()

