//! Page Markdown assembly over the layout tuples produced by `extract`.
//!
//! This is a Rust port of `src/pdfust/_markdown.py` (single-page form) so the
//! Node binding produces the same Markdown as `Page.to_markdown()` without
//! Python. Keep the two in lockstep: the Node parity tests compare their output.

use std::collections::{BTreeSet, HashMap};

use crate::extract::BlockTuple;

type BBox = (f64, f64, f64, f64);
/// Span: `(bbox, text, size, origin, font, flags)`, as in `extract`.
type SpanRow = (BBox, String, f64, (f64, f64), String, i64);

/// Minimum size ratio relative to body text for a heading.
const HEADING_RATIO: f64 = 1.15;
const MAX_HEADING_LEVELS: usize = 4;
const SPACED_BULLETS: &str = "・•●○◦▪‣–—-*";
const TIGHT_BULLETS: &str = "・•●○◦▪‣";
const ITALIC: i64 = 2;
const BOLD: i64 = 16;

const NO_SPACE_SCRIPT_RANGES: [(u32, u32); 11] = [
    (0x0E00, 0x0E7F),
    (0x0E80, 0x0EFF),
    (0x1000, 0x109F),
    (0x1780, 0x17FF),
    (0x19E0, 0x19FF),
    (0x3000, 0x30FF),
    (0x3400, 0x9FFF),
    (0xA9E0, 0xA9FF),
    (0xAA60, 0xAA7F),
    (0xF900, 0xFAFF),
    (0xFF00, 0xFFEF),
];

/// A table ready for Markdown output: bbox, row-major cells, merged-cell anchors.
pub struct MarkdownTable {
    pub bbox: BBox,
    pub columns: usize,
    pub cells: Vec<Option<String>>,
    pub anchors: Vec<u32>,
}

/// Raised when escaped output would exceed the caller's budget.
#[derive(Debug)]
pub struct OutputLimit;

/// Python `str.isspace` for one character.
fn py_space(ch: char) -> bool {
    ch.is_whitespace() || ('\x1c'..='\x1f').contains(&ch)
}

/// Python `str.strip()`.
fn py_strip(text: &str) -> &str {
    text.trim_matches(py_space)
}

/// Python rounding to one decimal, as an integer count of tenths.
fn size_key(size: f64) -> i64 {
    let rounded: f64 = format!("{size:.1}").parse().unwrap_or(0.0);
    (rounded * 10.0).round() as i64
}

fn key_size(key: i64) -> f64 {
    format!("{}.{}", key / 10, (key % 10).abs())
        .parse::<f64>()
        .unwrap_or(0.0)
        * if key < 0 { -1.0 } else { 1.0 }
}

/// Insertion-ordered counter matching `collections.Counter.most_common(1)`.
#[derive(Default)]
struct Counter {
    entries: Vec<(i64, usize)>,
}

impl Counter {
    fn add(&mut self, key: i64, amount: usize) {
        if let Some(entry) = self.entries.iter_mut().find(|entry| entry.0 == key) {
            entry.1 += amount;
        } else {
            self.entries.push((key, amount));
        }
    }

    fn most_common(&self) -> Option<i64> {
        let mut best: Option<(i64, usize)> = None;
        for &(key, count) in &self.entries {
            if best.is_none_or(|(_, best_count)| count > best_count) {
                best = Some((key, count));
            }
        }
        best.map(|(key, _)| key)
    }
}

fn char_count(text: &str) -> usize {
    text.chars().count()
}

fn lines_of(blocks: &[BlockTuple]) -> Vec<(BBox, &Vec<SpanRow>, (f64, f64))> {
    blocks
        .iter()
        .flat_map(|block| block.1.iter())
        .map(|line| (line.0, &line.1, line.3))
        .collect()
}

fn inside(bbox: BBox, outer: BBox) -> bool {
    let center_x = (bbox.0 + bbox.2) * 0.5;
    let center_y = (bbox.1 + bbox.3) * 0.5;
    outer.0 <= center_x && center_x <= outer.2 && outer.1 <= center_y && center_y <= outer.3
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Orientation {
    Right,
    Down,
    Left,
    Up,
}

fn orientation_of((x, y): (f64, f64)) -> Orientation {
    if x.abs() >= y.abs() {
        if x >= 0.0 { Orientation::Right } else { Orientation::Left }
    } else if y >= 0.0 {
        Orientation::Down
    } else {
        Orientation::Up
    }
}

fn dominant_orientation(lines: &[(BBox, &Vec<SpanRow>, (f64, f64))]) -> Orientation {
    let mut totals: Vec<(Orientation, usize)> = Vec::new();
    for line in lines {
        let text: String = line.1.iter().map(|span| span.1.as_str()).collect();
        let weight = char_count(py_strip(&text)).max(1);
        let orientation = orientation_of(line.2);
        if let Some(entry) = totals.iter_mut().find(|entry| entry.0 == orientation) {
            entry.1 += weight;
        } else {
            totals.push((orientation, weight));
        }
    }
    let mut best: Option<(Orientation, usize)> = None;
    for &(orientation, count) in &totals {
        if best.is_none_or(|(_, best_count)| count > best_count) {
            best = Some((orientation, count));
        }
    }
    best.map_or(Orientation::Right, |(orientation, _)| orientation)
}

fn table_orientation(blocks: &[BlockTuple], bbox: BBox) -> Orientation {
    let lines = lines_of(blocks);
    let contained: Vec<_> = lines
        .iter()
        .filter(|line| inside(line.0, bbox))
        .cloned()
        .collect();
    if contained.is_empty() {
        dominant_orientation(&lines)
    } else {
        dominant_orientation(&contained)
    }
}

fn escape_cell(value: &Option<String>) -> String {
    match value {
        None => String::new(),
        Some(text) => text
            .replace('\\', "\\\\")
            .replace('|', "\\|")
            .replace('\n', "<br>"),
    }
}

fn fill_merged_cells(rows: &mut [Vec<Option<String>>], anchors: &[u32]) {
    let columns = rows.first().map_or(0, Vec::len);
    if columns > 0 && anchors.len() == rows.len() * columns {
        for (index, &anchor) in anchors.iter().enumerate() {
            let anchor = anchor as usize;
            if anchor >= anchors.len() {
                continue;
            }
            let (row, column) = (index / columns, index % columns);
            let (anchor_row, anchor_column) = (anchor / columns, anchor % columns);
            if rows[row][column].is_none() {
                rows[row][column] = rows[anchor_row][anchor_column].clone();
            }
        }
        return;
    }
    for row_index in 0..rows.len() {
        for column_index in 0..rows[row_index].len() {
            if rows[row_index][column_index].is_some() {
                continue;
            }
            let above = if row_index > 0 {
                rows[row_index - 1][column_index].clone()
            } else {
                None
            };
            let left = if column_index > 0 {
                rows[row_index][column_index - 1].clone()
            } else {
                None
            };
            rows[row_index][column_index] = above.or(left);
        }
    }
}

fn transpose(rows: &[Vec<Option<String>>]) -> Vec<Vec<Option<String>>> {
    let columns = rows.first().map_or(0, Vec::len);
    (0..columns)
        .map(|column| rows.iter().map(|row| row[column].clone()).collect())
        .collect()
}

fn orient_rows(rows: Vec<Vec<Option<String>>>, orientation: Orientation) -> Vec<Vec<Option<String>>> {
    match orientation {
        Orientation::Right => rows,
        Orientation::Down => {
            let mut columns = transpose(&rows);
            columns.reverse();
            columns
        }
        Orientation::Left => rows
            .into_iter()
            .rev()
            .map(|mut row| {
                row.reverse();
                row
            })
            .collect(),
        Orientation::Up => {
            let mut reversed = rows;
            reversed.reverse();
            transpose(&reversed)
        }
    }
}

fn table_to_markdown(
    table: &MarkdownTable,
    orientation: Orientation,
    max_size: Option<usize>,
) -> Result<String, OutputLimit> {
    if table.columns == 0 || table.cells.is_empty() {
        return Ok(String::new());
    }
    let mut rows: Vec<Vec<Option<String>>> = table
        .cells
        .chunks(table.columns)
        .map(<[Option<String>]>::to_vec)
        .collect();
    fill_merged_cells(&mut rows, &table.anchors);
    let rows = orient_rows(rows, orientation);
    let header_columns = rows[0].len();
    let mut estimate = rows.len() + 4 + header_columns.saturating_sub(1) * 3 + header_columns * 3;
    for row in &rows {
        estimate += 4 + row.len().saturating_sub(1) * 3;
        for cell in row.iter().flatten() {
            estimate += cell.len();
        }
    }
    if max_size.is_some_and(|limit| estimate > limit) {
        return Err(OutputLimit);
    }
    let mut rendered = Vec::with_capacity(rows.len() + 1);
    rendered.push(format!(
        "| {} |",
        rows[0].iter().map(escape_cell).collect::<Vec<_>>().join(" | ")
    ));
    rendered.push(format!(
        "| {} |",
        rows[0].iter().map(|_| "---").collect::<Vec<_>>().join(" | ")
    ));
    for row in &rows[1..] {
        rendered.push(format!(
            "| {} |",
            row.iter().map(escape_cell).collect::<Vec<_>>().join(" | ")
        ));
    }
    Ok(rendered.join("\n"))
}

fn collect_sizes(blocks: &[BlockTuple], excluded: &[BBox]) -> Counter {
    let mut counter = Counter::default();
    for block in blocks {
        for line in &block.1 {
            if excluded.iter().any(|bbox| inside(line.0, *bbox)) {
                continue;
            }
            for span in &line.1 {
                counter.add(size_key(span.2), char_count(&span.1));
            }
        }
    }
    counter
}

fn heading_levels(counter: &Counter) -> HashMap<i64, usize> {
    let Some(body) = counter.most_common() else {
        return HashMap::new();
    };
    let body_size = key_size(body);
    let mut bigger: Vec<i64> = counter
        .entries
        .iter()
        .map(|entry| entry.0)
        .filter(|&key| key_size(key) > body_size * HEADING_RATIO)
        .collect();
    bigger.sort_unstable_by(|left, right| right.cmp(left));
    bigger
        .into_iter()
        .enumerate()
        .map(|(rank, key)| (key, (rank + 1).min(MAX_HEADING_LEVELS)))
        .collect()
}

fn joins_without_space(ch: char) -> bool {
    let code = ch as u32;
    NO_SPACE_SCRIPT_RANGES
        .iter()
        .any(|&(low, high)| low <= code && code <= high)
}

fn join_lines(lines: &[String]) -> String {
    let Some(first) = lines.first() else {
        return String::new();
    };
    let mut out = first.clone();
    let mut previous = first;
    for line in &lines[1..] {
        let glue = match (previous.chars().next_back(), line.chars().next()) {
            (Some(left), Some(right)) => joins_without_space(left) && joins_without_space(right),
            _ => false,
        };
        if !glue {
            out.push(' ');
        }
        out.push_str(line);
        previous = line;
    }
    out
}

fn span_markdown(span: &SpanRow) -> String {
    let text = span.1.as_str();
    let flags = span.5;
    let bold = flags & BOLD != 0;
    let italic = flags & ITALIC != 0;
    let core = py_strip(text);
    if core.is_empty() || !(bold || italic) {
        return text.to_owned();
    }
    let marker = if bold && italic {
        "***"
    } else if bold {
        "**"
    } else {
        "*"
    };
    let lead_len = text.len() - text.trim_start_matches(py_space).len();
    let trail_start = text.trim_end_matches(py_space).len();
    format!(
        "{}{marker}{core}{marker}{}",
        &text[..lead_len],
        &text[trail_start..]
    )
}

fn line_markdown(spans: &[SpanRow]) -> String {
    let joined: String = spans.iter().map(span_markdown).collect();
    py_strip(&joined).to_owned()
}

fn line_size_key(spans: &[SpanRow]) -> Option<i64> {
    let mut counter = Counter::default();
    for span in spans {
        counter.add(size_key(span.2), char_count(&span.1));
    }
    counter.most_common()
}

fn normalize_list_item(text: &str) -> Option<String> {
    let mut chars = text.chars();
    let first = chars.next()?;
    let second = chars.clone().next();
    if SPACED_BULLETS.contains(first) && matches!(second, Some(' ' | '　')) {
        let rest: String = chars.skip(1).collect();
        return Some(format!("- {}", rest.trim_start_matches([' ', '　'])));
    }
    if TIGHT_BULLETS.contains(first) {
        let rest: String = chars.collect();
        return Some(format!("- {}", rest.trim_start_matches([' ', '　'])));
    }
    // ^(\d{1,3})[.)][ 　]+
    let digits = text.chars().take_while(char::is_ascii_digit).count();
    if (1..=3).contains(&digits) {
        let after = &text[digits..];
        let mut rest = after.chars();
        if matches!(rest.next(), Some('.' | ')')) {
            let remainder = &after[1..];
            let stripped = remainder.trim_start_matches([' ', '　']);
            if stripped.len() < remainder.len() {
                return Some(format!("{}. {stripped}", &text[..digits]));
            }
        }
    }
    None
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Kind {
    Heading,
    ListItem,
    Paragraph,
    Table,
}

fn classify_line(
    spans: &[SpanRow],
    levels: &HashMap<i64, usize>,
    override_text: Option<&str>,
) -> Option<(Kind, String)> {
    let text = match override_text {
        None => {
            let joined: String = spans.iter().map(|span| span.1.as_str()).collect();
            py_strip(&joined).to_owned()
        }
        Some(value) => py_strip(value).to_owned(),
    };
    if text.is_empty() {
        return None;
    }
    if let Some(level) = line_size_key(spans).and_then(|key| levels.get(&key)) {
        return Some((Kind::Heading, format!("{} {text}", "#".repeat(*level))));
    }
    if let Some(item) = normalize_list_item(&text) {
        return Some((Kind::ListItem, item));
    }
    let body = if override_text.is_none() {
        line_markdown(spans)
    } else {
        text
    };
    Some((Kind::Paragraph, body))
}

type WordLines = HashMap<(usize, usize), Vec<(BBox, String)>>;

fn word_lines(words: &[BlockTuple]) -> WordLines {
    let mut map: WordLines = HashMap::new();
    for (block_index, block) in words.iter().enumerate() {
        for (line_index, line) in block.1.iter().enumerate() {
            map.entry((block_index, line_index)).or_default().extend(
                line.2
                    .iter()
                    .map(|word| (word.0, word.1.clone())),
            );
        }
    }
    map
}

struct Events {
    at: HashMap<usize, Vec<usize>>,
    memberships: Vec<BTreeSet<usize>>,
    residuals: HashMap<usize, (String, String)>,
}

fn geometric_event_position(
    lines: &[(BBox, &Vec<SpanRow>, (f64, f64))],
    bbox: BBox,
    orientation: Orientation,
) -> usize {
    let inline = match orientation {
        Orientation::Right => (1.0, 0.0),
        Orientation::Down => (0.0, 1.0),
        Orientation::Left => (-1.0, 0.0),
        Orientation::Up => (0.0, -1.0),
    };
    let block = (-inline.1, inline.0);
    let center = ((bbox.0 + bbox.2) * 0.5, (bbox.1 + bbox.3) * 0.5);
    let projection = center.0 * block.0 + center.1 * block.1;
    lines
        .iter()
        .position(|line| {
            (line.0.0 + line.0.2) * 0.5 * block.0 + (line.0.1 + line.0.3) * 0.5 * block.1
                >= projection
        })
        .unwrap_or(lines.len())
}

fn table_events(
    blocks: &[BlockTuple],
    tables: &[MarkdownTable],
    words: Option<&[BlockTuple]>,
) -> Events {
    let lines = lines_of(blocks);
    let mut positions: HashMap<(usize, usize), usize> = HashMap::new();
    let mut position = 0usize;
    for (block_index, block) in blocks.iter().enumerate() {
        for line_index in 0..block.1.len() {
            positions.insert((block_index, line_index), position);
            position += 1;
        }
    }
    let line_words = words.map(word_lines).unwrap_or_default();
    let mut memberships: Vec<BTreeSet<usize>> = vec![BTreeSet::new(); lines.len()];
    let mut at: HashMap<usize, Vec<usize>> = HashMap::new();
    let page_orientation = dominant_orientation(&lines);
    for (table_index, table) in tables.iter().enumerate() {
        let mut contained: Vec<usize> = if words.is_some() {
            let mut set = BTreeSet::new();
            for (key, entries) in &line_words {
                if let Some(&line_position) = positions.get(key)
                    && entries.iter().any(|word| inside(word.0, table.bbox))
                {
                    set.insert(line_position);
                }
            }
            set.into_iter().collect()
        } else {
            lines
                .iter()
                .enumerate()
                .filter(|(_, line)| inside(line.0, table.bbox))
                .map(|(index, _)| index)
                .collect()
        };
        contained.sort_unstable();
        for &index in &contained {
            memberships[index].insert(table_index);
        }
        let slot = contained
            .first()
            .copied()
            .unwrap_or_else(|| geometric_event_position(&lines, table.bbox, page_orientation));
        at.entry(slot).or_default().push(table_index);
    }
    for indices in at.values_mut() {
        indices.sort_by(|&left, &right| {
            let (a, b) = (tables[left].bbox, tables[right].bbox);
            (a.1, a.0)
                .partial_cmp(&(b.1, b.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        });
    }
    let mut residuals = HashMap::new();
    for (block_index, block) in blocks.iter().enumerate() {
        for (line_index, line) in block.1.iter().enumerate() {
            let position = positions[&(block_index, line_index)];
            if memberships[position].is_empty() {
                continue;
            }
            let bboxes: Vec<BBox> = memberships[position]
                .iter()
                .map(|&index| tables[index].bbox)
                .collect();
            let direction = line.3;
            let mut table_start = f64::INFINITY;
            for bbox in &bboxes {
                for corner_x in [bbox.0, bbox.2] {
                    for corner_y in [bbox.1, bbox.3] {
                        table_start =
                            table_start.min(corner_x * direction.0 + corner_y * direction.1);
                    }
                }
            }
            let mut before = Vec::new();
            let mut after = Vec::new();
            if let Some(entries) = line_words.get(&(block_index, line_index)) {
                for (word_bbox, text) in entries {
                    if bboxes.iter().any(|bbox| inside(*word_bbox, *bbox)) {
                        continue;
                    }
                    let center_x = (word_bbox.0 + word_bbox.2) * 0.5;
                    let center_y = (word_bbox.1 + word_bbox.3) * 0.5;
                    if center_x * direction.0 + center_y * direction.1 < table_start {
                        before.push(text.clone());
                    } else {
                        after.push(text.clone());
                    }
                }
            }
            residuals.insert(position, (join_lines(&before), join_lines(&after)));
        }
    }
    Events {
        at,
        memberships,
        residuals,
    }
}

struct Builder {
    entries: Vec<(Kind, String)>,
    paragraph: Vec<String>,
}

impl Builder {
    fn flush_paragraph(&mut self) {
        if self.paragraph.is_empty() {
            return;
        }
        let text = join_lines(&self.paragraph);
        self.entries.push((Kind::Paragraph, text));
        self.paragraph.clear();
    }

    fn append_classified(&mut self, classified: Option<(Kind, String)>) {
        match classified {
            Some((Kind::Paragraph, text)) => self.paragraph.push(text),
            Some((kind, text)) => {
                self.flush_paragraph();
                self.entries.push((kind, text));
            }
            None => {}
        }
    }

    fn append_tables(&mut self, rendered: &[String], indices: &[usize]) {
        self.flush_paragraph();
        for &index in indices {
            if !rendered[index].is_empty() {
                self.entries.push((Kind::Table, rendered[index].clone()));
            }
        }
    }

    fn render(mut self) -> String {
        self.flush_paragraph();
        let mut out = String::new();
        let mut previous: Option<Kind> = None;
        for (kind, text) in self.entries {
            if let Some(last) = previous {
                out.push_str(if kind == Kind::ListItem && last == Kind::ListItem {
                    "\n"
                } else {
                    "\n\n"
                });
            }
            out.push_str(&text);
            previous = Some(kind);
        }
        out
    }
}

/// Convert one page to Markdown.
///
/// `blocks` is the span-bearing layout; `words` is the word layout and is only
/// needed (and only used) when `tables` is non-empty. Heading sizes are inferred
/// from this page alone, as in `Page.to_markdown()`.
pub fn page_markdown(
    blocks: &[BlockTuple],
    tables: &[MarkdownTable],
    words: Option<&[BlockTuple]>,
    max_size: Option<usize>,
) -> Result<String, OutputLimit> {
    let bboxes: Vec<BBox> = tables.iter().map(|table| table.bbox).collect();
    let levels = heading_levels(&collect_sizes(blocks, &bboxes));
    let mut rendered = Vec::with_capacity(tables.len());
    let mut budget_used = 0usize;
    for table in tables {
        let remaining = max_size.map(|limit| limit.saturating_sub(budget_used));
        let markdown = table_to_markdown(table, table_orientation(blocks, table.bbox), remaining)?;
        budget_used += markdown.len();
        rendered.push(markdown);
    }
    let events = table_events(blocks, tables, if tables.is_empty() { None } else { words });
    let mut builder = Builder {
        entries: Vec::new(),
        paragraph: Vec::new(),
    };
    let mut position = 0usize;
    for block in blocks {
        for line in &block.1 {
            let spans = &line.1;
            let pending = events.at.get(&position);
            if !events.memberships[position].is_empty() {
                let (before, after) = events
                    .residuals
                    .get(&position)
                    .cloned()
                    .unwrap_or_default();
                builder.append_classified(classify_line(spans, &levels, Some(&before)));
                if let Some(indices) = pending {
                    builder.append_tables(&rendered, indices);
                }
                builder.append_classified(classify_line(spans, &levels, Some(&after)));
                position += 1;
                continue;
            }
            if let Some(indices) = pending {
                builder.append_tables(&rendered, indices);
            }
            builder.append_classified(classify_line(spans, &levels, None));
            position += 1;
        }
        builder.flush_paragraph();
    }
    if let Some(indices) = events.at.get(&position) {
        builder.append_tables(&rendered, indices);
    }
    let output = builder.render();
    if max_size.is_some_and(|limit| output.len() > limit) {
        return Err(OutputLimit);
    }
    Ok(output)
}

/// Fraction of the smaller bbox covered by the intersection of two bboxes.
pub fn overlap_ratio(left: BBox, right: BBox) -> f64 {
    let width = (left.2.min(right.2) - left.0.max(right.0)).max(0.0);
    let height = (left.3.min(right.3) - left.1.max(right.1)).max(0.0);
    let smaller = ((left.2 - left.0) * (left.3 - left.1)).min((right.2 - right.0) * (right.3 - right.1));
    if smaller <= 0.0 { 0.0 } else { width * height / smaller }
}
