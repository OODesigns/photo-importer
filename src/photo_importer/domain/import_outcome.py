"""Possible outcomes of attempting to import a single media file."""
from enum import Enum


class ImportOutcome(Enum):
    COPIED = "copied"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    FAILED = "failed"
