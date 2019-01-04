from shutil import which
from os.path import abspath, dirname

from gi.repository import GObject, GLib, Gio

from .parser import Parser


def load(doc, on_success=None, on_error=None):
    loader = Loader()
    if callable(on_success):
        loader.connect('success', on_success)
    if callable(on_error):
        loader.connect('error', on_error)
    loader.load(doc)


class Loader(GObject.GObject):

    __gsignals__ = {
        'success': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'error': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'complete': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super().__init__()

    def do_error(self, err):
        print(err)

    def load(self, doc):
        pdftk = which('pdftk')
        if not pdftk:
            self.emit('error', 'pdftk executable not found')
            return
        p = Gio.Subprocess.new(
            argv=[pdftk, doc.path, 'dump_data_utf8'],
            flags=Gio.SubprocessFlags.STDOUT_PIPE
        )
        p.communicate_utf8_async(callback=self._on_subprocess_complete, user_data=doc)

    def _on_subprocess_complete(self, subprocess, result, doc):
        try:
            success, stdout, _ = subprocess.communicate_utf8_finish(result)
        except GLib.Error as err:
            self.emit('error', err)
            self.emit('complete')
            return
        try:
            Parser().parse(stdout, doc)
        except Exception as err:
            self.emit('error', err)
            self.emit('complete')
            return
        self.emit('success', doc)
        self.emit('complete')

