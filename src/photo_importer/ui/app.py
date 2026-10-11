"""GTK application entry point."""
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from photo_importer.ui.main_window import MainWindow


class PhotoImporterApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id="com.local.photoimporter")
        self._window = None

    def do_activate(self) -> None:
        if self._window is None:
            self._window = MainWindow(self)
        self._window.present()
