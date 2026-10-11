"""Executes an import plan against the filesystem, never overwriting complete existing files."""
from typing import Callable, List, Optional

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.application.duty_cycle_throttle import DutyCycleThrottle
from photo_importer.domain.import_entry_result import ImportEntryResult
from photo_importer.domain.import_outcome import ImportOutcome
from photo_importer.domain.import_plan_entry import ImportPlanEntry
from photo_importer.domain.import_summary import ImportSummary
from photo_importer.infrastructure.filesystem_gateway import FilesystemGateway

ProgressCallback = Callable[[ImportEntryResult], None]


class ImportExecutor:
    def __init__(self, filesystem_gateway: FilesystemGateway) -> None:
        self._filesystem_gateway = filesystem_gateway

    def execute(
        self,
        plan_entries: List[ImportPlanEntry],
        on_progress: Optional[ProgressCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        throttle: Optional[DutyCycleThrottle] = None,
        max_copies: int = 0,
    ) -> ImportSummary:
        results = []
        copied_so_far = 0
        for entry in plan_entries:
            if max_copies > 0 and copied_so_far >= max_copies:
                return ImportSummary.of(results, batch_limit_reached=True)
            if throttle is not None:
                throttle.rest_if_due(cancellation_token)
            if cancellation_token is not None and cancellation_token.is_cancel_requested:
                return ImportSummary.of(results, cancelled=True)
            result = self._execute_entry(entry)
            results.append(result)
            copied_so_far += result.outcome is ImportOutcome.COPIED
            if on_progress is not None:
                on_progress(result)
        return ImportSummary.of(results)

    def _execute_entry(self, entry: ImportPlanEntry) -> ImportEntryResult:
        try:
            if self._is_already_imported(entry):
                return ImportEntryResult.skipped_duplicate(entry)
            self._filesystem_gateway.make_parent_directories(entry.destination_path)
            self._filesystem_gateway.copy_file(entry.media_file.source_path, entry.destination_path)
            return ImportEntryResult.copied(entry)
        except OSError as error:
            return ImportEntryResult.failed(entry, str(error))

    def _is_already_imported(self, entry: ImportPlanEntry) -> bool:
        # A size mismatch means an earlier run was cut short mid-copy, so it is redone.
        gateway = self._filesystem_gateway
        return gateway.exists(entry.destination_path) and gateway.file_size(
            entry.destination_path
        ) == gateway.file_size(entry.media_file.source_path)
