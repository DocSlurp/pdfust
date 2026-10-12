//! Plain-Rust document API for the Node binding (`bindings/node`).
//!
//! This module is a child of `document` so it can drive the same engine the
//! Python wheel uses, and it exposes owned, binding-neutral structs with no
//! PyO3 or N-API types. Every page index in this API is zero-based.

use super::*;

use std::collections::{BTreeSet, HashMap};

use hayro::hayro_interpret::font::Glyph;
use hayro::hayro_interpret::{
    BlendMode, ClipPath, Context, Device, GlyphDrawMode, Image, Paint, PathDrawMode,
    SoftMask, TransformExt, interpret_page,
};
use kurbo::{Affine, Point, Rect};

type BBox = (f64, f64, f64, f64);

/// Error with a stable machine-readable code.
///
/// Codes: `PDF_LOCKED` (password needed or wrong), `PDF_LIMIT` (a resource limit,
/// see `limit`), `PDF_ERROR` (malformed or unsupported input), `INVALID_ARGUMENT`.
#[derive(Debug, Clone)]
pub struct NativeError {
    pub code: &'static str,
    pub limit: Option<&'static str>,
    pub message: String,
}

impl From<PyErr> for NativeError {
    fn from(error: PyErr) -> Self {
        let code = match error.class {
            "PasswordError" => "PDF_LOCKED",
            "LimitError" => "PDF_LIMIT",
            "PyValueError" | "PyTypeError" => "INVALID_ARGUMENT",
            _ => "PDF_ERROR",
        };
        Self {
            code,
            limit: error.code,
            message: error.message,
        }
    }
}

impl NativeError {
    pub fn invalid(message: impl Into<String>) -> Self {
        Self {
            code: "INVALID_ARGUMENT",
            limit: None,
            message: message.into(),
        }
    }
}

pub type NativeResult<T> = Result<T, NativeError>;

fn py() -> Python<'static> {
    Python::none()
}

/// Optional resource limits applied while opening and interpreting.
#[derive(Debug, Clone, Default)]
pub struct NativeLimits {
    pub max_decompressed_size: Option<usize>,
    pub max_page_content_size: Option<usize>,
    pub max_file_size: Option<usize>,
    pub max_pages: Option<usize>,
    pub max_objects: Option<usize>,
    pub max_total_decompressed_size: Option<usize>,
    pub max_object_depth: Option<usize>,
    pub max_text_size: Option<usize>,
    pub max_interpretation_size: Option<usize>,
    pub max_text_glyphs: Option<usize>,
}

impl NativeLimits {
    /// Conservative profile for untrusted uploads (mirrors `DocumentLimits.web()`).
    pub fn web() -> Self {
        let mib = 1024 * 1024;
        Self {
            max_file_size: Some(10 * mib),
            max_pages: Some(200),
            max_objects: Some(100_000),
            max_decompressed_size: Some(64 * mib),
            max_page_content_size: Some(10 * mib),
            max_total_decompressed_size: Some(128 * mib),
            max_object_depth: Some(64),
            max_text_size: Some(mib),
            max_interpretation_size: Some(64 * mib),
            max_text_glyphs: Some(65_536),
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct NativeMetadata {
    pub title: Option<String>,
    pub author: Option<String>,
    pub subject: Option<String>,
    pub keywords: Option<String>,
    pub creator: Option<String>,
    pub producer: Option<String>,
    pub creation_date: Option<String>,
    pub modification_date: Option<String>,
    pub encrypted: bool,
    pub permissions: Option<Vec<String>>,
    pub pdf_version: String,
    pub repaired: bool,
}

#[derive(Debug, Clone)]
pub struct NativeFont {
    pub name: String,
    pub kind: String,
    pub embedded: bool,
    pub has_to_unicode: bool,
    pub is_type3: bool,
}

#[derive(Debug, Clone)]
pub struct NativeSpan {
    pub text: String,
    pub bbox: BBox,
    pub font: String,
    pub size: f64,
    pub render_mode: u8,
    pub invisible: bool,
    pub unmapped: u32,
}

#[derive(Debug, Clone, Default)]
pub struct NativeGlyphStats {
    pub glyphs: u32,
    pub invisible: u32,
    pub stroke: u32,
    pub unmapped: u32,
    pub fonts: u32,
}

#[derive(Debug, Clone)]
pub struct NativeImage {
    pub index: u32,
    pub bbox: BBox,
    pub width_px: u32,
    pub height_px: u32,
    pub effective_dpi: f64,
}

#[derive(Debug, Clone, Default)]
pub struct NativeDrawings {
    pub line_count: u32,
    pub rect_count: u32,
    pub long_rule_count: u32,
    pub path_count: u32,
    pub vector_area: f64,
}

#[derive(Debug, Clone)]
pub struct NativeWidget {
    pub kind: String,
    pub name: Option<String>,
    pub value: Option<String>,
    pub bbox: BBox,
}

#[derive(Debug, Clone)]
pub struct NativeAnnotation {
    pub subtype: String,
    pub contents: Option<String>,
    pub uri: Option<String>,
    pub bbox: BBox,
}

#[derive(Debug, Clone)]
pub struct NativeLink {
    pub kind: String,
    pub uri: Option<String>,
    /// Zero-based destination page for GoTo links.
    pub dest_page: Option<u32>,
    pub bbox: BBox,
}

#[derive(Debug, Clone)]
pub struct NativeTable {
    pub bbox: BBox,
    pub rows: Vec<Vec<String>>,
    pub row_count: u32,
    pub col_count: u32,
    pub confidence: f64,
    pub strategy: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ImageFormat {
    Png,
    Jpeg,
    Webp,
}

#[derive(Debug, Clone)]
pub struct NativeRender {
    pub dpi: Option<f64>,
    pub max_edge_px: Option<u32>,
    pub clip: Option<BBox>,
    pub format: ImageFormat,
    pub gray: bool,
    /// JPEG quality 1..=100.
    pub quality: u8,
}

impl Default for NativeRender {
    fn default() -> Self {
        Self {
            dpi: None,
            max_edge_px: None,
            clip: None,
            format: ImageFormat::Png,
            gray: false,
            quality: 85,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TableStrategy {
    Lines,
    Text,
    None,
}

impl TableStrategy {
    pub fn parse(value: Option<&str>) -> NativeResult<Self> {
        match value {
            None | Some("lines") => Ok(Self::Lines),
            Some("text") => Ok(Self::Text),
            Some("none") => Ok(Self::None),
            Some(other) => Err(NativeError::invalid(format!(
                "tableStrategy must be 'lines', 'text' or 'none': {other:?}"
            ))),
        }
    }
}

/// Maximum Markdown/text output accepted for one page.
const MAX_PAGE_OUTPUT: usize = 64 * 1024 * 1024;

/// Document handle. One document is used by one task at a time.
pub struct NativeDoc {
    doc: _Document,
}

impl NativeDoc {
    pub fn open_path(
        path: &str,
        password: Option<&str>,
        limits: &NativeLimits,
    ) -> NativeResult<Self> {
        Self::open_with(password, |pw| {
            _Document::load(
                py(),
                path,
                pw,
                limits.max_decompressed_size,
                limits.max_page_content_size,
                limits.max_file_size,
                limits.max_pages,
                limits.max_objects,
                limits.max_total_decompressed_size,
                limits.max_object_depth,
                limits.max_text_size,
                limits.max_interpretation_size,
                limits.max_text_glyphs,
            )
        })
    }

    pub fn open_bytes(
        data: &[u8],
        password: Option<&str>,
        limits: &NativeLimits,
    ) -> NativeResult<Self> {
        Self::open_with(password, |pw| {
            _Document::load_bytes(
                py(),
                data,
                pw,
                limits.max_decompressed_size,
                limits.max_page_content_size,
                limits.max_file_size,
                limits.max_pages,
                limits.max_objects,
                limits.max_total_decompressed_size,
                limits.max_object_depth,
                limits.max_text_size,
                limits.max_interpretation_size,
                limits.max_text_glyphs,
            )
        })
    }

    fn open_with(
        password: Option<&str>,
        load: impl Fn(Option<String>) -> PyResult<_Document>,
    ) -> NativeResult<Self> {
        let locked = || NativeError {
            code: "PDF_LOCKED",
            limit: None,
            message: "a password is required or incorrect".to_owned(),
        };
        let mut doc = load(None)?;
        if doc.is_encrypted() {
            let Some(password) = password else {
                return Err(locked());
            };
            doc = load(Some(password.to_owned()))?;
            if doc.is_encrypted() {
                return Err(locked());
            }
        }
        Ok(Self { doc })
    }

    fn page_number(&self, index: u32) -> NativeResult<u32> {
        let count = self.doc.page_count()?;
        if (index as usize) < count {
            Ok(index + 1)
        } else {
            Err(NativeError::invalid(format!(
                "page {index} is out of range (document has {count} pages)"
            )))
        }
    }

    pub fn page_count(&self) -> NativeResult<u32> {
        Ok(u32::try_from(self.doc.page_count()?).unwrap_or(u32::MAX))
    }

    pub fn take_warnings(&mut self) -> Vec<String> {
        self.doc.take_warnings()
    }

    pub fn metadata(&self) -> NativeResult<NativeMetadata> {
        let info = self.doc.get_metadata(py())?;
        let get = |key: &str| info.get(key).cloned();
        let encrypted = self.doc.was_encrypted();
        let permissions = self
            .doc
            .doc
            .encryption_state
            .as_ref()
            .map(|state| {
                state
                    .permissions()
                    .iter_names()
                    .map(|(name, _)| name.to_ascii_lowercase())
                    .collect()
            });
        Ok(NativeMetadata {
            title: get("Title"),
            author: get("Author"),
            subject: get("Subject"),
            keywords: get("Keywords"),
            creator: get("Creator"),
            producer: get("Producer"),
            creation_date: get("CreationDate"),
            modification_date: get("ModDate"),
            encrypted,
            permissions,
            pdf_version: self.doc.version(),
            repaired: self.doc.is_repaired(),
        })
    }

    /// Whether the file carries JavaScript (document actions, name tree, or widgets).
    pub fn has_java_script(&self) -> bool {
        let doc = &self.doc.doc;
        doc.objects.values().any(|object| {
            let dict = match object {
                Object::Dictionary(dict) => dict,
                Object::Stream(stream) => &stream.dict,
                _ => return false,
            };
            dict.has(b"JS")
                || matches!(dict.get(b"S").and_then(Object::as_name), Ok(b"JavaScript"))
        })
    }

    /// Optional content groups (layers) with their default visibility.
    pub fn optional_content(&self) -> Vec<(String, bool)> {
        let doc = &self.doc.doc;
        let Ok(catalog) = doc.catalog() else {
            return Vec::new();
        };
        let Some(properties) = catalog
            .get(b"OCProperties")
            .ok()
            .map(|object| deref_object(doc, object))
            .and_then(|object| object.as_dict().ok())
        else {
            return Vec::new();
        };
        let ids = |key: &[u8]| -> Vec<ObjectId> {
            properties
                .get(key)
                .ok()
                .map(|object| deref_object(doc, object))
                .and_then(|object| object.as_array().ok())
                .map(|items| {
                    items
                        .iter()
                        .filter_map(|item| item.as_reference().ok())
                        .collect()
                })
                .unwrap_or_default()
        };
        let default = properties
            .get(b"D")
            .ok()
            .map(|object| deref_object(doc, object))
            .and_then(|object| object.as_dict().ok());
        let ids_of = |key: &[u8]| -> Vec<ObjectId> {
            default
                .and_then(|default| default.get(key).ok())
                .map(|object| deref_object(doc, object))
                .and_then(|object| object.as_array().ok())
                .map(|items| {
                    items
                        .iter()
                        .filter_map(|item| item.as_reference().ok())
                        .collect()
                })
                .unwrap_or_default()
        };
        let base_off = default
            .and_then(|default| default.get(b"BaseState").ok())
            .and_then(|object| object.as_name().ok())
            == Some(b"OFF");
        let off = ids_of(b"OFF");
        let on = ids_of(b"ON");
        ids(b"OCGs")
            .into_iter()
            .map(|id| {
                let name = doc
                    .get_object(id)
                    .and_then(Object::as_dict)
                    .ok()
                    .and_then(|dict| dict.get(b"Name").ok())
                    .map(|object| deref_object(doc, object))
                    .and_then(|object| decode_text_string(object).ok())
                    .unwrap_or_default();
                let visible = if base_off {
                    on.contains(&id)
                } else {
                    !off.contains(&id)
                };
                (name, visible)
            })
            .collect()
    }

    /// Embedded file attachments as `(name, decoded size)`.
    pub fn attachments(&self) -> NativeResult<Vec<(String, u64)>> {
        let names = self.doc.embfile_names(py())?;
        let mut out = Vec::with_capacity(names.len());
        for name in names {
            let size = self
                .doc
                .embfile_get(py(), &name, Some(DEFAULT_MAX_EMBEDDED_FILE_SIZE))
                .map(|bytes| bytes.len() as u64)
                .unwrap_or(0);
            out.push((name, size));
        }
        Ok(out)
    }

    /// Fonts referenced by a page's resources (or by every page when `page` is `None`).
    pub fn fonts(&self, page: Option<u32>) -> NativeResult<Vec<NativeFont>> {
        let doc = &self.doc.doc;
        let pages: Vec<u32> = match page {
            Some(index) => vec![self.page_number(index)?],
            None => (1..=u32::try_from(self.doc.page_count()?).unwrap_or(0)).collect(),
        };
        let mut seen = BTreeSet::new();
        let mut fonts = Vec::new();
        for number in pages {
            let page_id = self.doc.page_id(number)?;
            let resources = self.doc.resolve_page_attr(page_id, b"Resources")?;
            if let Some(Object::Dictionary(resources)) = resources {
                collect_fonts(doc, &resources, 0, &mut seen, &mut fonts);
            }
        }
        Ok(fonts)
    }

    pub fn size(&mut self, index: u32) -> NativeResult<(f64, f64, u16)> {
        let number = self.page_number(index)?;
        let rotation = self.doc.get_page_rotation(number)?;
        let pdf = self.doc.hayro_view()?;
        let page = &pdf.pages()[index as usize];
        let (width, height) = page.render_dimensions();
        let rotation = match rotation.rem_euclid(360) / 90 * 90 {
            90 => 90,
            180 => 180,
            270 => 270,
            _ => 0,
        };
        Ok((f64::from(width), f64::from(height), rotation))
    }

    pub fn text(&mut self, index: u32) -> NativeResult<String> {
        let number = self.page_number(index)?;
        Ok(self.doc.extract_text(py(), vec![number])?)
    }

    /// Markdown for one page. Heading sizes are inferred from this page alone.
    pub fn markdown(&mut self, index: u32, strategy: TableStrategy) -> NativeResult<String> {
        let number = self.page_number(index)?;
        let settings = self.doc.interpreter_settings();
        let _ = settings;
        let (_, _, blocks) = self.doc.extract_layout(py(), number, true, false)?;
        let mut tables = self.markdown_tables(number, strategy)?;
        let words = if tables.is_empty() {
            None
        } else {
            Some(self.doc.extract_layout(py(), number, false, true)?.2)
        };
        let tables: Vec<crate::markdown::MarkdownTable> = tables
            .drain(..)
            .map(|table| crate::markdown::MarkdownTable {
                bbox: table.0,
                columns: table.2 as usize,
                cells: table.3.into_iter().map(|cell| cell.map(|c| c.1)).collect(),
                anchors: table.4,
            })
            .collect();
        crate::markdown::page_markdown(&blocks, &tables, words.as_deref(), Some(MAX_PAGE_OUTPUT))
            .map_err(|_| NativeError {
                code: "PDF_LIMIT",
                limit: Some("markdown_output_size"),
                message: format!("Markdown exceeds the {MAX_PAGE_OUTPUT}-byte output limit"),
            })
    }

    fn markdown_tables(
        &mut self,
        number: u32,
        strategy: TableStrategy,
    ) -> NativeResult<Vec<crate::extract::TableTuple>> {
        if strategy == TableStrategy::None {
            return Ok(Vec::new());
        }
        let mut tables = self.doc.find_tables(py(), number, "lines", None)?;
        if strategy == TableStrategy::Text {
            for candidate in self.doc.find_tables(py(), number, "text", None)? {
                if tables
                    .iter()
                    .all(|table| crate::markdown::overlap_ratio(candidate.0, table.0) < 0.5)
                {
                    tables.push(candidate);
                }
            }
        }
        tables.sort_by(|left, right| {
            (left.0.1, left.0.0)
                .partial_cmp(&(right.0.1, right.0.0))
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        Ok(tables)
    }

    pub fn tables(&mut self, index: u32, strategy: TableStrategy) -> NativeResult<Vec<NativeTable>> {
        let number = self.page_number(index)?;
        let name = match strategy {
            TableStrategy::Text => "text",
            _ => "lines",
        };
        let raw = self.doc.find_tables(py(), number, name, None)?;
        Ok(raw
            .into_iter()
            .map(|table| {
                let columns = (table.2 as usize).max(1);
                let values: Vec<String> = table
                    .3
                    .into_iter()
                    .map(|cell| cell.map(|c| c.1).unwrap_or_default())
                    .collect();
                NativeTable {
                    bbox: table.0,
                    rows: values.chunks(columns).map(<[String]>::to_vec).collect(),
                    row_count: table.1,
                    col_count: table.2,
                    confidence: table.5.0,
                    strategy: name,
                }
            })
            .collect())
    }

    /// Text spans in reading order (one font and size each), annotated with the
    /// PDF text render mode taken from the page's glyphs. `unmapped` is always 0
    /// per span (glyphs without Unicode never reach the text); see `glyph_stats`.
    pub fn spans(&mut self, index: u32) -> NativeResult<Vec<NativeSpan>> {
        let number = self.page_number(index)?;
        let (_, _, blocks) = self.doc.extract_layout(py(), number, true, false)?;
        let (rows, _) = self.glyph_rows(index)?;
        // Bucket glyph origins by whole-point y so each span only scans nearby glyphs.
        let mut buckets: HashMap<i64, Vec<(f64, f64, &'static str)>> = HashMap::new();
        for row in &rows {
            buckets
                .entry(row.2.1.floor() as i64)
                .or_default()
                .push((row.2.0, row.2.1, row.9));
        }
        let mut spans = Vec::new();
        for block in &blocks {
            for line in &block.1 {
                for (bbox, text, size, _, font, _) in &line.1 {
                    let (mut invisible, mut stroke, mut total) = (0u32, 0u32, 0u32);
                    for bucket in (bbox.1.floor() as i64 - 1)..=(bbox.3.ceil() as i64 + 1) {
                        for &(x, y, mode) in buckets.get(&bucket).into_iter().flatten() {
                            if x >= bbox.0 - 1.0 && x <= bbox.2 + 1.0 && y >= bbox.1 - 1.0 && y <= bbox.3 + 1.0 {
                                total += 1;
                                match mode {
                                    "invisible" => invisible += 1,
                                    "stroke" => stroke += 1,
                                    _ => {}
                                }
                            }
                        }
                    }
                    let half = total / 2;
                    let (render_mode, hidden) = if total > 0 && invisible > half {
                        (3, true)
                    } else if total > 0 && stroke > half {
                        (1, false)
                    } else {
                        (0, false)
                    };
                    spans.push(NativeSpan {
                        text: text.clone(),
                        bbox: *bbox,
                        font: font.clone(),
                        size: *size,
                        render_mode,
                        invisible: hidden,
                        unmapped: 0,
                    });
                }
            }
        }
        Ok(spans)
    }

    /// Glyph-level counts for probes: invisible (Tr 3), stroked, unmapped, distinct fonts.
    pub fn glyph_stats(&mut self, index: u32) -> NativeResult<NativeGlyphStats> {
        let (rows, unmapped) = self.glyph_rows(index)?;
        let mut stats = NativeGlyphStats {
            unmapped: u32::try_from(unmapped).unwrap_or(u32::MAX),
            ..Default::default()
        };
        let mut fonts = BTreeSet::new();
        for row in &rows {
            stats.glyphs += 1;
            match row.9 {
                "invisible" => stats.invisible += 1,
                "stroke" => stats.stroke += 1,
                _ => {}
            }
            fonts.insert(row.6.clone());
        }
        stats.fonts = u32::try_from(fonts.len()).unwrap_or(u32::MAX);
        Ok(stats)
    }

    fn glyph_rows(
        &mut self,
        index: u32,
    ) -> NativeResult<(Vec<crate::extract::GlyphSnapshotRow>, usize)> {
        let number = self.page_number(index)?;
        let (_, _, rows, unmapped) =
            self.doc
                .extract_glyph_snapshot(py(), number, 65_536, 1_048_576)?;
        Ok((rows, unmapped))
    }

    /// Image placements (metadata only; nothing is decoded).
    pub fn images(&mut self, index: u32) -> NativeResult<Vec<NativeImage>> {
        self.page_number(index)?;
        let settings = self.doc.interpreter_settings();
        let pdf = self.doc.hayro_view()?;
        let page = &pdf.pages()[index as usize];
        let cache = hayro::hayro_interpret::InterpreterCache::new();
        let (width, height) = page.render_dimensions();
        let mut context = Context::new(
            page.initial_transform(true).to_kurbo(),
            Rect::new(0.0, 0.0, f64::from(width), f64::from(height)),
            &cache,
            pdf.xref(),
            settings,
        );
        let mut collector = PlacementCollector::default();
        interpret_page(page, &mut context, &mut collector);
        Ok(collector.images)
    }

    pub fn drawings(&mut self, index: u32) -> NativeResult<NativeDrawings> {
        let number = self.page_number(index)?;
        let (width, height, _) = self.size(index)?;
        let paths = self.doc.extract_drawings(py(), number)?;
        let mut stats = NativeDrawings::default();
        // Union area on a 1 pt grid so overlapping fills are not double counted.
        let columns = (width.ceil() as usize).clamp(1, 4096);
        let rows = (height.ceil() as usize).clamp(1, 4096);
        let mut grid = vec![false; columns * rows];
        for (bbox, _, items, _, _, _) in &paths {
            stats.path_count += 1;
            let (path_width, path_height) = (bbox.2 - bbox.0, bbox.3 - bbox.1);
            stats.line_count += items.iter().filter(|item| item.0 == "l").count() as u32;
            if path_width >= 20.0 && path_height <= 2.0 || path_height >= 12.0 && path_width <= 2.0 {
                stats.long_rule_count += 1;
            }
            if is_rect_path(items) {
                stats.rect_count += 1;
            }
            let x0 = (bbox.0.floor().max(0.0) as usize).min(columns);
            let x1 = (bbox.2.ceil().max(0.0) as usize).min(columns);
            let y0 = (bbox.1.floor().max(0.0) as usize).min(rows);
            let y1 = (bbox.3.ceil().max(0.0) as usize).min(rows);
            for y in y0..y1 {
                grid[y * columns + x0..y * columns + x1].fill(true);
            }
        }
        stats.vector_area = grid.iter().filter(|cell| **cell).count() as f64;
        Ok(stats)
    }

    pub fn widgets(&mut self, index: u32) -> NativeResult<Vec<NativeWidget>> {
        let number = self.page_number(index)?;
        let (crop, rotation) = self.doc.page_display_geometry(number)?;
        let page_id = self.doc.page_id(number)?;
        let fields = self.doc.collect_form_fields()?;
        let doc = &self.doc.doc;
        let Some(annots) = self.doc.page_annotation_items(page_id)? else {
            return Ok(Vec::new());
        };
        let mut out = Vec::new();
        for item in annots {
            let (id, dict) = match item {
                Object::Reference(id) => match doc.get_object(*id).and_then(Object::as_dict) {
                    Ok(dict) => (Some(*id), dict),
                    Err(_) => continue,
                },
                Object::Dictionary(dict) => (None, dict),
                _ => continue,
            };
            if !matches!(dict.get(b"Subtype").and_then(Object::as_name), Ok(b"Widget")) {
                continue;
            }
            let Some(rect) = resolve_box(doc, dict, b"Rect") else {
                continue;
            };
            let display = draw::pdf_rect_to_display(crop, rotation, rect);
            let parent = dict.get(b"Parent").and_then(Object::as_reference).ok();
            let field = fields
                .iter()
                .find(|field| Some(field.1) == id)
                .or_else(|| fields.iter().find(|field| Some(field.1) == parent));
            let (kind, name, value) = match field {
                Some((name, _, ft, flags, value)) => (
                    widget_kind(ft, *flags).to_owned(),
                    Some(name.clone()),
                    value.as_ref().map(|value| value.to_string()),
                ),
                None => ("unknown".to_owned(), None, None),
            };
            out.push(NativeWidget {
                kind,
                name,
                value,
                bbox: (display[0], display[1], display[2], display[3]),
            });
        }
        Ok(out)
    }

    pub fn annotations(&self, index: u32) -> NativeResult<Vec<NativeAnnotation>> {
        let number = self.page_number(index)?;
        Ok(self
            .doc
            .read_annotations(py(), number)?
            .into_iter()
            .map(|(subtype, rect, contents, uri)| NativeAnnotation {
                subtype,
                contents,
                uri,
                bbox: rect,
            })
            .collect())
    }

    pub fn links(&self, index: u32) -> NativeResult<Vec<NativeLink>> {
        let number = self.page_number(index)?;
        Ok(self
            .doc
            .read_links(py(), number)?
            .into_iter()
            .map(|(kind, rect, uri, page, _, _, _, _)| NativeLink {
                kind,
                uri,
                dest_page: page.map(|page| page.saturating_sub(1)),
                bbox: rect,
            })
            .collect())
    }

    /// Render a page and encode it as PNG, JPEG or lossless WebP.
    pub fn render(&mut self, index: u32, options: &NativeRender) -> NativeResult<Vec<u8>> {
        let number = self.page_number(index)?;
        let (width, height, _) = self.size(index)?;
        let mut scale = match (options.dpi, options.max_edge_px) {
            (Some(dpi), _) if dpi > 0.0 => dpi / 72.0,
            (Some(_), _) => return Err(NativeError::invalid("dpi must be positive")),
            (None, None) => 1.0,
            (None, Some(_)) => f64::INFINITY,
        };
        if let Some(edge) = options.max_edge_px {
            if edge == 0 {
                return Err(NativeError::invalid("maxEdgePx must be positive"));
            }
            let longest = width.max(height).max(1.0);
            scale = scale.min(f64::from(edge) / longest);
        }
        let scale = scale as f32;
        // Opaque white keeps JPEG/PNG output compact and avoids alpha for scans.
        let pixmap = self
            .doc
            .render_pixmap_impl(py(), number, scale, Some((255, 255, 255, 255)))?;
        let (pixel_width, pixel_height) = (u32::from(pixmap.width()), u32::from(pixmap.height()));
        let (out_width, out_height, rgba) = match options.clip {
            Some(clip) => cropped_rgba_bytes(pixmap, pixel_width, pixel_height, scale, clip)
                .map_err(NativeError::invalid)?,
            None => (
                pixel_width,
                pixel_height,
                rgba_bytes(pixmap).map_err(|message| NativeError {
                    code: "PDF_ERROR",
                    limit: None,
                    message,
                })?,
            ),
        };
        encode(&rgba, out_width, out_height, options)
    }
}

fn widget_kind(ft: &str, flags: i64) -> &'static str {
    match ft {
        "Tx" => "text",
        "Sig" => "signature",
        "Ch" if flags & (1 << 17) != 0 => "combobox",
        "Ch" => "listbox",
        "Btn" if flags & (1 << 16) != 0 => "button",
        "Btn" if flags & (1 << 15) != 0 => "radio",
        "Btn" => "checkbox",
        _ => "unknown",
    }
}

fn render_mode_of(mode: &str) -> u8 {
    match mode {
        "stroke" => 1,
        "invisible" => 3,
        _ => 0,
    }
}

fn glyph_bbox(x: f64, y: f64, size: f64, advance: f64, direction: (f64, f64)) -> BBox {
    const ASCENT: f64 = 0.8;
    const DESCENT: f64 = 0.2;
    if direction.0 >= 1.0 - 1e-6 && direction.1.abs() <= 1e-6 {
        return (x, y - size * ASCENT, x + advance, y + size * DESCENT);
    }
    let block = (-direction.1, direction.0);
    let mut bbox = (f64::INFINITY, f64::INFINITY, f64::NEG_INFINITY, f64::NEG_INFINITY);
    for inline in [0.0, advance] {
        for cross in [-size * ASCENT, size * DESCENT] {
            let px = x + direction.0 * inline + block.0 * cross;
            let py = y + direction.1 * inline + block.1 * cross;
            bbox = (bbox.0.min(px), bbox.1.min(py), bbox.2.max(px), bbox.3.max(py));
        }
    }
    bbox
}

/// A closed path of four axis-aligned line segments.
fn is_rect_path(items: &[crate::extract::DrawingItemTuple]) -> bool {
    if items.len() < 4 || items.len() > 5 || items.iter().any(|item| item.0 != "l") {
        return false;
    }
    items.iter().all(|item| {
        item.1.len() == 2
            && ((item.1[0].0 - item.1[1].0).abs() < 1e-3 || (item.1[0].1 - item.1[1].1).abs() < 1e-3)
    })
}

fn collect_fonts(
    doc: &Document,
    resources: &Dictionary,
    depth: usize,
    seen: &mut BTreeSet<(u32, u16)>,
    fonts: &mut Vec<NativeFont>,
) {
    if depth > 4 {
        return;
    }
    if let Some(font_dict) = resources
        .get(b"Font")
        .ok()
        .map(|object| deref_object(doc, object))
        .and_then(|object| object.as_dict().ok())
    {
        for (_, entry) in font_dict.iter() {
            if let Object::Reference(id) = entry
                && !seen.insert(*id)
            {
                continue;
            }
            let Ok(dict) = deref_object(doc, entry).as_dict() else {
                continue;
            };
            fonts.push(describe_font(doc, dict));
        }
    }
    // Form XObjects carry their own resources.
    if let Some(xobjects) = resources
        .get(b"XObject")
        .ok()
        .map(|object| deref_object(doc, object))
        .and_then(|object| object.as_dict().ok())
    {
        for (_, entry) in xobjects.iter() {
            if let Object::Reference(id) = entry
                && !seen.insert(*id)
            {
                continue;
            }
            let Ok(stream) = deref_object(doc, entry).as_stream() else {
                continue;
            };
            if !matches!(stream.dict.get(b"Subtype").and_then(Object::as_name), Ok(b"Form")) {
                continue;
            }
            if let Some(inner) = stream
                .dict
                .get(b"Resources")
                .ok()
                .map(|object| deref_object(doc, object))
                .and_then(|object| object.as_dict().ok())
            {
                collect_fonts(doc, inner, depth + 1, seen, fonts);
            }
        }
    }
}

fn describe_font(doc: &Document, dict: &Dictionary) -> NativeFont {
    let name_of = |dict: &Dictionary, key: &[u8]| {
        dict.get(key)
            .ok()
            .map(|object| deref_object(doc, object))
            .and_then(|object| object.as_name().ok())
            .map(|bytes| String::from_utf8_lossy(bytes).into_owned())
    };
    let kind = name_of(dict, b"Subtype").unwrap_or_default();
    let name = name_of(dict, b"BaseFont")
        .or_else(|| name_of(dict, b"Name"))
        .unwrap_or_default();
    let is_type3 = kind == "Type3";
    let descriptor_owner = if kind == "Type0" {
        dict.get(b"DescendantFonts")
            .ok()
            .map(|object| deref_object(doc, object))
            .and_then(|object| object.as_array().ok())
            .and_then(|items| items.first())
            .and_then(|item| deref_object(doc, item).as_dict().ok())
    } else {
        Some(dict)
    };
    let embedded = is_type3
        || descriptor_owner
            .and_then(|owner| owner.get(b"FontDescriptor").ok())
            .map(|object| deref_object(doc, object))
            .and_then(|object| object.as_dict().ok())
            .is_some_and(|descriptor| {
                descriptor.has(b"FontFile")
                    || descriptor.has(b"FontFile2")
                    || descriptor.has(b"FontFile3")
            });
    NativeFont {
        name,
        kind,
        embedded,
        has_to_unicode: dict.has(b"ToUnicode"),
        is_type3,
    }
}

/// Collects raster placements without decoding pixels.
#[derive(Default)]
struct PlacementCollector {
    images: Vec<NativeImage>,
}

impl Device<'_> for PlacementCollector {
    fn set_soft_mask(&mut self, _: Option<SoftMask<'_>>) {}
    fn set_blend_mode(&mut self, _: BlendMode) {}
    fn draw_path(&mut self, _: &kurbo::BezPath, _: Affine, _: &Paint<'_>, _: &PathDrawMode) {}
    fn push_clip_path(&mut self, _: &ClipPath) {}
    fn push_transparency_group(&mut self, _: f32, _: Option<SoftMask<'_>>, _: BlendMode) {}
    fn draw_glyph(&mut self, _: &Glyph<'_>, _: Affine, _: Affine, _: &Paint<'_>, _: &GlyphDrawMode) {}
    fn pop_clip_path(&mut self) {}
    fn pop_transparency_group(&mut self) {}

    fn draw_image(&mut self, image: Image<'_, '_>, transform: Affine) {
        let Image::Raster(raster) = image else {
            return;
        };
        if self.images.len() >= 4096 {
            return;
        }
        let (width, height) = (raster.width(), raster.height());
        let [a, b, c, d, _, _] = transform.as_coeffs();
        let dpi = |scale: f64| {
            if scale.is_finite() && scale > 0.0 { 72.0 / scale } else { 0.0 }
        };
        let (dpi_x, dpi_y) = (dpi(a.hypot(b)), dpi(c.hypot(d)));
        let (w, h) = (f64::from(width), f64::from(height));
        let mut bbox = (f64::INFINITY, f64::INFINITY, f64::NEG_INFINITY, f64::NEG_INFINITY);
        for (px, py) in [(0.0, 0.0), (w, 0.0), (0.0, h), (w, h)] {
            let p = transform * Point::new(px, py);
            bbox = (bbox.0.min(p.x), bbox.1.min(p.y), bbox.2.max(p.x), bbox.3.max(p.y));
        }
        self.images.push(NativeImage {
            index: self.images.len() as u32,
            bbox,
            width_px: width,
            height_px: height,
            effective_dpi: dpi_x.min(dpi_y),
        });
    }
}

fn encode(rgba: &[u8], width: u32, height: u32, options: &NativeRender) -> NativeResult<Vec<u8>> {
    let pixels = (width as usize) * (height as usize);
    let (samples, png_color, jpeg_color, channels) = if options.gray {
        let mut luma = Vec::with_capacity(pixels);
        for px in rgba.chunks_exact(4) {
            luma.push(
                ((299 * u32::from(px[0]) + 587 * u32::from(px[1]) + 114 * u32::from(px[2])) / 1000)
                    as u8,
            );
        }
        (luma, png::ColorType::Grayscale, jpeg_encoder::ColorType::Luma, 1u8)
    } else {
        let mut rgb = Vec::with_capacity(pixels * 3);
        for px in rgba.chunks_exact(4) {
            rgb.extend_from_slice(&px[..3]);
        }
        (rgb, png::ColorType::Rgb, jpeg_encoder::ColorType::Rgb, 3u8)
    };
    let encoding_error = |message: String| NativeError {
        code: "PDF_ERROR",
        limit: None,
        message,
    };
    match options.format {
        ImageFormat::Png => crate::extract::encode_png_bounded(
            width,
            height,
            png_color,
            &samples,
            png::Compression::Fast,
            None,
        )
        .map_err(|error| match error {
            crate::extract::PngEncodeError::Allocation(message) => encoding_error(message),
            crate::extract::PngEncodeError::Encoding(error) => {
                encoding_error(format!("failed to encode PNG: {error}"))
            }
            crate::extract::PngEncodeError::OutputLimit => encoding_error("PNG output limit".into()),
        }),
        ImageFormat::Jpeg => {
            let mut out = Vec::new();
            let encoder = jpeg_encoder::Encoder::new(&mut out, options.quality.clamp(1, 100));
            let (w, h) = (
                u16::try_from(width).map_err(|_| encoding_error("image too wide for JPEG".into()))?,
                u16::try_from(height).map_err(|_| encoding_error("image too tall for JPEG".into()))?,
            );
            encoder
                .encode(&samples, w, h, jpeg_color)
                .map_err(|error| encoding_error(format!("failed to encode JPEG: {error}")))?;
            Ok(out)
        }
        ImageFormat::Webp => {
            let mut out = Vec::new();
            let color = if channels == 1 {
                image_webp::ColorType::L8
            } else {
                image_webp::ColorType::Rgb8
            };
            image_webp::WebPEncoder::new(&mut out)
                .encode(&samples, width, height, color)
                .map_err(|error| encoding_error(format!("failed to encode WebP: {error}")))?;
            Ok(out)
        }
    }
}
