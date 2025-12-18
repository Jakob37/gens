"""Utility functions."""

import datetime
import gzip
from pathlib import Path


def get_timestamp() -> datetime.datetime:
    """Get datetime timestamp in utc timezone."""
    return datetime.datetime.now(tz=datetime.timezone.utc)


def get_counts_columns(file: Path) -> list[str]:
    """Parse value column names from a tabixed multi-column counts file."""

    with gzip.open(file, "rt", encoding="utf-8") as handle:
        header_line = handle.readline().strip()

    if not header_line.startswith("#"):
        raise ValueError("Counts file is missing header line")

    columns = header_line.lstrip("#").split("\t")
    if len(columns) < 4:
        raise ValueError("Counts header must include at least one value column")

    return columns[3:]
