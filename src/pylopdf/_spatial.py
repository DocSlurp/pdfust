"""Owned spatial snapshots and conservative, source-backed field assignment."""

from __future__ import annotations

import bisect
import html
import itertools
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Literal, TypeAlias, TypeVar

from pylopdf.pylopdf_core import LimitError, PdfError

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from pylopdf.pylopdf_core import RawLayoutBlock, RawLayoutTable

_BBox: TypeAlias = tuple[float, float, float, float]
_ValueType: TypeAlias = Literal["any", "number", "date", "text"]
_MAX_WORDS = 65_536
_MAX_FIELDS = 256
_MAX_CANDIDATES = 256
_MAX_CELLS = 4096
_FEATURE_COUNT = 6
_RECT_COORDINATES = 4
_MAX_QUERY_CHARS = 256
_MIN_EDGES = 2
_Item = TypeVar("_Item")


def _box(value: Sequence[float]) -> _BBox:
    if len(value) != _RECT_COORDINATES or any(isinstance(part, bool) for part in value):
        msg = "a region must contain four finite coordinates"
        raise PdfError(msg)
    try:
        x0, y0, x1, y1 = (float(part) for part in value)
    except (TypeError, ValueError) as exc:
        msg = "a region must contain four finite coordinates"
        raise PdfError(msg) from exc
    if not all(map(math.isfinite, (x0, y0, x1, y1))) or x0 >= x1 or y0 >= y1:
        msg = "a region must have finite coordinates and positive width and height"
        raise PdfError(msg)
    return x0, y0, x1, y1


def _contains(box: _BBox, word: SpatialWord) -> bool:
    x0, y0, x1, y1 = word.bbox
    return box[0] <= (x0 + x1) / 2 < box[2] and box[1] <= (y0 + y1) / 2 < box[3]


def _bounds(words: Sequence[SpatialWord]) -> _BBox:
    return (
        min(word.bbox[0] for word in words),
        min(word.bbox[1] for word in words),
        max(word.bbox[2] for word in words),
        max(word.bbox[3] for word in words),
    )


def _text(words: Sequence[SpatialWord]) -> str:
    parts: list[str] = []
    previous = None
    for word in words:
        if previous is not None:
            parts.append(" " if previous == word.line else "\n")
        parts.append(word.text)
        previous = word.line
    return "".join(parts)


def _bounded(items: Iterable[_Item], limit: int, label: str) -> tuple[_Item, ...]:
    result: list[_Item] = []
    for item in items:
        if len(result) == limit:
            msg = "spatial_count"
            raise LimitError(msg, f"{label} exceeds {limit} entries")
        result.append(item)
    return tuple(result)


@dataclass(frozen=True)
class SpatialWord:
    """One source word in display coordinates; IDs are local to its snapshot."""

    id: int
    text: str
    bbox: _BBox
    line: int
    direction: tuple[float, float]


@dataclass(frozen=True)
class SpatialCell:
    """One logical table cell; merged slots refer to the same cell ID."""

    id: int
    row: int
    column: int
    row_span: int
    column_span: int
    bbox: _BBox
    text: str
    word_ids: tuple[int, ...]


@dataclass(frozen=True)
class TableField:
    """A value with ordered column headers and optional row headers.

    Relationships follow the caller's declared header rows/columns. Repeated
    header text remains distinct by cell ID. A merged value can be referenced
    by more than one field; the shared cell ID makes that relationship explicit.
    """

    column: int
    headers: tuple[SpatialCell, ...]
    row_headers: tuple[SpatialCell, ...]
    cell: SpatialCell

    @property
    def name(self) -> str:
        """Return a hierarchical label, with a neutral fallback for empty headers."""
        return " / ".join(cell.text for cell in self.headers if cell.text) or f"Column {self.column + 1}"

    @property
    def value(self) -> str:
        """Return the unchanged source cell text."""
        return self.cell.text


@dataclass(frozen=True)
class SpatialTable:
    """An immutable grid in logical text orientation, with display-space boxes."""

    bbox: _BBox
    row_count: int
    col_count: int
    cells: tuple[SpatialCell, ...]
    slots: tuple[int, ...]
    strategy: str

    def records(self, *, header_rows: int, row_header_columns: int = 0) -> tuple[tuple[TableField, ...], ...]:
        """Associate values with declared header bands, retaining merged ancestry.

        Header bands must not cut through merged cells. This method does not
        guess that the first row is a header or infer semantic header scope.
        """
        for value, maximum in ((header_rows, self.row_count), (row_header_columns, self.col_count)):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < maximum:
                msg = "header bands must be nonnegative integers leaving at least one data row and column"
                raise PdfError(msg)
        for cell in self.cells:
            if cell.row < header_rows < cell.row + cell.row_span:
                msg = "header_rows cuts through a merged cell"
                raise PdfError(msg)
            if cell.row >= header_rows and cell.column < row_header_columns < cell.column + cell.column_span:
                msg = "row_header_columns cuts through a merged body cell"
                raise PdfError(msg)
        by_id = {cell.id: cell for cell in self.cells}

        def unique(indices: Iterable[int]) -> tuple[SpatialCell, ...]:
            return tuple(by_id[index] for index in dict.fromkeys(indices))

        headers = [
            unique(self.slots[row * self.col_count + column] for row in range(header_rows))
            for column in range(self.col_count)
        ]
        result = []
        for row in range(header_rows, self.row_count):
            row_headers = unique(self.slots[row * self.col_count + col] for col in range(row_header_columns))
            result.append(
                tuple(
                    TableField(col, headers[col], row_headers, by_id[self.slots[row * self.col_count + col]])
                    for col in range(row_header_columns, self.col_count)
                )
            )
        return tuple(result)

    def to_bullets(  # noqa: C901 - preflight each escaped fragment before retaining it.
        self,
        *,
        header_rows: int,
        row_header_columns: int = 0,
        max_size: int = 64 * 1024 * 1024,
    ) -> str:
        """Render labeled records, escaping source text and bounding UTF-8 output."""
        if isinstance(max_size, bool) or not isinstance(max_size, int) or max_size <= 0:
            msg = "max_size must be a positive integer"
            raise PdfError(msg)
        parts: list[str] = []
        size = 0

        def append(text: str, *, escaped: bool = False) -> None:
            nonlocal size
            size += _escaped_size(text) if escaped else len(text.encode("utf-8"))
            if size > max_size:
                msg = "spatial_output_size"
                raise LimitError(msg, f"record output exceeds {max_size} bytes")
            parts.append(_escape(text) if escaped else text)

        def labels(cells: tuple[SpatialCell, ...]) -> None:
            first = True
            for cell in cells:
                if cell.text:
                    if not first:
                        append(" / ")
                    append(cell.text, escaped=True)
                    first = False

        for row, fields in enumerate(self.records(header_rows=header_rows, row_header_columns=row_header_columns), 1):
            append(f"- Record {row}")
            if any(cell.text for cell in fields[0].row_headers):
                append(" (")
                labels(fields[0].row_headers)
                append(")")
            append("\n")
            for item in fields:
                append("  - ")
                if any(cell.text for cell in item.headers):
                    labels(item.headers)
                else:
                    append(f"Column {item.column + 1}")
                append(": ")
                append(item.value, escaped=True)
                append("\n")
        return "".join(parts)


def _escape(text: str) -> str:
    text = html.escape(text, quote=False).replace("\n", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)


def _escaped_size(text: str) -> int:
    """Preflight escape expansion without allocating a complete encoded string."""
    sizes = {"&": 5, "<": 4, ">": 4}
    return sum(sizes.get(char, len(char.encode("utf-8")) + (char in "\\`*_{}[]()#+.!|~-")) for char in text)


@dataclass(frozen=True)
class FieldSpec:
    """A named rectangle or a label-relative query in display coordinates.

    Provide ``region`` for a known value rectangle, or ``anchor`` for an exact
    case-insensitive label. With both, region scopes the label and candidates.
    Directions refer to the displayed page. ``value_type`` is an explicit hint,
    not an inferred understanding of the label's meaning.
    """

    name: str
    region: _BBox | None = None
    anchor: str | None = None
    direction: Literal["right", "below"] = "right"
    max_distance: float = 144.0
    value_type: _ValueType = "any"

    def __post_init__(self) -> None:
        """Reject invalid or unbounded query parameters before page work."""
        if not isinstance(self.name, str) or not self.name or len(self.name) > _MAX_QUERY_CHARS:
            msg = "field name must contain 1 through 256 characters"
            raise PdfError(msg)
        if self.region is not None:
            object.__setattr__(self, "region", _box(self.region))
        if self.anchor is not None and (
            not isinstance(self.anchor, str) or not self.anchor.strip() or len(self.anchor) > _MAX_QUERY_CHARS
        ):
            msg = "anchor must contain 1 through 256 characters"
            raise PdfError(msg)
        if self.anchor is None and self.region is None:
            msg = "a field needs a value region or a label anchor"
            raise PdfError(msg)
        if self.direction not in ("right", "below") or self.value_type not in ("any", "number", "date", "text"):
            msg = "invalid field direction or value_type"
            raise PdfError(msg)
        if isinstance(self.max_distance, bool) or not math.isfinite(self.max_distance) or self.max_distance <= 0:
            msg = "max_distance must be finite and positive"
            raise PdfError(msg)


@dataclass(frozen=True)
class FieldCandidate:
    """A complete source span and the geometric evidence for its placement."""

    text: str
    bbox: _BBox
    word_ids: tuple[int, ...]
    anchor_ids: tuple[int, ...]
    features: tuple[float, ...]
    score: float | None = None


@dataclass(frozen=True)
class FieldResult:
    """A selected span or an explicit abstention; rejected candidates stay visible."""

    name: str
    status: Literal["matched", "missing", "ambiguous", "conflict"]
    selected: FieldCandidate | None
    candidates: tuple[FieldCandidate, ...]

    @property
    def value(self) -> str | None:
        """Return source text only when assignment succeeded."""
        return None if self.selected is None else self.selected.text


@dataclass(frozen=True)
class PlacementModel:
    """An optional six-feature CPU logistic ranker with rejection thresholds.

    Coefficients must be fitted and evaluated on the caller's document family.
    Scores are ranking evidence, not a guarantee or calibrated probability.
    The model cannot change source text, override explicit rectangles, resolve
    duplicate anchors, or reuse one value across conflicting fields.
    """

    weights: tuple[float, ...]
    bias: float
    threshold: float = 0.9
    margin: float = 0.2

    def __post_init__(self) -> None:
        """Bound coefficients and validate the acceptance policy."""
        values = _bounded(self.weights, _FEATURE_COUNT, "placement weights")
        if len(values) != _FEATURE_COUNT or not all(math.isfinite(value) for value in (*values, self.bias)):
            msg = "placement model needs six finite weights and a finite bias"
            raise PdfError(msg)
        if not 0 < self.threshold <= 1 or not 0 <= self.margin <= 1:
            msg = "threshold must be in (0, 1] and margin in [0, 1]"
            raise PdfError(msg)
        object.__setattr__(self, "weights", values)

    def score(self, candidate: FieldCandidate) -> float:
        """Evaluate a bounded source candidate using a handful of scalar operations."""
        if len(candidate.features) != _FEATURE_COUNT or not all(map(math.isfinite, candidate.features)):
            msg = "invalid placement features"
            raise PdfError(msg)
        logit = self.bias + sum(weight * value for weight, value in zip(self.weights, candidate.features, strict=True))
        return 1 / (1 + math.exp(-max(-60.0, min(60.0, logit))))


@dataclass(frozen=True)
class PageLayout:
    """A reusable CPU spatial snapshot, independent of subsequent edits or close.

    Words, tables, and queries use top-left display coordinates. An index over
    word centers accelerates repeated rectangle queries without reparsing PDF
    instructions. Selection uses half-open rectangles and word centers.
    """

    width: float
    height: float
    words: tuple[SpatialWord, ...]
    tables: tuple[SpatialTable, ...]
    _y_order: tuple[tuple[float, int], ...] = field(repr=False, compare=False)

    def select(self, region: Sequence[float]) -> tuple[SpatialWord, ...]:
        """Return source words whose centers lie inside a validated rectangle."""
        box = _box(region)
        start = bisect.bisect_left(self._y_order, (box[1], -1))
        stop = bisect.bisect_left(self._y_order, (box[3], -1))
        return tuple(
            self.words[index]
            for index in sorted(index for _, index in self._y_order[start:stop] if _contains(box, self.words[index]))
        )

    def extract_fields(
        self,
        fields: Iterable[FieldSpec],
        *,
        model: PlacementModel | None = None,
    ) -> tuple[FieldResult, ...]:
        """Resolve bounded rectangle/anchor queries with all-or-abstain assignment.

        Without a model, exactly one eligible candidate is required. A model
        must pass both an absolute threshold and a margin over the runner-up.
        Overlapping selected source IDs invalidate every conflicting result.
        """
        specs: tuple[FieldSpec, ...] = _bounded(fields, _MAX_FIELDS, "field queries")
        if any(not isinstance(spec, FieldSpec) for spec in specs):
            msg = "fields must contain FieldSpec instances"
            raise PdfError(msg)
        if len({spec.name for spec in specs}) != len(specs):
            msg = "field names must be unique"
            raise PdfError(msg)
        if model is not None and not isinstance(model, PlacementModel):
            msg = "model must be a PlacementModel or None"
            raise PdfError(msg)
        anchors = {spec.name: self._anchors(spec) for spec in specs if spec.anchor is not None}
        label_ids = {word.id for groups in anchors.values() for group in groups for word in group}
        results = []
        for spec in specs:
            if spec.anchor is None:
                words = self.select(spec.region)  # type: ignore[arg-type]
                candidate = _candidate(words, (), ()) if words else None
                results.append(
                    FieldResult(
                        spec.name, "matched" if words else "missing", candidate, (candidate,) if candidate else ()
                    )
                )
                continue
            groups = anchors[spec.name]
            if len(groups) != 1:
                results.append(FieldResult(spec.name, "ambiguous" if groups else "missing", None, ()))
                continue
            candidates = self._candidates(spec, groups[0], label_ids)
            results.append(_resolve(spec.name, candidates, model))
        counts = Counter(word_id for result in results if result.selected for word_id in result.selected.word_ids)
        return tuple(
            replace(result, status="conflict", selected=None)
            if result.selected
            and any(counts[word_id] > 1 or word_id in label_ids for word_id in result.selected.word_ids)
            else result
            for result in results
        )

    def _anchors(self, spec: FieldSpec) -> tuple[tuple[SpatialWord, ...], ...]:
        def normalize(text: str) -> str:
            return text.casefold().strip(":")

        tokens = tuple(normalize(part) for part in (spec.anchor or "").split())
        words = self.words if spec.region is None else self.select(spec.region)
        matches: list[tuple[SpatialWord, ...]] = []
        for index in range(len(words) - len(tokens) + 1):
            group = words[index : index + len(tokens)]
            if group[0].line == group[-1].line and tuple(normalize(word.text) for word in group) == tokens:
                if len(matches) == _MAX_CANDIDATES:
                    msg = "spatial_count"
                    raise LimitError(msg, "too many matching field anchors")
                matches.append(group)
        return tuple(matches)

    def _candidates(  # noqa: C901 - bound, group, and score the same source spans.
        self,
        spec: FieldSpec,
        anchor: tuple[SpatialWord, ...],
        label_ids: set[int],
    ) -> tuple[FieldCandidate, ...]:
        abox = _bounds(anchor)
        height = max(1.0, abox[3] - abox[1])
        if spec.direction == "right":
            search = (abox[2], abox[1] - height, abox[2] + spec.max_distance, abox[3] + height)
        else:
            search = (abox[0] - height, abox[3], abox[2] + spec.max_distance, abox[3] + spec.max_distance)
        words = self.select(search)
        if spec.region is not None:
            words = tuple(word for word in words if _contains(spec.region, word))
        barriers = tuple(word.bbox for word in words if word.id in label_ids)
        groups: list[list[SpatialWord]] = []
        for word in words:
            if word.id in label_ids:
                # Another declared label terminates its own line's candidate.
                groups.append([])
                continue
            if (
                not groups
                or not groups[-1]
                or word.line != groups[-1][-1].line
                or (word.bbox[0] - groups[-1][-1].bbox[2] > height * 2)
            ):
                groups.append([])
            groups[-1].append(word)
        result: list[FieldCandidate] = []
        for group in groups:
            if not group:
                continue
            box = _bounds(group)
            content = _text(group)
            if not _type_matches(content, spec.value_type) or _crosses_label(abox, box, barriers, spec.direction):
                continue
            if len(result) == _MAX_CANDIDATES:
                msg = "spatial_count"
                raise LimitError(msg, "too many placement candidates")
            if spec.direction == "right":
                gap = max(0.0, box[0] - abox[2]) / height
                cross = abs((box[1] + box[3] - abox[1] - abox[3]) / 2) / height
            else:
                gap = max(0.0, box[1] - abox[3]) / height
                cross = abs(box[0] - abox[0]) / height
            features = (
                1 / (1 + gap),
                1 / (1 + cross),
                float(spec.value_type != "any"),
                min(len(group), 8) / 8,
                float(spec.direction == "below"),
                min(height, box[3] - box[1]) / max(height, box[3] - box[1]),
            )
            result.append(_candidate(tuple(group), anchor, features))
        return tuple(result)

    def grid(self, *, columns: Sequence[float], rows: Sequence[float]) -> SpatialTable:
        """Extract an explicit display-space grid without table detection or models.

        Supply every boundary, including outer edges. Words crossing a boundary
        are assigned by center; inspect their source boxes when that is unsuitable.
        """
        xs, ys = _edges(columns), _edges(rows)
        count = (len(xs) - 1) * (len(ys) - 1)
        if count > _MAX_CELLS:
            msg = "spatial_count"
            raise LimitError(msg, "explicit grid exceeds 4096 cells")
        groups: list[list[SpatialWord]] = [[] for _ in range(count)]
        for word in self.select((xs[0], ys[0], xs[-1], ys[-1])):
            col = bisect.bisect_right(xs, (word.bbox[0] + word.bbox[2]) / 2) - 1
            row = bisect.bisect_right(ys, (word.bbox[1] + word.bbox[3]) / 2) - 1
            groups[row * (len(xs) - 1) + col].append(word)
        cells = []
        for index, group in enumerate(groups):
            row, col = divmod(index, len(xs) - 1)
            cells.append(
                SpatialCell(
                    index,
                    row,
                    col,
                    1,
                    1,
                    (xs[col], ys[row], xs[col + 1], ys[row + 1]),
                    _text(group),
                    tuple(word.id for word in group),
                )
            )
        return SpatialTable(
            (xs[0], ys[0], xs[-1], ys[-1]), len(ys) - 1, len(xs) - 1, tuple(cells), tuple(range(count)), "explicit"
        )


def _edges(values: Sequence[float]) -> tuple[float, ...]:
    edges = _bounded(values, _MAX_CELLS + 1, "grid boundaries")
    if (
        len(edges) < _MIN_EDGES
        or not all(math.isfinite(value) for value in edges)
        or any(a >= b for a, b in itertools.pairwise(edges))
    ):
        msg = "grid boundaries must be finite and strictly increasing"
        raise PdfError(msg)
    return edges


def _crosses_label(anchor: _BBox, value: _BBox, labels: tuple[_BBox, ...], direction: str) -> bool:
    """Prevent a field from reaching past another declared label into its value."""
    if direction == "right":
        return any(
            anchor[2] <= label[0] <= value[0] and min(label[3], value[3]) > max(label[1], value[1]) for label in labels
        )
    return any(
        anchor[3] <= label[1] <= value[1] and min(label[2], value[2]) > max(label[0], value[0]) for label in labels
    )


def _candidate(
    words: Sequence[SpatialWord], anchor: Sequence[SpatialWord], features: tuple[float, ...]
) -> FieldCandidate:
    return FieldCandidate(
        _text(words), _bounds(words), tuple(word.id for word in words), tuple(word.id for word in anchor), features
    )


def _type_matches(text: str, kind: _ValueType) -> bool:
    if kind == "number":
        return re.fullmatch(r"[($€£+\-]?\s*\d[\d,. ]*\)?%?", text.strip()) is not None
    if kind == "date":
        return re.fullmatch(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}", text.strip()) is not None
    return kind != "text" or any(char.isalpha() for char in text)


def _resolve(name: str, candidates: tuple[FieldCandidate, ...], model: PlacementModel | None) -> FieldResult:
    if not candidates:
        return FieldResult(name, "missing", None, ())
    if model is None:
        return FieldResult(
            name,
            "matched" if len(candidates) == 1 else "ambiguous",
            candidates[0] if len(candidates) == 1 else None,
            candidates,
        )
    ranked = tuple(
        sorted(
            (replace(candidate, score=model.score(candidate)) for candidate in candidates),
            key=lambda candidate: candidate.score or 0,
            reverse=True,
        )
    )
    best = ranked[0].score or 0
    second = ranked[1].score or 0 if len(ranked) > 1 else 0
    accepted = best >= model.threshold and best - second >= model.margin
    return FieldResult(name, "matched" if accepted else "ambiguous", ranked[0] if accepted else None, ranked)


def build_layout(
    width: float, height: float, blocks: Sequence[RawLayoutBlock], raw_tables: Sequence[RawLayoutTable], strategy: str
) -> PageLayout:
    """Materialize a bounded owned snapshot from the combined Rust interpretation."""
    words: list[SpatialWord] = []
    line_index = 0
    for _, lines in blocks:
        for _, _, source_words, direction, _ in lines:
            for bbox, text in source_words:
                if len(words) == _MAX_WORDS:
                    msg = "spatial_count"
                    raise LimitError(msg, "spatial snapshot exceeds 65536 words")
                words.append(SpatialWord(len(words), text, bbox, line_index, direction))
            line_index += 1
    y_order = tuple(sorted(((word.bbox[1] + word.bbox[3]) / 2, word.id) for word in words))
    layout = PageLayout(width, height, tuple(words), (), y_order)
    tables = tuple(_table(layout, raw, strategy) for raw in raw_tables)
    return replace(layout, tables=tables)


def _table(layout: PageLayout, raw: RawLayoutTable, strategy: str) -> SpatialTable:
    bbox, nr, nc, source, anchors, _ = raw
    words = layout.select(bbox)
    cell_words = _cell_words(layout, raw, words)
    direction = Counter(word.direction for word in words).most_common(1)
    dx, dy = direction[0][0] if direction else (1, 0)
    # Transform slot positions, keeping source cell IDs and display boxes intact.
    positions = [(row, col) for row in range(nr) for col in range(nc)]
    if abs(dy) > abs(dx):
        positions = [(nc - col - 1, row) if dy > 0 else (col, nr - row - 1) for row, col in positions]
        nr, nc = nc, nr
    elif dx < 0:
        positions = [(nr - row - 1, nc - col - 1) for row, col in positions]
    slots = [0] * len(anchors)
    membership: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for anchor, (row, col) in zip(anchors, positions, strict=True):
        slots[row * nc + col] = anchor
        membership[anchor].append((row, col))
    cells = []
    for index, cell in enumerate(source):
        if cell is None:
            continue
        box, text = cell
        members = membership[index]
        row, col = min(r for r, _ in members), min(c for _, c in members)
        cells.append(
            SpatialCell(
                index,
                row,
                col,
                max(r for r, _ in members) - row + 1,
                max(c for _, c in members) - col + 1,
                box,
                text,
                cell_words[index],
            )
        )
    return SpatialTable(bbox, nr, nc, tuple(cells), tuple(slots), strategy)


def _cell_words(
    layout: PageLayout,
    raw: RawLayoutTable,
    words: tuple[SpatialWord, ...],
) -> dict[int, tuple[int, ...]]:
    """Assign each word once through a complete native grid's anchor map."""
    _, rows, columns, cells, anchors, _ = raw
    xs = sorted({x for cell in cells if cell is not None for x in (cell[0][0], cell[0][2])})
    ys = sorted({y for cell in cells if cell is not None for y in (cell[0][1], cell[0][3])})
    if len(xs) != columns + 1 or len(ys) != rows + 1:
        # Text-detected cells need not share complete rectangular boundaries.
        return {
            index: tuple(word.id for word in layout.select(cell[0]))
            for index, cell in enumerate(cells)
            if cell is not None
        }
    groups: dict[int, list[int]] = {index: [] for index, cell in enumerate(cells) if cell is not None}
    for word in words:
        column = bisect.bisect_right(xs, (word.bbox[0] + word.bbox[2]) / 2) - 1
        row = bisect.bisect_right(ys, (word.bbox[1] + word.bbox[3]) / 2) - 1
        if 0 <= row < rows and 0 <= column < columns:
            groups[anchors[row * columns + column]].append(word.id)
    return {index: tuple(ids) for index, ids in groups.items()}
