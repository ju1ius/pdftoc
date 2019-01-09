from pathlib import Path
import json

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gio, Gtk, Gdk

from .app_window import AppWindowController


__dir__ = Path(__file__).absolute().parent


class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(
            application_id='me.ju1ius.pdftoc',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        self.resource_path: Path = __dir__ / 'resources'
        # Maps window ids to controller objects
        self.controllers = {}
        self.css_provider = Gtk.CssProvider()

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

        self.css_provider.load_from_path(str(self.resource_path / 'app.css'))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._load_keybindings()

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
        self.quit()

    def on_open(self, action, param):
        controller = self._create_controller()
        controller.present()

    def _load_keybindings(self):
        with open(self.resource_path / 'keybindings.json', encoding='utf8') as fp:
            config = json.load(fp)
            for action, accels in config['actions'].items():
                self.set_accels_for_action(action, accels)

    def _create_controller(self):
        builder = Gtk.Builder.new_from_file(str(self.resource_path / 'app_window.ui'))
        builder.add_from_file(str(self.resource_path / 'menus.ui'))
        controller = AppWindowController(self, builder)
        controller.window.get_style_context()
        self.add_window(controller.window)
        self.controllers[controller.get_window_id()] = controller

        return controller
