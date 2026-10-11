"""GTK window that lets a user pick folders, tweak the destination pattern, and run an import."""
import threading
from pathlib import Path
from typing import Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.application.duty_cycle_throttle import DutyCycleThrottle
from photo_importer.application.import_executor import ImportExecutor
from photo_importer.application.import_planner import ImportPlanner
from photo_importer.application.source_folder_scanner import SourceFolderScanner
from photo_importer.domain.app_settings import AppSettings
from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.domain.import_entry_result import ImportEntryResult
from photo_importer.domain.import_outcome import ImportOutcome
from photo_importer.domain.throttle_level import ThrottleLevel
from photo_importer.domain.throttle_policy import ThrottlePolicy
from photo_importer.infrastructure.app_settings_store import AppSettingsStore
from photo_importer.infrastructure.exif_date_reader import ExifDateReader
from photo_importer.infrastructure.filesystem_gateway import RealFilesystemGateway


_THROTTLE_CHOICES = {
    ThrottleLevel.VERY_GENTLE: "Very gentle (10 MB/s, 60 s rest every minute) - for hot NAS",
    ThrottleLevel.GENTLE: "Gentle (25 MB/s, 30 s rest every minute) - recommended for NAS",
    ThrottleLevel.NORMAL: "Normal (60 MB/s, 30 s rest every 5 minutes)",
    ThrottleLevel.OFF: "Off (full speed)",
}


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application) -> None:
        super().__init__(application=application, title="Photo Importer")
        self.set_default_size(640, 480)

        filesystem_gateway = RealFilesystemGateway()
        self._scanner = SourceFolderScanner(filesystem_gateway, ExifDateReader(filesystem_gateway))
        self._settings_store = AppSettingsStore(AppSettingsStore.default_config_path())
        settings = self._settings_store.load()

        self._source_chooser = _FolderPickerRow("Source folder", str(settings.source_folder), self)
        self._destination_chooser = _FolderPickerRow("Destination folder", str(settings.destination_folder), self)

        self._pattern_entry = Gtk.Entry(text=settings.destination_pattern.template)
        self._pattern_entry.connect("changed", self._on_pattern_changed)
        self._pattern_preview = Gtk.Label(xalign=0)

        self._throttle_combo = Gtk.ComboBoxText()
        for level in _THROTTLE_CHOICES:
            self._throttle_combo.append(level.value, _THROTTLE_CHOICES[level])
        self._throttle_combo.set_active_id(settings.throttle_level.value)
        self._batch_spin = Gtk.SpinButton.new_with_range(0, 1_000_000, 100)
        self._batch_spin.set_value(settings.batch_limit)

        defaults = AppSettings.defaults()
        self._defaults_label = Gtk.Label(
            xalign=0,
            label=(
                f"Factory defaults: {defaults.source_folder} -> {defaults.destination_folder} "
                f"[{defaults.destination_pattern.template}]"
            ),
        )

        self._reset_button = Gtk.Button(label="Reset to Defaults")
        self._reset_button.connect("clicked", self._on_reset_clicked)
        self._save_button = Gtk.Button(label="Save Settings")
        self._save_button.connect("clicked", self._on_save_clicked)
        settings_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        settings_buttons.pack_start(self._reset_button, False, False, 0)
        settings_buttons.pack_start(self._save_button, False, False, 0)

        self._cancellation_token: Optional[CancellationToken] = None

        self._start_button = Gtk.Button(label="Start Import")
        self._start_button.connect("clicked", self._on_start_clicked)
        self._cancel_button = Gtk.Button(label="Cancel")
        self._cancel_button.connect("clicked", self._on_cancel_clicked)
        self._cancel_button.set_sensitive(False)
        run_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        run_buttons.pack_start(self._start_button, False, False, 0)
        run_buttons.pack_start(self._cancel_button, False, False, 0)

        self._status_label = Gtk.Label(xalign=0, label="Choose folders and press Start Import.")
        self._progress_bar = Gtk.ProgressBar(show_text=True)

        self._log_buffer = Gtk.TextBuffer()
        log_view = Gtk.TextView(buffer=self._log_buffer, editable=False, cursor_visible=False)
        log_scroller = Gtk.ScrolledWindow()
        log_scroller.set_vexpand(True)
        log_scroller.add(log_view)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin=12)
        root.pack_start(self._source_chooser.widget, False, False, 0)
        root.pack_start(self._destination_chooser.widget, False, False, 0)
        root.pack_start(self._build_pattern_row(), False, False, 0)
        root.pack_start(self._build_throttle_row(), False, False, 0)
        root.pack_start(self._defaults_label, False, False, 0)
        root.pack_start(settings_buttons, False, False, 0)
        root.pack_start(run_buttons, False, False, 0)
        root.pack_start(self._status_label, False, False, 0)
        root.pack_start(self._progress_bar, False, False, 0)
        root.pack_start(log_scroller, True, True, 0)
        self.add(root)

        self._update_pattern_preview()
        self.show_all()

    def _build_pattern_row(self) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label = Gtk.Label(
            xalign=0,
            label="Destination format (tokens: {year} {month} {day} {category} {filename})",
        )
        row.pack_start(label, False, False, 0)
        row.pack_start(self._pattern_entry, False, False, 0)
        row.pack_start(self._pattern_preview, False, False, 0)
        return row

    def _build_throttle_row(self) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        row.pack_start(Gtk.Label(xalign=0, label="Drive protection (limits speed and adds cooling pauses)"), False, False, 0)
        row.pack_start(self._throttle_combo, False, False, 0)
        row.pack_start(Gtk.Label(xalign=0, label="Stop after this many copied files (0 = no limit; run again to continue)"), False, False, 0)
        row.pack_start(self._batch_spin, False, False, 0)
        return row

    def _on_pattern_changed(self, _entry: Gtk.Entry) -> None:
        self._update_pattern_preview()

    def _update_pattern_preview(self) -> None:
        try:
            pattern = DestinationPattern(self._pattern_entry.get_text())
        except ValueError as error:
            self._pattern_preview.set_markup(f"<span foreground='red'>{GLib.markup_escape_text(str(error))}</span>")
            return
        self._pattern_preview.set_text(f"Example: {pattern.preview()}")

    def _on_save_clicked(self, _button: Gtk.Button) -> None:
        settings = self._current_settings()
        if settings is None:
            return
        self._settings_store.save(settings)
        self._status_label.set_text(f"Settings saved to {self._settings_store.config_path}")

    def _on_reset_clicked(self, _button: Gtk.Button) -> None:
        defaults = AppSettings.defaults()
        self._source_chooser.entry.set_text(str(defaults.source_folder))
        self._destination_chooser.entry.set_text(str(defaults.destination_folder))
        self._pattern_entry.set_text(defaults.destination_pattern.template)
        self._throttle_combo.set_active_id(defaults.throttle_level.value)
        self._batch_spin.set_value(defaults.batch_limit)
        self._status_label.set_text("Fields reset to factory defaults (not saved yet).")

    def _current_settings(self) -> Optional[AppSettings]:
        try:
            pattern = DestinationPattern(self._pattern_entry.get_text())
        except ValueError as error:
            self._status_label.set_text(f"Invalid destination format: {error}")
            return None
        return AppSettings(
            source_folder=Path(self._source_chooser.selected_path),
            destination_folder=Path(self._destination_chooser.selected_path),
            destination_pattern=pattern,
            throttle_level=ThrottleLevel(self._throttle_combo.get_active_id()),
            batch_limit=self._batch_spin.get_value_as_int(),
        )

    def _on_start_clicked(self, _button: Gtk.Button) -> None:
        settings = self._current_settings()
        if settings is None:
            return
        self._settings_store.save(settings)

        self._cancellation_token = CancellationToken()
        self._scan_progress_counter = 0
        self._copy_progress_completed = 0
        self._copy_progress_total = 0
        self._start_button.set_sensitive(False)
        self._cancel_button.set_sensitive(True)
        self._log_buffer.set_text("")
        self._status_label.set_text(f"Scanning {settings.source_folder} ...")
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_text("Scanning...")

        thread = threading.Thread(
            target=self._run_import,
            args=(settings.source_folder, settings.destination_folder, settings.destination_pattern,
                  settings.throttle_level, settings.batch_limit, self._cancellation_token),
            daemon=True,
        )
        thread.start()

    def _on_cancel_clicked(self, _button: Gtk.Button) -> None:
        if self._cancellation_token is not None:
            self._cancellation_token.request_cancel()
        self._cancel_button.set_sensitive(False)
        self._status_label.set_text("Cancelling... (finishing current file)")

    def _run_import(
        self,
        source_folder: Path,
        destination_folder: Path,
        pattern: DestinationPattern,
        throttle_level: ThrottleLevel,
        batch_limit: int,
        cancellation_token: CancellationToken,
    ) -> None:
        try:
            policy = ThrottlePolicy.for_level(throttle_level)
            scan_result = self._scanner.scan(
                source_folder,
                on_file_found=self._report_scan_progress,
                cancellation_token=cancellation_token,
                throttle=DutyCycleThrottle(policy, on_rest=self._report_rest),
            )
        except OSError as error:
            GLib.idle_add(self._status_label.set_text, f"Failed to read source folder: {error}")
            GLib.idle_add(self._on_run_finished)
            return

        if scan_result.cancelled:
            GLib.idle_add(
                self._status_label.set_text,
                f"Cancelled during scan ({len(scan_result.media_files)} file(s) found before stopping).",
            )
            GLib.idle_add(self._on_run_finished)
            return

        GLib.idle_add(self._status_label.set_text, f"Found {len(scan_result.media_files)} file(s). Importing...")
        plan_entries = ImportPlanner(destination_folder, pattern).plan_for(list(scan_result.media_files))
        self._copy_progress_total = len(plan_entries)
        GLib.idle_add(self._progress_bar.set_fraction, 0.0)
        summary = self._build_executor(policy).execute(
            plan_entries,
            on_progress=self._report_progress,
            cancellation_token=cancellation_token,
            throttle=DutyCycleThrottle(policy, on_rest=self._report_rest),
            max_copies=batch_limit,
        )

        message = (
            f"Done: {summary.copied_count} copied, "
            f"{summary.skipped_count} skipped, {summary.failed_count} failed "
            f"({summary.total_count} of {len(plan_entries)} total)"
        )
        if summary.cancelled:
            message = f"Cancelled. {message}"
        if summary.batch_limit_reached:
            message = f"Batch limit reached - run again to continue. {message}"
        GLib.idle_add(self._status_label.set_text, message)
        GLib.idle_add(self._on_run_finished)

    @staticmethod
    def _build_executor(policy: ThrottlePolicy) -> ImportExecutor:
        return ImportExecutor(RealFilesystemGateway(max_bytes_per_second=policy.max_bytes_per_second))

    def _report_rest(self, rest_seconds: float) -> None:
        GLib.idle_add(self._status_label.set_text, f"Resting {rest_seconds:.0f} s to let the drives cool...")

    def _on_run_finished(self) -> None:
        self._cancellation_token = None
        self._start_button.set_sensitive(True)
        self._cancel_button.set_sensitive(False)

    def _report_scan_progress(self, path: Path) -> None:
        # Throttled: updating the label on every single file would flood the
        # GTK main loop with idle callbacks on trees with many thousands of files.
        self._scan_progress_counter += 1
        if self._scan_progress_counter % 20 == 0:
            GLib.idle_add(self._pulse_progress_bar, f"Scanning... found {self._scan_progress_counter} files")
            GLib.idle_add(self._status_label.set_text, f"Scanning... found {self._scan_progress_counter} files, latest: {path}")

    def _pulse_progress_bar(self, text: str) -> None:
        self._progress_bar.set_text(text)
        self._progress_bar.pulse()

    def _report_progress(self, result: ImportEntryResult) -> None:
        self._copy_progress_completed += 1
        GLib.idle_add(self._update_copy_progress_bar, self._copy_progress_completed, self._copy_progress_total)
        GLib.idle_add(self._append_log, self._describe(result))

    def _update_copy_progress_bar(self, completed: int, total: int) -> None:
        fraction = completed / total if total else 1.0
        percent = round(fraction * 100)
        self._progress_bar.set_fraction(fraction)
        self._progress_bar.set_text(f"{completed}/{total} ({percent}%)")

    def _append_log(self, line: str) -> None:
        end_iter = self._log_buffer.get_end_iter()
        self._log_buffer.insert(end_iter, line + "\n")

    @staticmethod
    def _describe(result: ImportEntryResult) -> str:
        source_name = result.entry.media_file.source_path.name
        if result.outcome is ImportOutcome.COPIED:
            return f"Copied   {source_name} -> {result.entry.destination_path}"
        if result.outcome is ImportOutcome.SKIPPED_DUPLICATE:
            return f"Skipped  {source_name} (already exists)"
        return f"Failed   {source_name}: {result.error_message}"


class _FolderPickerRow:
    """A labeled entry + browse button pair for choosing a folder."""

    def __init__(self, label_text: str, default_path: str, parent_window: Gtk.Window) -> None:
        self._parent_window = parent_window
        self.entry = Gtk.Entry(text=default_path, hexpand=True)
        browse_button = Gtk.Button(label="Choose...")
        browse_button.connect("clicked", self._on_browse_clicked)

        label = Gtk.Label(xalign=0, label=label_text)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.pack_start(self.entry, True, True, 0)
        row.pack_start(browse_button, False, False, 0)

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.widget.pack_start(label, False, False, 0)
        self.widget.pack_start(row, False, False, 0)

    @property
    def selected_path(self) -> str:
        return self.entry.get_text()

    def _on_browse_clicked(self, _button: Gtk.Button) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Select folder",
            parent=self._parent_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        current_path = self.entry.get_text()
        if current_path:
            dialog.set_current_folder(current_path)
        if dialog.run() == Gtk.ResponseType.OK:
            self.entry.set_text(dialog.get_filename())
        dialog.destroy()
