import os
from os.path import dirname
from shutil import which
import tempfile

from gi.repository import GObject, GLib, Gio

from ..utils import local_now
from .serializer import Serializer


def write(doc, path=None, on_success=None, on_error=None):
    writer = Writer()
    if callable(on_success):
        writer.connect('success', on_success)
    if callable(on_error):
        writer.connect('error', on_error)
    writer.write(doc, path)


class Writer(GObject.GObject):

    __gsignals__ = {
        # args=(Document, new_file_path)
        'success': (GObject.SIGNAL_RUN_FIRST, None, (object, str)),
        # args=(Document,)
        'error': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'complete': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__()

    def write(self, doc, dst=None):
        pdftk = which('pdftk')
        if not pdftk:
            self.emit('error', 'pdftk executable not found')
            return
        if not doc.path:
            self.emit('error', 'Document was not loaded from disk')
            return
        if not dst:
            dst = doc.path
        try:
            stdin = Serializer().serialize(doc)
        except Exception as err:
            self.emit('error', err)
            self.emit('complete')
            return

        _, outfile = tempfile.mkstemp(dir=dirname(dst))

        p = Gio.Subprocess.new(
            argv=[pdftk, doc.path, 'update_info_utf8', '-', 'output', outfile],
            flags=Gio.SubprocessFlags.STDIN_PIPE
        )
        p.communicate_utf8_async(
            stdin_buf=stdin,
            callback=self._on_subprocess_complete,
            user_data=(doc, outfile, dst)
        )

    def _on_subprocess_complete(self, subprocess, result, user_data):
        doc, outfile, dst = user_data
        try:
            success, stdout, _ = subprocess.communicate_utf8_finish(result)
            os.replace(outfile, dst)
            self.emit('success', doc, dst)
        except GLib.Error as err:
            self._maybe_delete_file(outfile)
            self.emit('error', err)
        self.emit('complete')

    def _maybe_delete_file(self, path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

