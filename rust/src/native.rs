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
/// Codes, mapped from the Python exception classes the engine raises:
/// `PDF_LOCKED` (`PasswordError`: password needed or wrong),
/// `PDF_UNSUPPORTED_ENCRYPTION` (`UnsupportedEncryptionError`: unknown security
/// handler or unsupported /V or /R), `PDF_LIMIT` (`LimitError`; `limit` carries its
/// stable `code`), `INVALID_ARGUMENT` (`ValueError`/`TypeError`), `PDF_ERROR`
/// (`PdfError` and `OcrError`: malformed input or engine failure), and
/// `NATIVE_PDF_UNSUPPORTED` (a capability this build cannot serve, such as OCR
/// without models). The binding adds `PDF_CLOSED`.
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
            "UnsupportedEncryptionError" => "PDF_UNSUPPORTED_ENCRYPTION",
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
    /// Server-side ingestion profile for validated uploads: sized for multi-hundred-page
    /// scans and text-heavy books (the `web` profile rejects many ordinary files).
    /// Text and glyph limits are cumulative over the document, so they scale with pages.
    pub fn worker() -> Self {
        let mib = 1024 * 1024;
        Self {
            max_file_size: Some(512 * mib),
            max_pages: Some(2_000),
            max_objects: Some(2_000_000),
            max_decompressed_size: Some(256 * mib),
            max_page_content_size: Some(32 * mib),
            max_total_decompressed_size: Some(2048 * mib),
            max_object_depth: Some(64),
            max_text_size: Some(32 * mib),
            max_interpretation_size: Some(512 * mib),
            max_text_glyphs: Some(4 * mib),
        }
    }

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
    /// Object number, absent for direct font dictionaries.
    pub xref: Option<u32>,
    /// BaseFont, subset tag included (`ABCDEF+Name`).
    pub name: String,
    /// PDF subtype: Type1, MMType1, TrueType, Type0 or Type3.
    pub kind: String,
    /// `CIDFontType0`/`CIDFontType2` for Type0 fonts.
    pub descendant_type: Option<String>,
    pub embedded: bool,
    pub has_to_unicode: bool,
    pub is_type3: bool,
    /// BaseFont carries a six-letter subset tag.
    pub subset: bool,
    pub encoding: Option<String>,
    /// Zero-based pages that use the font.
    pub pages: Vec<u32>,
}

#[derive(Debug, Clone)]
pub struct NativeJavaScript {
    /// `document`, `page`, `annotation`, `field`, ...
    pub scope: String,
    /// Zero-based page, when the action is page-scoped.
    pub page: Option<u32>,
    pub event: Option<String>,
}

#[derive(Debug, Clone)]
pub struct NativeLayer {
    pub xref: u32,
    pub name: String,
    pub visible: bool,
    pub intent: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct NativeAttachment {
    pub name: String,
    /// Stored (decoded) size in bytes.
    pub size: u64,
    pub declared_size: Option<u64>,
    pub mime: Option<String>,
    pub description: Option<String>,
}

/// One word with its page-space box (points, top-left origin).
#[derive(Debug, Clone)]
pub struct NativeWord {
    pub text: String,
    pub bbox: BBox,
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
    /// Baseline direction of the line the span belongs to (unit vector).
    pub direction: (f64, f64),
    /// 1 for vertical writing (for example vertical CJK), else 0.
    pub writing_mode: u8,
}

#[derive(Debug, Clone, Default)]
pub struct NativeGlyphStats {
    pub glyphs: u32,
    pub invisible: u32,
    pub stroke: u32,
    pub unmapped: u32,
    pub fonts: u32,
}

/// One raw text run from `scan`: a single font/size/render-mode run with glyph evidence.
#[derive(Debug, Clone)]
pub struct NativeScanSpan {
    pub text: String,
    pub bbox: BBox,
    pub font: String,
    pub size: f64,
    pub flags: i64,
    pub render_mode: u8,
    pub invisible: bool,
    pub unmapped: u32,
    pub glyphs: u32,
    pub type3: bool,
    pub control_chars: u32,
    pub over_image: u32,
    pub direction: (f64, f64),
    /// 1 for vertical writing, else 0.
    pub writing_mode: u8,
}

/// One image placement from `scan` (no pixels decoded).
#[derive(Debug, Clone)]
pub struct NativeScanImage {
    pub index: u32,
    pub bbox: BBox,
    pub width_px: u32,
    pub height_px: u32,
    pub dpi_x: f64,
    pub dpi_y: f64,
    pub dpi: f64,
    pub stencil: bool,
}

#[derive(Debug, Clone, Default)]
pub struct NativeScanStats {
    pub glyphs: u32,
    pub mapped: u32,
    pub unmapped: u32,
    pub invisible: u32,
    pub stroke: u32,
    pub type3: u32,
    pub control_chars: u32,
    pub over_image: u32,
}

/// Everything the routing probes need from one interpretation pass.
#[derive(Debug, Clone, Default)]
pub struct NativeScan {
    pub width: f64,
    pub height: f64,
    pub spans: Vec<NativeScanSpan>,
    pub images: Vec<NativeScanImage>,
    pub stats: NativeScanStats,
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
    /// Horizontal plus vertical rules (`h_rule_count + v_rule_count`).
    pub long_rule_count: u32,
    /// Paths at least 20 pt wide and at most 2 pt tall.
    pub h_rule_count: u32,
    /// Paths at least 12 pt tall and at most 2 pt wide.
    pub v_rule_count: u32,
    pub path_count: u32,
    /// Union area of all path bounding boxes in pt² (1 pt grid).
    pub vector_area: f64,
    /// A drawing safety limit (paths, commands, dash values) cut collection short; the
    /// counts and boxes cover the paths seen before it.
    pub truncated: bool,
    /// One entry per path: bounding box and paint (`f`, `s` or `fs`).
    pub paths: Vec<NativeDrawingPath>,
}

#[derive(Debug, Clone)]
pub struct NativeDrawingPath {
    pub bbox: BBox,
    pub paint: String,
}

#[derive(Debug, Clone)]
pub struct NativeWidget {
    pub kind: String,
    pub name: Option<String>,
    pub value: Option<String>,
    pub filled: bool,
    pub read_only: bool,
    pub required: bool,
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
    fn ordered_pages(&self) -> NativeResult<Vec<(u32, ObjectId)>> {
        Ok(self
            .doc
            .ordered_page_ids()?
            .into_iter()
            .enumerate()
            .map(|(index, id)| (index as u32 + 1, id))
            .collect())
    }

    /// Whether any JavaScript action exists (document, page, annotation or field).
    pub fn has_java_script(&self) -> NativeResult<bool> {
        Ok(!self.java_script()?.is_empty())
    }

    /// Every JavaScript action with its scope, page and trigger event.
    pub fn java_script(&self) -> NativeResult<Vec<NativeJavaScript>> {
        let pages = self.ordered_pages()?;
        Ok(crate::inspect::collect_javascript(&self.doc.doc, &pages)
            .into_iter()
            .map(|found| NativeJavaScript {
                scope: found.scope.to_owned(),
                page: found.page.map(|page| page.saturating_sub(1)),
                event: found.event,
            })
            .collect())
    }

    /// Optional content groups (layers) with their default visibility.
    pub fn optional_content(&self) -> Vec<NativeLayer> {
        crate::inspect::collect_optional_content(&self.doc.doc)
            .into_iter()
            .map(|group| NativeLayer {
                xref: group.object.0,
                name: group.name,
                visible: group.visible,
                intent: group.intent,
            })
            .collect()
    }

    /// Embedded file attachments with stored size, declared size and MIME type.
    pub fn attachments(&self) -> Vec<NativeAttachment> {
        crate::inspect::collect_attachments(&self.doc.doc)
            .into_iter()
            .map(|file| NativeAttachment {
                name: file.name,
                size: file.stored_size as u64,
                declared_size: file.size,
                mime: file.mime,
                description: file.description,
            })
            .collect()
    }

    /// Fonts referenced by one page (through Form XObjects too), or by every page.
    pub fn fonts(&self, page: Option<u32>) -> NativeResult<Vec<NativeFont>> {
        let all = self.ordered_pages()?;
        let pages: Vec<(u32, ObjectId)> = match page {
            Some(index) => {
                let number = self.page_number(index)?;
                all.into_iter().filter(|(n, _)| *n == number).collect()
            }
            None => all,
        };
        Ok(crate::inspect::collect_fonts(&self.doc.doc, &pages)
            .into_iter()
            .map(|font| NativeFont {
                xref: font.object.map(|id| id.0),
                name: font.name,
                kind: font.subtype,
                descendant_type: font.descendant_subtype,
                embedded: font.embedded,
                has_to_unicode: font.has_to_unicode,
                is_type3: font.is_type3,
                subset: font.subset,
                encoding: font.encoding,
                pages: font.pages.into_iter().map(|n| n.saturating_sub(1)).collect(),
            })
            .collect())
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

    /// Leave out text painted in render mode 3 (OCR layers) from `text` and
    /// `markdown`. Default off: invisible text is part of the document's text.
    /// `spans` and `glyph_stats` always report it.
    pub fn set_skip_invisible_text(&mut self, skip: bool) {
        self.doc.set_skip_invisible_text(skip);
    }

    pub fn text(&mut self, index: u32) -> NativeResult<String> {
        let number = self.page_number(index)?;
        Ok(self.doc.extract_text(py(), vec![number])?)
    }

    /// Markdown for one page. Heading sizes are inferred from this page alone.
    pub fn markdown(&mut self, index: u32, strategy: TableStrategy) -> NativeResult<String> {
        let number = self.page_number(index)?;
        let strategy = match strategy {
            TableStrategy::Lines => Some("lines"),
            TableStrategy::Text => Some("text"),
            TableStrategy::None => None,
        };
        Ok(self
            .doc
            .page_markdown(py(), number, strategy, Some(MAX_PAGE_OUTPUT))?)
    }

    pub fn tables(
        &mut self,
        index: u32,
        strategy: TableStrategy,
    ) -> NativeResult<Vec<NativeTable>> {
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
        // Spans always include invisible text (that is how callers see OCR layers), even
        // when text()/markdown() skip it. Flipping the flag drops the cached text pages.
        let skipping = self.doc.skip_invisible_text();
        if skipping {
            self.doc.set_skip_invisible_text(false);
        }
        let layout = self.doc.extract_layout(py(), number, true, false);
        if skipping {
            self.doc.set_skip_invisible_text(true);
        }
        let (_, _, blocks) = layout?;
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
                        direction: line.3,
                        writing_mode: line.4,
                    });
                }
            }
        }
        Ok(spans)
    }

    /// One interpretation pass: raw text runs with render mode, unmapped/Type 3/control
    /// counts and text-over-image evidence, image placements without decoding pixels,
    /// and glyph totals. `host_coverage` is the share of the page an image must cover
    /// to count as a text host.
    pub fn scan(
        &mut self,
        index: u32,
        spans: bool,
        images: bool,
        host_coverage: f64,
    ) -> NativeResult<NativeScan> {
        let number = self.page_number(index)?;
        if !host_coverage.is_finite() || !(0.0..=1.0).contains(&host_coverage) {
            return Err(NativeError::invalid("hostCoverage must be a number from 0 to 1"));
        }
        let (width, height, raw_spans, raw_images, unmapped_total, glyph_total) =
            self.doc
                .scan_page_ext(py(), number, spans, images, host_coverage, 65_536, 1_048_576)?;
        let spans: Vec<NativeScanSpan> = raw_spans
            .into_iter()
            .map(
                |(text, bbox, font, size, flags, mode, unmapped, glyphs, type3, controls, over, direction)| {
                    NativeScanSpan {
                        text,
                        bbox,
                        font,
                        size,
                        flags,
                        render_mode: mode,
                        invisible: mode == 3,
                        unmapped,
                        glyphs,
                        type3,
                        control_chars: controls,
                        over_image: over,
                        direction: (direction.0, direction.1),
                        writing_mode: direction.2 as u8,
                    }
                },
            )
            .collect();
        let images = raw_images
            .into_iter()
            .enumerate()
            .map(|(index, (bbox, width_px, height_px, dpi_x, dpi_y, stencil))| NativeScanImage {
                index: index as u32,
                bbox,
                width_px,
                height_px,
                dpi_x,
                dpi_y,
                dpi: dpi_x.min(dpi_y),
                stencil,
            })
            .collect();
        let sum = |pick: &dyn Fn(&NativeScanSpan) -> u32| -> u32 {
            spans.iter().map(pick).fold(0u32, u32::saturating_add)
        };
        let glyphs = u32::try_from(glyph_total).unwrap_or(u32::MAX);
        let unmapped = u32::try_from(unmapped_total).unwrap_or(u32::MAX);
        let stats = NativeScanStats {
            glyphs,
            mapped: glyphs.saturating_sub(unmapped),
            unmapped,
            invisible: sum(&|s| if s.invisible { s.glyphs } else { 0 }),
            stroke: sum(&|s| if matches!(s.render_mode, 1 | 2) { s.glyphs } else { 0 }),
            type3: sum(&|s| if s.type3 { s.glyphs } else { 0 }),
            control_chars: sum(&|s| s.control_chars),
            over_image: sum(&|s| s.over_image),
        };
        Ok(NativeScan { width, height, spans, images, stats })
    }

    /// Words with boxes, in layout order. Unlike `spans`, a line shared by
    /// side-by-side columns is not merged into one entry, so callers can find
    /// gutters and fix column reading order.
    pub fn words(&mut self, index: u32) -> NativeResult<Vec<NativeWord>> {
        let number = self.page_number(index)?;
        let (_, _, blocks) = self.doc.extract_layout(py(), number, false, true)?;
        let mut words = Vec::new();
        for block in &blocks {
            for line in &block.1 {
                for (bbox, text) in &line.2 {
                    words.push(NativeWord { text: text.clone(), bbox: *bbox });
                }
            }
        }
        Ok(words)
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
        let (paths, truncated) = self.doc.extract_drawings_partial(py(), number)?;
        let mut stats = NativeDrawings { truncated, ..Default::default() };
        // Union area on a 1 pt grid so overlapping fills are not double counted.
        let columns = (width.ceil() as usize).clamp(1, 4096);
        let rows = (height.ceil() as usize).clamp(1, 4096);
        let mut grid = vec![false; columns * rows];
        for (bbox, paint, items, _, _, _) in paths {
            stats.path_count += 1;
            let (path_width, path_height) = (bbox.2 - bbox.0, bbox.3 - bbox.1);
            stats.line_count += items.iter().filter(|item| item.0 == "l").count() as u32;
            if path_width >= 20.0 && path_height <= 2.0 {
                stats.h_rule_count += 1;
            } else if path_height >= 12.0 && path_width <= 2.0 {
                stats.v_rule_count += 1;
            }
            if is_rect_path(&items) {
                stats.rect_count += 1;
            }
            let x0 = (bbox.0.floor().max(0.0) as usize).min(columns);
            let x1 = (bbox.2.ceil().max(0.0) as usize).min(columns);
            let y0 = (bbox.1.floor().max(0.0) as usize).min(rows);
            let y1 = (bbox.3.ceil().max(0.0) as usize).min(rows);
            for y in y0..y1 {
                grid[y * columns + x0..y * columns + x1].fill(true);
            }
            stats.paths.push(NativeDrawingPath { bbox, paint });
        }
        stats.long_rule_count = stats.h_rule_count + stats.v_rule_count;
        stats.vector_area = grid.iter().filter(|cell| **cell).count() as f64;
        Ok(stats)
    }

    pub fn widgets(&mut self, index: u32) -> NativeResult<Vec<NativeWidget>> {
        let number = self.page_number(index)?;
        let (crop, rotation) = self.doc.page_display_geometry(number)?;
        let page_id = self.doc.page_id(number)?;
        let to_display = |rect: [f64; 4]| draw::pdf_rect_to_display(crop, rotation, rect);
        Ok(crate::inspect::collect_widgets(&self.doc.doc, page_id, &to_display)
            .into_iter()
            .map(|w| NativeWidget {
                kind: w.kind.to_owned(),
                name: (!w.name.is_empty()).then_some(w.name),
                value: w.value,
                filled: w.filled,
                read_only: w.read_only,
                required: w.required,
                bbox: (w.bbox[0], w.bbox[1], w.bbox[2], w.bbox[3]),
            })
            .collect())
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
            None => {
                // Convert straight to the encoder's samples: no intermediate RGBA copy,
                // and the raster is freed before encoding starts.
                let samples = pixmap_samples(pixmap, options.gray)?;
                return encode_samples(samples, pixel_width, pixel_height, options);
            }
        };
        encode(&rgba, out_width, out_height, options)
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
    let samples = if options.gray {
        let mut luma = Vec::with_capacity(pixels);
        for px in rgba.chunks_exact(4) {
            luma.push(luma_of(px[0], px[1], px[2]));
        }
        luma
    } else {
        let mut rgb = Vec::with_capacity(pixels * 3);
        for px in rgba.chunks_exact(4) {
            rgb.extend_from_slice(&px[..3]);
        }
        rgb
    };
    encode_samples(samples, width, height, options)
}

fn luma_of(r: u8, g: u8, b: u8) -> u8 {
    ((299 * u32::from(r) + 587 * u32::from(g) + 114 * u32::from(b)) / 1000) as u8
}

/// Encode 8-bit samples (gray or RGB per `options.gray`).
fn encode_samples(
    samples: Vec<u8>,
    width: u32,
    height: u32,
    options: &NativeRender,
) -> NativeResult<Vec<u8>> {
    let (png_color, jpeg_color, channels) = if options.gray {
        (png::ColorType::Grayscale, jpeg_encoder::ColorType::Luma, 1u8)
    } else {
        (png::ColorType::Rgb, jpeg_encoder::ColorType::Rgb, 3u8)
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

/// Unpremultiply a rendered pixmap into RGB (or gray) samples, consuming the raster.
fn pixmap_samples(pixmap: hayro::vello_cpu::Pixmap, gray: bool) -> NativeResult<Vec<u8>> {
    let pixels = pixmap.take_unpremultiplied();
    let channels = if gray { 1 } else { 3 };
    let length = pixels.len().checked_mul(channels).ok_or_else(|| NativeError {
        code: "PDF_ERROR",
        limit: None,
        message: "rendered raster size overflowed".to_owned(),
    })?;
    let mut out = Vec::new();
    out.try_reserve_exact(length).map_err(|error| NativeError {
        code: "PDF_ERROR",
        limit: None,
        message: format!("failed to allocate rendered raster: {error}"),
    })?;
    if gray {
        out.extend(pixels.iter().map(|px| luma_of(px.r, px.g, px.b)));
    } else {
        for px in &pixels {
            out.extend_from_slice(&[px.r, px.g, px.b]);
        }
    }
    Ok(out)
}

// ---------------------------------------------------------------------------
// OCR fill (PP-OCR through the pure-Rust RTen runtime)
// ---------------------------------------------------------------------------

const OCR_FILL_MIN_CONFIDENCE: f32 = 0.7;
const OCR_ADAPTIVE_MIN_CONFIDENCE: f32 = 0.5;
const OCR_FILL_UNRELIABLE_RATIO: f64 = 0.5;
const OCR_FILL_SLACK: f64 = 2.0;
const OCR_ADAPTIVE_MIN_NATIVE_CHARS: usize = 20;
const OCR_ADAPTIVE_MIN_IMAGE_AREA: f64 = 0.02;
const OCR_LAYER_CHUNK_WORDS: usize = 4096;
const OCR_LAYER_CHUNK_BYTES: usize = 1024 * 1024;
const OCR_MODEL_FILES: [&str; 3] = [
    "PP-OCRv6_det_small.rten",
    "PP-OCRv6_rec_small.rten",
    "ppocrv6_dict.txt",
];

/// Loaded OCR model set, shared by every document in the process.
pub struct NativeOcrEngine {
    engine: crate::ocr_engine::Engine,
    pub threads: usize,
}

type OcrEngineCache = std::sync::Mutex<HashMap<(String, usize), std::sync::Arc<NativeOcrEngine>>>;

fn ocr_engines() -> &'static OcrEngineCache {
    static CACHE: std::sync::OnceLock<OcrEngineCache> = std::sync::OnceLock::new();
    CACHE.get_or_init(Default::default)
}

/// Bounded number of concurrent render-and-recognize calls (default 1, like the
/// Python engine): each holds a page raster plus detector tensors.
struct OcrSlots {
    free: std::sync::Mutex<usize>,
    ready: std::sync::Condvar,
}

fn ocr_slots() -> &'static OcrSlots {
    static SLOTS: std::sync::OnceLock<OcrSlots> = std::sync::OnceLock::new();
    SLOTS.get_or_init(|| {
        let limit = std::env::var("PDFUST_OCR_MAX_CONCURRENT")
            .ok()
            .and_then(|value| value.parse::<usize>().ok())
            .map_or(1, |value| value.clamp(1, 16));
        OcrSlots { free: std::sync::Mutex::new(limit), ready: std::sync::Condvar::new() }
    })
}

struct OcrSlot;

impl OcrSlot {
    fn acquire() -> Self {
        let slots = ocr_slots();
        let mut free = slots.free.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
        while *free == 0 {
            free = slots.ready.wait(free).unwrap_or_else(|poisoned| poisoned.into_inner());
        }
        *free -= 1;
        Self
    }
}

impl Drop for OcrSlot {
    fn drop(&mut self) {
        let slots = ocr_slots();
        *slots.free.lock().unwrap_or_else(|poisoned| poisoned.into_inner()) += 1;
        slots.ready.notify_one();
    }
}

impl NativeOcrEngine {
    /// Load (or reuse) the PP-OCR model set. `model_dir` falls back to
    /// `PDFUST_OCR_MODEL_DIR`; `threads` defaults to min(4, CPUs). Missing models
    /// are reported as `NATIVE_PDF_UNSUPPORTED` so callers can fall back.
    pub fn load(
        model_dir: Option<&str>,
        threads: Option<usize>,
    ) -> NativeResult<std::sync::Arc<Self>> {
        let dir = model_dir
            .map(str::to_owned)
            .or_else(|| std::env::var("PDFUST_OCR_MODEL_DIR").ok())
            .filter(|dir| !dir.is_empty())
            .ok_or_else(|| NativeError {
                code: "NATIVE_PDF_UNSUPPORTED",
                limit: None,
                message: "OCR models are not configured: pass modelDir or set PDFUST_OCR_MODEL_DIR"
                    .to_owned(),
            })?;
        let threads = threads.unwrap_or_else(|| {
            std::thread::available_parallelism().map_or(1, usize::from).min(4)
        });
        if !(1..=16).contains(&threads) {
            return Err(NativeError::invalid("ocr threads must be from 1 through 16"));
        }
        let key = (dir.clone(), threads);
        let mut cache = ocr_engines().lock().unwrap_or_else(|poisoned| poisoned.into_inner());
        if let Some(engine) = cache.get(&key) {
            return Ok(std::sync::Arc::clone(engine));
        }
        let base = std::path::Path::new(&dir);
        for file in OCR_MODEL_FILES {
            if !base.join(file).is_file() {
                return Err(NativeError {
                    code: "NATIVE_PDF_UNSUPPORTED",
                    limit: None,
                    message: format!("OCR model file {file} not found in {dir}"),
                });
            }
        }
        let engine = crate::ocr_engine::Engine::load(
            base.join(OCR_MODEL_FILES[0]),
            base.join(OCR_MODEL_FILES[1]),
            base.join(OCR_MODEL_FILES[2]),
            threads,
            Some(64 * 1024 * 1024),
        )?;
        let engine = std::sync::Arc::new(Self { engine, threads });
        cache.insert(key, std::sync::Arc::clone(&engine));
        Ok(engine)
    }

    pub fn name(&self) -> &'static str {
        "pp-ocrv6-small-rten"
    }
}

#[derive(Debug, Clone)]
pub struct NativeOcrOptions {
    /// `fill` (default) or `adaptive`.
    pub adaptive: bool,
    pub dpi: f64,
    pub min_confidence: Option<f32>,
    pub tile_size: usize,
    pub overlap: usize,
    pub table_strategy: TableStrategy,
}

impl Default for NativeOcrOptions {
    fn default() -> Self {
        Self {
            adaptive: false,
            dpi: 200.0,
            min_confidence: None,
            tile_size: 1408,
            overlap: 192,
            table_strategy: TableStrategy::Lines,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct NativeOcrFill {
    pub text: String,
    pub markdown: String,
    /// OCR words inserted into the page's invisible text layer.
    pub filled_words: u32,
    /// Words the recognizer returned above the confidence threshold.
    pub recognized: u32,
    /// 1 when the whole native layer was replaced or OCR'd as a full page.
    pub replaced_pages: u32,
    /// Raster placements OCR'd by the adaptive policy.
    pub regions: u32,
    pub unmapped_native: bool,
}

type OcrWord = (f64, f64, f64, f64, String);

impl NativeDoc {
    /// Recognize one page (optionally one clip region) and return words in page points.
    #[allow(clippy::too_many_arguments)]
    fn ocr_recognize(
        &mut self,
        index: u32,
        engine: &NativeOcrEngine,
        options: &NativeOcrOptions,
        min_confidence: f32,
        clip: Option<BBox>,
    ) -> NativeResult<Vec<OcrWord>> {
        if !options.dpi.is_finite() || !(36.0..=600.0).contains(&options.dpi) {
            return Err(NativeError::invalid("dpi must be from 36 through 600"));
        }
        if !(256..=2048).contains(&options.tile_size) || options.tile_size % 32 != 0 {
            return Err(NativeError::invalid(
                "tileSize must be a multiple of 32 from 256 through 2048",
            ));
        }
        if options.overlap < 32 || options.overlap > options.tile_size / 2 {
            return Err(NativeError::invalid(
                "overlap must be from 32 through half of tileSize",
            ));
        }
        let number = self.page_number(index)?;
        let (page_width, page_height, _) = self.size(index)?;
        let _slot = OcrSlot::acquire();
        let scale = (options.dpi / 72.0) as f32;
        let pixmap = self
            .doc
            .render_pixmap_impl(py(), number, scale, Some((255, 255, 255, 255)))?;
        let (pixel_width, pixel_height) = (u32::from(pixmap.width()), u32::from(pixmap.height()));
        let pixel_to_page = 72.0 / options.dpi;
        let (width, height, rgba, offset_x, offset_y) = match clip {
            Some(clip) => {
                let clip = (
                    clip.0.max(0.0),
                    clip.1.max(0.0),
                    clip.2.min(page_width),
                    clip.3.min(page_height),
                );
                let (w, h, rgba) = cropped_rgba_bytes(pixmap, pixel_width, pixel_height, scale, clip)
                    .map_err(NativeError::invalid)?;
                (
                    w,
                    h,
                    rgba,
                    (clip.0 / pixel_to_page).floor() * pixel_to_page,
                    (clip.1 / pixel_to_page).floor() * pixel_to_page,
                )
            }
            None => (
                pixel_width,
                pixel_height,
                rgba_bytes(pixmap).map_err(|message| NativeError {
                    code: "PDF_ERROR",
                    limit: None,
                    message,
                })?,
                0.0,
                0.0,
            ),
        };
        let found = engine
            .engine
            .recognize(
                &rgba,
                width as usize,
                height as usize,
                options.tile_size,
                options.overlap,
                min_confidence,
            )
            .map_err(|message| NativeError { code: "PDF_ERROR", limit: None, message })?;
        Ok(found
            .into_iter()
            .map(|(x0, y0, x1, y1, text, _)| {
                (
                    offset_x + f64::from(x0) * pixel_to_page,
                    offset_y + f64::from(y0) * pixel_to_page,
                    offset_x + f64::from(x1) * pixel_to_page,
                    offset_y + f64::from(y1) * pixel_to_page,
                    text,
                )
            })
            .collect())
    }

    /// Insert OCR words as an invisible text layer (chunked to the layer limits).
    fn ocr_insert(&mut self, index: u32, words: &[OcrWord]) -> NativeResult<()> {
        let number = self.page_number(index)?;
        let mut chunk: Vec<OcrWord> = Vec::new();
        let mut bytes = 0usize;
        for word in words.iter().filter(|word| !word.4.is_empty()) {
            if chunk.len() == OCR_LAYER_CHUNK_WORDS || bytes + word.4.len() > OCR_LAYER_CHUNK_BYTES {
                self.doc.insert_ocr_layer(py(), number, std::mem::take(&mut chunk), 0)?;
                bytes = 0;
            }
            bytes += word.4.len();
            chunk.push(word.clone());
        }
        if !chunk.is_empty() {
            self.doc.insert_ocr_layer(py(), number, chunk, 0)?;
        }
        Ok(())
    }

    /// Add OCR text only where the native text layer is missing or unusable
    /// (policies `fill` and `adaptive`, identical to Python `Page.ocr_fill`), then
    /// return the page's text and Markdown including the new invisible layer.
    pub fn ocr_fill(
        &mut self,
        index: u32,
        engine: &NativeOcrEngine,
        options: &NativeOcrOptions,
    ) -> NativeResult<NativeOcrFill> {
        let fill_confidence = options.min_confidence.unwrap_or(OCR_FILL_MIN_CONFIDENCE);
        let adaptive_confidence = options.min_confidence.unwrap_or(OCR_ADAPTIVE_MIN_CONFIDENCE);
        for value in [fill_confidence, adaptive_confidence] {
            if !value.is_finite() || !(0.0..=1.0).contains(&value) {
                return Err(NativeError::invalid("minConfidence must be a number from 0 to 1"));
            }
        }
        let native_words = self.words(index)?;
        let unmapped_native = self.scan(index, false, false, 0.25)?.stats.unmapped > 0;
        let mut result = NativeOcrFill { unmapped_native, ..Default::default() };
        if options.adaptive {
            let native_chars = self.text(index)?.trim().chars().count();
            if unmapped_native || native_chars < OCR_ADAPTIVE_MIN_NATIVE_CHARS {
                result.replaced_pages = 1;
                let found = self.ocr_recognize(index, engine, options, adaptive_confidence, None)?;
                result.recognized += found.len() as u32;
                if !found.is_empty() {
                    self.ocr_insert(index, &found)?;
                    result.filled_words += found.iter().filter(|w| !w.4.is_empty()).count() as u32;
                }
            } else {
                let (width, height, _) = self.size(index)?;
                let min_area = OCR_ADAPTIVE_MIN_IMAGE_AREA * width * height;
                for image in self.images(index)? {
                    let b = image.bbox;
                    if (b.2 - b.0) * (b.3 - b.1) < min_area {
                        continue;
                    }
                    result.regions += 1;
                    // Native text inside the region wins: skip it (Python apply_ocr default).
                    let covered = self.words(index)?.iter().any(|word| {
                        !word.text.trim().is_empty()
                            && word.bbox.0 < b.2
                            && word.bbox.2 > b.0
                            && word.bbox.1 < b.3
                            && word.bbox.3 > b.1
                    });
                    if covered {
                        continue;
                    }
                    let found =
                        self.ocr_recognize(index, engine, options, adaptive_confidence, Some(b))?;
                    result.recognized += found.len() as u32;
                    if !found.is_empty() {
                        self.ocr_insert(index, &found)?;
                        result.filled_words +=
                            found.iter().filter(|w| !w.4.is_empty()).count() as u32;
                    }
                }
            }
        } else {
            let found = self.ocr_recognize(index, engine, options, fill_confidence, None)?;
            result.recognized = found.len() as u32;
            let native_boxes: Vec<BBox> = native_words.iter().map(|word| word.bbox).collect();
            let native_chars: usize = native_words.iter().map(|word| word.text.chars().count()).sum();
            let (replace_page, keep) = _Document::select_ocr_fill_words(
                native_boxes,
                native_chars,
                unmapped_native,
                found.clone(),
                OCR_FILL_SLACK,
                OCR_FILL_UNRELIABLE_RATIO,
            );
            result.replaced_pages = u32::from(replace_page);
            let fresh: Vec<OcrWord> = keep.into_iter().filter_map(|i| found.get(i).cloned()).collect();
            if !fresh.is_empty() {
                self.ocr_insert(index, &fresh)?;
                result.filled_words = fresh.iter().filter(|w| !w.4.is_empty()).count() as u32;
            }
        }
        result.text = self.text(index)?;
        result.markdown = self.markdown(index, options.table_strategy)?;
        Ok(result)
    }
}
