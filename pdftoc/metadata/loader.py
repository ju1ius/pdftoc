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
    }

    def __init__(self):
        super().__init__()

    def do_error(self, err):
        print(err)

    def load(self, doc):
        pdftk = which('pdftk')
        if not pdftk:
            return self.emit('error', 'pdftk executable not found')
        p = Gio.Subprocess.new(
            argv=[pdftk, doc.path, 'dump_data_utf8'],
            flags=Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_PIPE
        )
        p.communicate_utf8_async(callback=self._on_subprocess_complete, user_data=doc)

    def _on_subprocess_complete(self, subprocess, result, doc):
        try:
            success, stdout, stderr = subprocess.communicate_utf8_finish(result)
            retcode = subprocess.get_exit_status()
        except GLib.Error as err:
            return self.emit('error', err)
        if retcode != 0:
            return self.emit('error', f'pdftk command failed with exit code {retcode}')
        try:
            Parser().parse(stdout, doc)
            self.emit('success', doc)
        except Exception as err:
            self.emit('error', err)
