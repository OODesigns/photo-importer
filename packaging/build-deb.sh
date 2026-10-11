#!/usr/bin/env bash
set -euo pipefail

# Builds packaging/build/photo-importer_<version>_all.deb from the project
# sources. Does not install anything system-wide.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_NAME="photo-importer"
VERSION="$(sed -nE 's/^version = "(.*)"/\1/p' "$ROOT_DIR/pyproject.toml")"
STAGE_DIR="$ROOT_DIR/packaging/build/${PKG_NAME}_${VERSION}_all"
OUTPUT_DEB="$ROOT_DIR/packaging/build/${PKG_NAME}_${VERSION}_all.deb"

rm -rf "$STAGE_DIR"
mkdir -p \
    "$STAGE_DIR/DEBIAN" \
    "$STAGE_DIR/usr/lib/python3/dist-packages" \
    "$STAGE_DIR/usr/bin" \
    "$STAGE_DIR/usr/share/applications" \
    "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps" \
    "$STAGE_DIR/usr/share/doc/${PKG_NAME}"

cp -r "$ROOT_DIR/src/photo_importer" "$STAGE_DIR/usr/lib/python3/dist-packages/"
find "$STAGE_DIR/usr/lib/python3/dist-packages/photo_importer" -type d -name "__pycache__" -exec rm -rf {} +

install -m 755 "$ROOT_DIR/packaging/photo-importer.sh" "$STAGE_DIR/usr/bin/photo-importer"
install -m 644 "$ROOT_DIR/packaging/photo-importer.desktop" "$STAGE_DIR/usr/share/applications/photo-importer.desktop"
install -m 644 "$ROOT_DIR/packaging/icons/photo-importer.png" "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps/photo-importer.png"
install -m 644 "$ROOT_DIR/README.md" "$STAGE_DIR/usr/share/doc/${PKG_NAME}/README.md"

sed "s/@VERSION@/${VERSION}/" "$ROOT_DIR/packaging/debian/control" > "$STAGE_DIR/DEBIAN/control"
install -m 755 "$ROOT_DIR/packaging/debian/postinst" "$STAGE_DIR/DEBIAN/postinst"
install -m 755 "$ROOT_DIR/packaging/debian/postrm" "$STAGE_DIR/DEBIAN/postrm"

fakeroot dpkg-deb --build --root-owner-group "$STAGE_DIR" "$OUTPUT_DEB"

echo "Built: $OUTPUT_DEB"
echo "Install with: sudo apt install ${OUTPUT_DEB#"$ROOT_DIR"/}"
