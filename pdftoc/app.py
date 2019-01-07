import os.path
from os.path import abspath, dirname

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gio, Gtk

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
        """
        Called on application startup
        """
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new('open', None)
        action.connect('activate', self.on_open)
        self.add_action(action)

        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self.on_quit)
        self.add_action(action)

        self.set_accels_for_action('app.open', ['<Control><Shift>o'])
        self.set_accels_for_action('app.quit', ['<Control>q'])
        self.set_accels_for_action('win.open', ['<Control>o'])
        self.set_accels_for_action('win.close', ['<Control>w'])
        self.set_accels_for_action('win.save', ['<Control>s'])
        self.set_accels_for_action('win.save-as', ['<Control><Shift>s'])

    def do_activate(self):
        """
        Called when app is activated without a file parameter
        """
        Gtk.Application.do_activate(self)
        controller = self._create_controller()
        controller.present()

    def do_open(self, files, n_files, hint):
        """
        Called when app is activated with a file parameter
        """
        for gfile in files:
            path = gfile.get_path()
            if not path:
                print('TODO: implement remote files.')
                continue
            controller = self._create_controller()
            controller.present()
            controller.open_file(path)

    def do_window_removed(self, window, data=None):
        """
        Called when an app window is closed
        """
        del self.controllers[window.get_id()]
        Gtk.Application.do_window_removed(self, window)

    def on_quit(self, action, param):
        print('app.on_quit')
        self.quit()

    def on_open(self, action, param):
        print('app.on_open')
        controller = self._create_controller()
        controller.present()

    def _create_controller(self):
        resources = os.path.join(__dir__, 'resources')
        builder = Gtk.Builder.new_from_file(os.path.join(resources, 'app_window.ui'))
        builder.add_from_file(os.path.join(resources, 'menus.ui'))
        controller = AppWindowController(self, builder)
        self.add_window(controller.window)
        self.controllers[controller.get_window_id()] = controller

        return controller
