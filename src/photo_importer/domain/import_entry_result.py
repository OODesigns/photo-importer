"""Typed result of executing a single import plan entry."""
from dataclasses import dataclass
from typing import Optional

from photo_importer.domain.import_outcome import ImportOutcome
from photo_importer.domain.import_plan_entry import ImportPlanEntry


@dataclass(frozen=True)
class ImportEntryResult:
    entry: ImportPlanEntry
    outcome: ImportOutcome
    error_message: Optional[str] = None

    @staticmethod
    def copied(entry: ImportPlanEntry) -> "ImportEntryResult":
        return ImportEntryResult(entry, ImportOutcome.COPIED)

    @staticmethod
    def skipped_duplicate(entry: ImportPlanEntry) -> "ImportEntryResult":
        return ImportEntryResult(entry, ImportOutcome.SKIPPED_DUPLICATE)

    @staticmethod
    def failed(entry: ImportPlanEntry, error_message: str) -> "ImportEntryResult":
        return ImportEntryResult(entry, ImportOutcome.FAILED, error_message)
