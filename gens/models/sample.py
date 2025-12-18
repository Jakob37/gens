"""Models related to sample information."""

import gzip
import re
from enum import StrEnum
from pathlib import Path

from pydantic import Field, computed_field, field_serializer, field_validator
from pydantic.types import FilePath
from pydantic_extra_types.color import Color

from gens.utils import get_counts_columns

from .base import CreatedAtModel, RWModel
from .genomic import GenomeBuild


def _get_tabix_path(path: Path, check: bool = False) -> Path:
    """Get path to a tabix index.

    The index is assumed to be in the same location as the file."""
    idx_path = path.with_suffix(path.suffix + ".tbi")
    if check and not idx_path.is_file():
        raise FileNotFoundError(f"Index file: {idx_path} was not found.")
    return idx_path


SAMPLE_RECORD_PATTERN = re.compile(r"^[A-Za-z0-9]+_(?:[1-9]|1[0-9]|2[0-2]|X|Y)$")


class ScatterDataType(StrEnum):
    COV = "coverage"
    BAF = "baf"


class ZoomLevel(StrEnum):
    """Valid zoom or resolution levels."""

    A = "a"
    B = "b"
    C = "c"
    D = "d"
    overview = "o"


class SampleSex(StrEnum):
    """Valid sample sexes."""

    MALE = "M"
    FEMALE = "F"


class MetaValue(RWModel):
    """
    The meta value can be key-value pairs or part of a table
    They always need a type. This is the key, or the column name.
    For a table, a row name needs to be present.
    Tables are stored in long format, i.e. one row represents one cell with a row and col name.
    """

    type: str
    value: str
    row_name: str | None = None
    color: str = "rgb(0,0,0)"

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        try:
            Color(value)
        except ValueError as err:
            raise ValueError(f"Invalid color: {value}") from err
        return value


class MetaEntry(RWModel):
    id: str
    file_name: str
    row_name_header: str | None = None
    data: list[MetaValue]


class SampleInfo(RWModel, CreatedAtModel):
    """Sample record stored in the database."""

    sample_id: str
    case_id: str
    genome_build: GenomeBuild
    baf_file: FilePath
    coverage_file: FilePath
    counts_file: FilePath | None = None
    overview_file: FilePath | None = None
    sample_type: str | None = None
    sex: SampleSex | None = None
    meta: list[MetaEntry] = Field(default_factory=list)

    @classmethod
    def _validate_sample_file(cls, path: Path, require_header: bool = False) -> tuple[list[str] | None, list[str]]:
        if not path.is_file():
            raise ValueError(f"Sample file not found: {path}")

        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                header_cols: list[str] | None = None
                first_line = handle.readline().strip()
                # FIXME: Should this be simplified?
                if require_header:
                    if not first_line.startswith("#"):
                        raise ValueError(
                            "Sample file must start with a header line beginning with '#'"
                        )
                    header_cols = first_line.lstrip("#").split("\t")
                    first_line = handle.readline().strip()
                else:
                    header_cols = (
                        first_line.lstrip("#").split("\t")
                        if first_line.startswith("#")
                        else None
                    )
                    if first_line.startswith("#"):
                        first_line = handle.readline().strip()
        except OSError as err:
            raise ValueError(f"Could not read sample file {path}: {err}") from err

        if not first_line:
            raise ValueError("Sample file is empty")

        columns = first_line.split("\t")
        if len(columns) < 4:
            raise ValueError(
                f"Sample file should contain four column, found: {len(columns)}. First line: {first_line}"
            )

        if not SAMPLE_RECORD_PATTERN.match(columns[0]):
            raise ValueError(
                "First column should combine zoom and chromosome: 0_1, a_X, d_22"
            )

        try:
            int(columns[1])
            int(columns[2])
            float(columns[3])
        except ValueError:
            raise ValueError(
                f"Start, end and value columns must be numeric. Found row: {first_line}"
            )

        return header_cols, columns

    @classmethod
    def _validate_counts_file(cls, path: Path) -> Path:
        header_cols, columns = cls._validate_sample_file(path, require_header=True)

        if header_cols is None:
            raise ValueError("Counts file is missing a header line")

        if len(header_cols) < 4:
            raise ValueError(
                "Counts file header must include at least one data column after chr, start and end"
            )

        value_col_count = len(header_cols) - 3
        if len(columns) - 3 != value_col_count:
            raise ValueError(
                "Counts file header does not match number of value columns in data rows"
            )

        try:
            for val in columns[3:]:
                float(val)
        except ValueError as err:
            raise ValueError("Counts file value columns must be numeric") from err

        return path


    @field_validator("baf_file", "coverage_file")
    @classmethod
    def validate_sample_files(cls, path: Path) -> Path:
        cls._validate_sample_file(path)
        return path

    @field_validator("counts_file")
    @classmethod
    def validate_counts_file(cls, path: Path | None) -> Path | None:
        if path is None:
            return None
        return cls._validate_counts_file(path)


    @computed_field()  # type: ignore
    @property
    def baf_index(self) -> FilePath:
        """Get path to a tabix index."""

        return _get_tabix_path(self.baf_file, check=True)

    @computed_field()  # type: ignore
    @property
    def coverage_index(self) -> FilePath:
        """Get path to a tabix index."""

        return _get_tabix_path(self.coverage_file, check=True)


    @computed_field()  # type: ignore
    @property
    def counts_index(self) -> FilePath | None:
        return (
            _get_tabix_path(self.counts_file, check=True)
            if self.counts_file is not None
            else None
        )

    @computed_field()  # type: ignore
    @property
    def counts_columns(self) -> list[str] | None:
        return get_counts_columns(self.counts_file) if self.counts_file else None

    @field_serializer("baf_file", "coverage_file", "overview_file")
    def serialize_path(self, path: Path) -> str:
        """Serialize a Path object as string"""

        return str(path)


class GenomeCoverage(RWModel):
    """Contains genome coverage info for scatter plots.

    The genome coverage is represented by paired list of position and value.
    """

    region: str | None
    position: list[int]
    value: list[float]
    zoom: ZoomLevel | None = None

class BinnedCounts(RWModel):
    region: str | None
    start: list[int]
    end: list[int]
    values: dict[str, list[float]]
    zoom: ZoomLevel | None = None


class MultipleSamples(RWModel):  # pylint: disable=too-few-public-methods
    """Generic response model for multiple data records."""

    data: list[SampleInfo] = Field(
        ..., description="List of records from the database."
    )
    records_total: int = Field(
        ...,
        alias="recordsTotal",
        description="Number of db records matching the query",
    )

    @property
    @computed_field(alias="recordsFiltered")
    def records_filtered(self) -> int:
        """
        Number of db returned records after narrowing the result.

        The result can be reduced with limit and skip operations etc.
        """
        return len(self.data)
