import os.path
from os.path import abspath, dirname

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk


from .metadata.loader import Loader
from .app_window import AppWindowController


__dir__ = dirname(abspath(__file__))


class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(
            application_id='me.ju1ius.pdftoc',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        # Maps window ids to controller objects
        self.controllers = {}

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new('open', None)
        action.connect('activate', self.on_open)
        self.add_action(action)

        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self.on_quit)
        self.add_action(action)

    def do_activate(self):
        controller = self._create_controller()
        controller.present()

    def do_window_removed(self, window, data=None):
        del self.controllers[window.get_id()]
        Gtk.Application.do_window_removed(self, window)

    def do_open(self, files, n_files, hint):
        for gfile in files:
            path = gfile.get_path()
            if not path:
                print('TODO: implement remote files.')
                continue
            controller = self._create_controller()
            controller.present()
            controller.open_file(path)

    def on_quit(self, action, param):
        self.quit()

    def on_open(self, action, param):
        pass

    def _create_controller(self):
        resources = os.path.join(__dir__, 'resources')
        builder = Gtk.Builder.new_from_file(os.path.join(resources, 'app_window.ui'))
        builder.add_from_file(os.path.join(resources, 'menus.ui'))
        controller = AppWindowController(builder)
        self.add_window(controller.window)
        self.controllers[controller.get_window_id()] = controller

        return controller
