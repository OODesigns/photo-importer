"""Executes an import plan against the filesystem, never overwriting existing files."""
from typing import Callable, List, Optional

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.domain.import_entry_result import ImportEntryResult
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
    ) -> ImportSummary:
        results = []
        for entry in plan_entries:
            if cancellation_token is not None and cancellation_token.is_cancel_requested:
                return ImportSummary.of(results, cancelled=True)
            result = self._execute_entry(entry)
            results.append(result)
            if on_progress is not None:
                on_progress(result)
        return ImportSummary.of(results)

    def _execute_entry(self, entry: ImportPlanEntry) -> ImportEntryResult:
        if self._filesystem_gateway.exists(entry.destination_path):
            return ImportEntryResult.skipped_duplicate(entry)
        try:
            self._filesystem_gateway.make_parent_directories(entry.destination_path)
            self._filesystem_gateway.copy_file(entry.media_file.source_path, entry.destination_path)
            return ImportEntryResult.copied(entry)
        except OSError as error:
            return ImportEntryResult.failed(entry, str(error))
