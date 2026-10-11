"""Aggregate, typed outcome of an entire import run."""
from dataclasses import dataclass
from typing import List, Tuple

from photo_importer.domain.import_entry_result import ImportEntryResult
from photo_importer.domain.import_outcome import ImportOutcome


@dataclass(frozen=True)
class ImportSummary:
    results: Tuple[ImportEntryResult, ...]
    cancelled: bool = False

    @staticmethod
    def of(results: List[ImportEntryResult], cancelled: bool = False) -> "ImportSummary":
        return ImportSummary(tuple(results), cancelled)

    @property
    def copied_count(self) -> int:
        return self._count(ImportOutcome.COPIED)

    @property
    def skipped_count(self) -> int:
        return self._count(ImportOutcome.SKIPPED_DUPLICATE)

    @property
    def failed_count(self) -> int:
        return self._count(ImportOutcome.FAILED)

    @property
    def total_count(self) -> int:
        return len(self.results)

    def _count(self, outcome: ImportOutcome) -> int:
        return sum(1 for result in self.results if result.outcome is outcome)
