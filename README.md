# Photo Importer

A small GTK3 desktop app for Linux Mint that copies photos from a chosen
source folder into a dated folder structure on your NAS, matching the
existing layout under `/mnt/photo` (`<year>/<month>-<day>/<category>/<filename>`).

## Features
- Pick any source and destination folder via native folder choosers.
- Destination folder format is editable in the app (tokens: `{year}`,
  `{month}`, `{day}`, `{category}`, `{filename}`), with a live preview.
- Capture date comes from EXIF `DateTimeOriginal` when available, otherwise
  falls back to the file's modified time.
- Existing destination files are never overwritten or duplicated, so an
  import can be safely re-run.
- Copies (does not delete/move) source files.

## Requirements
- Python 3.10+
- GTK 3 + PyGObject: `sudo apt install python3-gi gir1.2-gtk-3.0` (Mint/Ubuntu)
- Pillow

## Setup

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

`--system-site-packages` lets the venv see the system-installed PyGObject/GTK.

## Run

```bash
python -m photo_importer.main
```

## Install as a Mint desktop app (.deb)

Build a package that installs the app, a `/usr/bin/photo-importer` launcher,
and a menu entry + icon:

```bash
./packaging/build-deb.sh
sudo apt install ./packaging/build/photo-importer_0.1.0_all.deb
```

It then appears in the application menu as "Photo Importer" (or run
`photo-importer` from a terminal). Uninstall with
`sudo apt remove photo-importer`.

## Test

```bash
pytest
```

Unit tests cover the domain/application logic in isolation (no GTK, no real
filesystem). Integration tests run the full scan -> plan -> copy pipeline
against a temporary filesystem.
