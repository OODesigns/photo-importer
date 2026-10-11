"""Launches the Photo Importer GTK application."""
import sys

from photo_importer.ui.app import PhotoImporterApp


def main() -> int:
    app = PhotoImporterApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
