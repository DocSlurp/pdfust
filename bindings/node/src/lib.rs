//! N-API binding for the pdfust Rust core.
//!
//! The shape follows the frozen `PdfustNode` adapter interface. Errors carry a
//! `[CODE] message` prefix that `index.js` turns into `error.code`.

#![deny(clippy::all)]

use std::sync::{Arc, Mutex};

use napi::bindgen_prelude::*;
use napi_derive::napi;
use pdfust::document::native::{
    ImageFormat, NativeDoc, NativeError, NativeLimits, NativeOcrEngine, NativeOcrFill,
    NativeOcrOptions, NativeRender, TableStrategy,
};

type Shared = Arc<Mutex<Option<NativeDoc>>>;

/// Return freed heap pages to the OS. Rendering allocates multi-megabyte rasters on
/// libuv worker threads; glibc keeps them in per-thread arenas, which shows up as
/// hundreds of MB of RSS that never comes back. Trimming after each large task bounds it.
#[cfg(all(target_os = "linux", target_env = "gnu"))]
fn release_heap() {
    unsafe extern "C" {
        fn malloc_trim(pad: usize) -> i32;
    }
    // SAFETY: malloc_trim is thread-safe and takes no pointers.
    unsafe {
        malloc_trim(0);
    }
}

#[cfg(not(all(target_os = "linux", target_env = "gnu")))]
fn release_heap() {}

fn fail(error: NativeError) -> Error {
    let limit = error
        .limit
        .map(|limit| format!(":{limit}"))
        .unwrap_or_default();
    Error::new(
        Status::GenericFailure,
        format!("[{}{limit}] {}", error.code, error.message),
    )
}

fn closed() -> Error {
    Error::new(
        Status::GenericFailure,
        "[PDF_CLOSED] the document has been closed".to_owned(),
    )
}

fn with_doc<T>(
    shared: &Shared,
    run: impl FnOnce(&mut NativeDoc) -> std::result::Result<T, NativeError>,
) -> Result<T> {
    let mut guard = shared
        .lock()
        .map_err(|_| Error::new(Status::GenericFailure, "[PDF_ERROR] document lock poisoned"))?;
    let doc = guard.as_mut().ok_or_else(closed)?;
    run(doc).map_err(fail)
}

fn bbox(value: (f64, f64, f64, f64)) -> Vec<f64> {
    vec![value.0, value.1, value.2, value.3]
}

fn count(value: Option<f64>) -> Option<usize> {
    value
        .filter(|value| value.is_finite() && *value >= 0.0)
        .map(|value| value as usize)
}

#[napi(object)]
pub struct VersionInfo {
    pub version: String,
    pub git_sha: String,
    pub features: Vec<String>,
}

/// Resource limits for opening and interpreting a document. Unset means unbounded
/// (Python parity); `profile: "web"` applies the conservative upload profile first.
#[napi(object)]
pub struct Limits {
    #[napi(ts_type = "'web' | 'worker'")]
    pub profile: Option<String>,
    pub max_decompressed_size: Option<f64>,
    pub max_page_content_size: Option<f64>,
    pub max_file_size: Option<f64>,
    pub max_pages: Option<f64>,
    pub max_objects: Option<f64>,
    pub max_total_decompressed_size: Option<f64>,
    pub max_object_depth: Option<f64>,
    pub max_text_size: Option<f64>,
    pub max_interpretation_size: Option<f64>,
    pub max_text_glyphs: Option<f64>,
}

#[napi(object)]
pub struct OpenOptions {
    pub password: Option<String>,
    pub limits: Option<Limits>,
}

fn limits_of(options: &Option<OpenOptions>) -> Result<NativeLimits> {
    let Some(limits) = options.as_ref().and_then(|options| options.limits.as_ref()) else {
        return Ok(NativeLimits::default());
    };
    let mut resolved = match limits.profile.as_deref() {
        None => NativeLimits::default(),
        Some("web") => NativeLimits::web(),
        Some("worker") => NativeLimits::worker(),
        Some(other) => {
            return Err(Error::new(
                Status::InvalidArg,
                format!("[INVALID_ARGUMENT] unknown limits profile {other:?}"),
            ));
        }
    };
    macro_rules! set {
        ($field:ident) => {
            if let Some(value) = count(limits.$field) {
                resolved.$field = Some(value);
            }
        };
    }
    set!(max_decompressed_size);
    set!(max_page_content_size);
    set!(max_file_size);
    set!(max_pages);
    set!(max_objects);
    set!(max_total_decompressed_size);
    set!(max_object_depth);
    set!(max_text_size);
    set!(max_interpretation_size);
    set!(max_text_glyphs);
    Ok(resolved)
}

fn password_of(options: &Option<OpenOptions>) -> Option<&str> {
    options
        .as_ref()
        .and_then(|options| options.password.as_deref())
}

#[napi]
pub fn version() -> VersionInfo {
    VersionInfo {
        version: env!("CARGO_PKG_VERSION").to_owned(),
        git_sha: env!("PDFUST_GIT_SHA").to_owned(),
        features: [
            "text",
            "markdown",
            "spans",
            "images",
            "drawings",
            "widgets",
            "annotations",
            "links",
            "tables",
            "render:png",
            "render:jpeg",
            "render:webp",
            "scan",
            "fonts",
            "inspect",
            "ocr-fill",
        ]
        .map(str::to_owned)
        .to_vec(),
    }
}

#[napi]
pub fn open_path(path: String, options: Option<OpenOptions>) -> Result<PdfDoc> {
    let limits = limits_of(&options)?;
    let doc = NativeDoc::open_path(&path, password_of(&options), &limits).map_err(fail)?;
    Ok(PdfDoc::wrap(doc))
}

#[napi]
pub fn open_buffer(buffer: Buffer, options: Option<OpenOptions>) -> Result<PdfDoc> {
    let limits = limits_of(&options)?;
    let doc = NativeDoc::open_bytes(&buffer, password_of(&options), &limits).map_err(fail)?;
    Ok(PdfDoc::wrap(doc))
}

#[napi(object)]
pub struct Metadata {
    pub producer: Option<String>,
    pub creator: Option<String>,
    pub title: Option<String>,
    pub author: Option<String>,
    pub subject: Option<String>,
    pub keywords: Option<String>,
    pub creation_date: Option<String>,
    pub modification_date: Option<String>,
    pub pdf_version: String,
    pub repaired: bool,
    pub encrypted: bool,
    pub permissions: Option<Vec<String>>,
}

#[napi(object)]
pub struct OptionalContentGroup {
    pub xref: u32,
    pub name: String,
    /// Default visibility (`/D` `BaseState`, `/ON`, `/OFF`).
    pub visible: bool,
    pub intent: Vec<String>,
}

#[napi(object)]
pub struct Attachment {
    pub name: String,
    /// Stored (decoded) size in bytes.
    pub size: f64,
    /// Size declared in the file's `/Params`, when present.
    pub declared_size: Option<f64>,
    pub mime: Option<String>,
    pub description: Option<String>,
}

#[napi(object)]
pub struct JavaScriptAction {
    /// `document`, `page`, `annotation`, `field` ...
    pub scope: String,
    /// Zero-based page for page-scoped actions.
    pub page: Option<u32>,
    pub event: Option<String>,
}

#[napi(object)]
pub struct FontInfo {
    /// Object number; absent for direct font dictionaries.
    pub xref: Option<u32>,
    /// BaseFont including the subset tag (`ABCDEF+Name`).
    pub name: String,
    /// PDF subtype: Type1, MMType1, TrueType, Type0 or Type3.
    pub r#type: String,
    /// `CIDFontType0` or `CIDFontType2` for Type0 fonts.
    pub descendant_type: Option<String>,
    pub embedded: bool,
    pub has_to_unicode: bool,
    pub is_type3: bool,
    pub subset: bool,
    pub encoding: Option<String>,
    /// Zero-based pages using the font.
    pub pages: Vec<u32>,
}

#[napi]
pub struct PdfDoc {
    shared: Shared,
}

impl PdfDoc {
    fn wrap(doc: NativeDoc) -> Self {
        Self {
            shared: Arc::new(Mutex::new(Some(doc))),
        }
    }
}

#[napi]
impl PdfDoc {
    #[napi]
    pub fn page_count(&self) -> Result<u32> {
        with_doc(&self.shared, |doc| doc.page_count())
    }

    #[napi]
    pub fn metadata(&self) -> Result<Metadata> {
        with_doc(&self.shared, |doc| {
            let meta = doc.metadata()?;
            Ok(Metadata {
                producer: meta.producer,
                creator: meta.creator,
                title: meta.title,
                author: meta.author,
                subject: meta.subject,
                keywords: meta.keywords,
                creation_date: meta.creation_date,
                modification_date: meta.modification_date,
                pdf_version: meta.pdf_version,
                repaired: meta.repaired,
                encrypted: meta.encrypted,
                permissions: meta.permissions,
            })
        })
    }

    #[napi]
    pub fn has_java_script(&self) -> Result<bool> {
        with_doc(&self.shared, |doc| doc.has_java_script())
    }

    /// Every JavaScript action with scope, page and trigger event.
    #[napi]
    pub fn java_script(&self) -> Result<Vec<JavaScriptAction>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .java_script()?
                .into_iter()
                .map(|found| JavaScriptAction {
                    scope: found.scope,
                    page: found.page,
                    event: found.event,
                })
                .collect())
        })
    }

    #[napi]
    pub fn optional_content(&self) -> Result<Vec<OptionalContentGroup>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .optional_content()
                .into_iter()
                .map(|group| OptionalContentGroup {
                    xref: group.xref,
                    name: group.name,
                    visible: group.visible,
                    intent: group.intent,
                })
                .collect())
        })
    }

    #[napi]
    pub fn attachments(&self) -> Result<Vec<Attachment>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .attachments()
                .into_iter()
                .map(|file| Attachment {
                    name: file.name,
                    size: file.size as f64,
                    declared_size: file.declared_size.map(|size| size as f64),
                    mime: file.mime,
                    description: file.description,
                })
                .collect())
        })
    }

    #[napi]
    pub fn fonts(&self, page: Option<u32>) -> Result<Vec<FontInfo>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .fonts(page)?
                .into_iter()
                .map(|font| FontInfo {
                    xref: font.xref,
                    name: font.name,
                    r#type: font.kind,
                    descendant_type: font.descendant_type,
                    embedded: font.embedded,
                    has_to_unicode: font.has_to_unicode,
                    is_type3: font.is_type3,
                    subset: font.subset,
                    encoding: font.encoding,
                    pages: font.pages,
                })
                .collect())
        })
    }

    /// Leave invisible text (render mode 3, such as an OCR layer) out of `text()`,
    /// `markdown()` and `tables()`. Default `false`: it is included. `spans()`, `scan()`
    /// and `glyphStats()` always report it.
    #[napi]
    pub fn set_skip_invisible_text(&self, skip: bool) -> Result<()> {
        with_doc(&self.shared, |doc| {
            doc.set_skip_invisible_text(skip);
            Ok(())
        })
    }

    /// Engine warnings (for example a repaired cross-reference table) since the last call.
    #[napi]
    pub fn take_warnings(&self) -> Result<Vec<String>> {
        with_doc(&self.shared, |doc| Ok(doc.take_warnings()))
    }

    #[napi]
    pub fn page(&self, i: u32) -> Result<PdfPage> {
        let count = with_doc(&self.shared, |doc| doc.page_count())?;
        if i >= count {
            return Err(Error::new(
                Status::InvalidArg,
                format!("[INVALID_ARGUMENT] page {i} is out of range (document has {count} pages)"),
            ));
        }
        Ok(PdfPage {
            shared: Arc::clone(&self.shared),
            index: i,
        })
    }

    /// Release the document. Later calls throw `PDF_CLOSED`.
    #[napi]
    pub fn close(&self) {
        if let Ok(mut guard) = self.shared.lock() {
            guard.take();
        }
    }
}

#[napi(object)]
pub struct PageSize {
    pub width_pt: f64,
    pub height_pt: f64,
    #[napi(ts_type = "0 | 90 | 180 | 270")]
    pub rotation: u32,
}

#[napi(object)]
pub struct Span {
    pub text: String,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
    pub font: String,
    pub size: f64,
    pub render_mode: u32,
    pub invisible: bool,
    pub unmapped: u32,
    /// Baseline direction of the span's line (unit vector, `[1, 0]` for left-to-right).
    #[napi(ts_type = "[number, number]")]
    pub dir: Vec<f64>,
    /// 1 for vertical writing (for example vertical CJK), else 0.
    pub writing_mode: u32,
}

#[napi(object)]
pub struct Word {
    pub text: String,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
}

#[napi(object)]
pub struct GlyphStats {
    pub glyphs: u32,
    pub invisible: u32,
    pub stroke: u32,
    pub unmapped: u32,
    pub fonts: u32,
}

#[napi(object)]
pub struct ImageInfo {
    pub index: u32,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
    pub width_px: u32,
    pub height_px: u32,
    pub effective_dpi: f64,
}

#[napi(object)]
pub struct ScanOptions {
    /// Collect text runs (default true).
    pub spans: Option<bool>,
    /// Collect image placements (default true).
    pub images: Option<bool>,
    /// Page share an image must cover to count as a text host (default 0.25).
    pub host_coverage: Option<f64>,
}

#[napi(object)]
pub struct ScanSpan {
    pub text: String,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
    pub font: String,
    pub size: f64,
    pub flags: f64,
    pub render_mode: u32,
    pub invisible: bool,
    /// Glyphs in this run without a Unicode mapping.
    pub unmapped: u32,
    pub glyphs: u32,
    pub type3: bool,
    pub control_chars: u32,
    /// Glyphs drawn over a page-sized image (an OCR text layer or text on a scan).
    pub over_image: u32,
    #[napi(ts_type = "[number, number]")]
    pub dir: Vec<f64>,
    /// 1 for vertical writing, else 0.
    pub writing_mode: u32,
}

#[napi(object)]
pub struct ScanImage {
    pub index: u32,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
    pub width_px: u32,
    pub height_px: u32,
    pub dpi_x: f64,
    pub dpi_y: f64,
    pub dpi: f64,
    pub stencil: bool,
}

#[napi(object)]
pub struct ScanStats {
    pub glyphs: u32,
    pub mapped: u32,
    pub unmapped: u32,
    pub invisible: u32,
    pub stroke: u32,
    pub type3: u32,
    pub control_chars: u32,
    pub over_image: u32,
}

#[napi(object)]
pub struct PageScan {
    pub width: f64,
    pub height: f64,
    pub spans: Vec<ScanSpan>,
    pub images: Vec<ScanImage>,
    pub stats: ScanStats,
}

#[napi(object)]
pub struct DrawingPath {
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
    /// `f` fill, `s` stroke, `fs` both.
    pub paint: String,
}

#[napi(object)]
pub struct Drawings {
    pub line_count: u32,
    pub rect_count: u32,
    /// `h_rule_count + v_rule_count`.
    pub long_rule_count: u32,
    /// Paths at least 20 pt wide and at most 2 pt tall.
    pub h_rule_count: u32,
    /// Paths at least 12 pt tall and at most 2 pt wide.
    pub v_rule_count: u32,
    pub path_count: u32,
    /// Union area of the path bounding boxes in pt².
    pub vector_area: f64,
    /// A drawing safety limit cut collection short; everything else covers the paths seen.
    pub truncated: bool,
    pub paths: Vec<DrawingPath>,
}

#[napi(object)]
pub struct Widget {
    pub kind: String,
    pub name: Option<String>,
    pub value: Option<String>,
    pub filled: bool,
    pub read_only: bool,
    pub required: bool,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
}

#[napi(object)]
pub struct Annotation {
    pub subtype: String,
    pub contents: Option<String>,
    pub uri: Option<String>,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
}

#[napi(object)]
pub struct Link {
    pub uri: Option<String>,
    pub kind: String,
    /// Zero-based destination page for in-document links.
    pub dest_page: Option<u32>,
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
}

#[napi(object)]
pub struct Table {
    #[napi(ts_type = "[number, number, number, number]")]
    pub bbox: Vec<f64>,
    pub rows: Vec<Vec<String>>,
    pub row_count: u32,
    pub col_count: u32,
    pub confidence: f64,
}

#[napi(object)]
pub struct MarkdownOptions {
    #[napi(ts_type = "'lines' | 'text' | 'none'")]
    pub table_strategy: Option<String>,
}

#[napi(object)]
pub struct TablesOptions {
    #[napi(ts_type = "'lines' | 'text'")]
    pub strategy: Option<String>,
}

#[napi(object)]
pub struct RenderOptions {
    pub dpi: Option<f64>,
    pub max_edge_px: Option<u32>,
    #[napi(ts_type = "[number, number, number, number]")]
    pub clip: Option<Vec<f64>>,
    #[napi(ts_type = "'png' | 'jpeg' | 'webp'")]
    pub format: Option<String>,
    pub gray: Option<bool>,
    /// JPEG quality, 1-100 (default 85).
    pub quality: Option<u32>,
}

#[napi(object)]
pub struct OcrFillOptions {
    /// `fill` recognizes the whole page and inserts only words the native layer lacks;
    /// `adaptive` OCRs the whole page only when native text is nearly absent or
    /// unmapped, otherwise only the large raster regions. Default `fill`.
    #[napi(ts_type = "'fill' | 'adaptive'")]
    pub policy: Option<String>,
    /// Raster resolution for recognition (default 200; 150-200 is ~2x faster than 300).
    pub dpi: Option<f64>,
    /// Accepted for interface parity; the bundled PP-OCRv6 model set is multilingual.
    pub lang: Option<String>,
    /// Word confidence floor, 0-1 (default 0.7 for fill, 0.5 for adaptive).
    pub min_confidence: Option<f64>,
    /// Directory holding the PP-OCRv6 `.rten` models and dictionary
    /// (default: `PDFUST_OCR_MODEL_DIR`).
    pub model_dir: Option<String>,
    /// Inference threads, 1-16 (default min(4, CPUs)). Concurrent OCR calls in the
    /// process are bounded by `PDFUST_OCR_MAX_CONCURRENT` (default 1).
    pub threads: Option<u32>,
    pub tile_size: Option<u32>,
    pub overlap: Option<u32>,
    #[napi(ts_type = "'lines' | 'text' | 'none'")]
    pub table_strategy: Option<String>,
}

#[napi(object)]
pub struct OcrFillResult {
    /// Page text including the new invisible OCR layer.
    pub text: String,
    pub markdown: String,
    /// OCR words inserted into the page's invisible text layer.
    pub filled_regions: u32,
    /// Engine id, e.g. `pp-ocrv6-small-rten`.
    pub engine: String,
    pub policy: String,
    /// Words the recognizer returned above the confidence floor.
    pub recognized: u32,
    /// 1 when the page was OCR'd as a whole (fill replaced an unusable layer, or adaptive full-page).
    pub replaced_pages: u32,
    /// Raster placements OCR'd by the adaptive policy.
    pub regions: u32,
    /// The native layer had glyphs without Unicode.
    pub unmapped_native: bool,
}

fn strategy_of(value: Option<&str>) -> Result<TableStrategy> {
    TableStrategy::parse(value).map_err(fail)
}

fn render_of(options: Option<RenderOptions>) -> Result<NativeRender> {
    let mut render = NativeRender::default();
    let Some(options) = options else {
        return Ok(render);
    };
    render.dpi = options.dpi;
    render.max_edge_px = options.max_edge_px;
    render.gray = options.gray.unwrap_or(false);
    if let Some(quality) = options.quality {
        render.quality = quality.clamp(1, 100) as u8;
    }
    render.format = match options.format.as_deref() {
        None | Some("png") => ImageFormat::Png,
        Some("jpeg" | "jpg") => ImageFormat::Jpeg,
        Some("webp") => ImageFormat::Webp,
        Some(other) => {
            return Err(Error::new(
                Status::InvalidArg,
                format!("[INVALID_ARGUMENT] unknown render format {other:?}"),
            ));
        }
    };
    if let Some(clip) = options.clip {
        let [x0, y0, x1, y1] = clip[..] else {
            return Err(Error::new(
                Status::InvalidArg,
                "[INVALID_ARGUMENT] clip must have four numbers".to_owned(),
            ));
        };
        render.clip = Some((x0, y0, x1, y1));
    }
    Ok(render)
}

#[napi]
pub struct PdfPage {
    shared: Shared,
    index: u32,
}

#[napi]
impl PdfPage {
    #[napi]
    pub fn size(&self) -> Result<PageSize> {
        with_doc(&self.shared, |doc| {
            let (width_pt, height_pt, rotation) = doc.size(self.index)?;
            Ok(PageSize {
                width_pt,
                height_pt,
                rotation: u32::from(rotation),
            })
        })
    }

    #[napi]
    pub fn text(&self) -> Result<String> {
        with_doc(&self.shared, |doc| doc.text(self.index))
    }

    #[napi]
    pub fn markdown(&self, options: Option<MarkdownOptions>) -> Result<String> {
        let strategy = strategy_of(options.as_ref().and_then(|o| o.table_strategy.as_deref()))?;
        with_doc(&self.shared, |doc| doc.markdown(self.index, strategy))
    }

    #[napi(ts_return_type = "Promise<string>")]
    pub fn markdown_async(
        &self,
        options: Option<MarkdownOptions>,
    ) -> Result<AsyncTask<MarkdownTask>> {
        let strategy = strategy_of(options.as_ref().and_then(|o| o.table_strategy.as_deref()))?;
        Ok(AsyncTask::new(MarkdownTask {
            shared: Arc::clone(&self.shared),
            index: self.index,
            strategy,
        }))
    }

    #[napi]
    pub fn spans(&self) -> Result<Vec<Span>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .spans(self.index)?
                .into_iter()
                .map(|span| Span {
                    text: span.text,
                    bbox: bbox(span.bbox),
                    font: span.font,
                    size: span.size,
                    render_mode: u32::from(span.render_mode),
                    invisible: span.invisible,
                    unmapped: span.unmapped,
                    dir: vec![span.direction.0, span.direction.1],
                    writing_mode: u32::from(span.writing_mode),
                })
                .collect())
        })
    }

    /// One pass for routing probes: raw text runs (render mode, unmapped/Type 3/control
    /// counts, glyphs over a host image), image placements read without decoding pixels,
    /// and glyph totals. Cheaper than calling `spans()`, `images()` and `glyphStats()`.
    #[napi]
    pub fn scan(&self, options: Option<ScanOptions>) -> Result<PageScan> {
        let want_spans = options.as_ref().and_then(|o| o.spans).unwrap_or(true);
        let want_images = options.as_ref().and_then(|o| o.images).unwrap_or(true);
        let coverage = options
            .as_ref()
            .and_then(|o| o.host_coverage)
            .unwrap_or(0.25);
        with_doc(&self.shared, |doc| {
            let scan = doc.scan(self.index, want_spans, want_images, coverage)?;
            Ok(PageScan {
                width: scan.width,
                height: scan.height,
                spans: scan
                    .spans
                    .into_iter()
                    .map(|span| ScanSpan {
                        text: span.text,
                        bbox: bbox(span.bbox),
                        font: span.font,
                        size: span.size,
                        flags: span.flags as f64,
                        render_mode: u32::from(span.render_mode),
                        invisible: span.invisible,
                        unmapped: span.unmapped,
                        glyphs: span.glyphs,
                        type3: span.type3,
                        control_chars: span.control_chars,
                        over_image: span.over_image,
                        dir: vec![span.direction.0, span.direction.1],
                        writing_mode: u32::from(span.writing_mode),
                    })
                    .collect(),
                images: scan
                    .images
                    .into_iter()
                    .map(|image| ScanImage {
                        index: image.index,
                        bbox: bbox(image.bbox),
                        width_px: image.width_px,
                        height_px: image.height_px,
                        dpi_x: image.dpi_x,
                        dpi_y: image.dpi_y,
                        dpi: image.dpi,
                        stencil: image.stencil,
                    })
                    .collect(),
                stats: ScanStats {
                    glyphs: scan.stats.glyphs,
                    mapped: scan.stats.mapped,
                    unmapped: scan.stats.unmapped,
                    invisible: scan.stats.invisible,
                    stroke: scan.stats.stroke,
                    type3: scan.stats.type3,
                    control_chars: scan.stats.control_chars,
                    over_image: scan.stats.over_image,
                },
            })
        })
    }

    /// Words with boxes. `spans()` merges text that shares a baseline across
    /// columns into one entry; words keep their own boxes for column analysis.
    #[napi]
    pub fn words(&self) -> Result<Vec<Word>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .words(self.index)?
                .into_iter()
                .map(|word| Word {
                    text: word.text,
                    bbox: bbox(word.bbox),
                })
                .collect())
        })
    }

    /// Glyph counts for probes: invisible (Tr 3), stroked, unmapped, distinct fonts.
    #[napi]
    pub fn glyph_stats(&self) -> Result<GlyphStats> {
        with_doc(&self.shared, |doc| {
            let stats = doc.glyph_stats(self.index)?;
            Ok(GlyphStats {
                glyphs: stats.glyphs,
                invisible: stats.invisible,
                stroke: stats.stroke,
                unmapped: stats.unmapped,
                fonts: stats.fonts,
            })
        })
    }

    #[napi]
    pub fn images(&self) -> Result<Vec<ImageInfo>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .images(self.index)?
                .into_iter()
                .map(|image| ImageInfo {
                    index: image.index,
                    bbox: bbox(image.bbox),
                    width_px: image.width_px,
                    height_px: image.height_px,
                    effective_dpi: image.effective_dpi,
                })
                .collect())
        })
    }

    #[napi]
    pub fn drawings(&self) -> Result<Drawings> {
        with_doc(&self.shared, |doc| {
            let stats = doc.drawings(self.index)?;
            Ok(Drawings {
                line_count: stats.line_count,
                rect_count: stats.rect_count,
                long_rule_count: stats.long_rule_count,
                h_rule_count: stats.h_rule_count,
                v_rule_count: stats.v_rule_count,
                path_count: stats.path_count,
                vector_area: stats.vector_area,
                truncated: stats.truncated,
                paths: stats
                    .paths
                    .into_iter()
                    .map(|path| DrawingPath {
                        bbox: bbox(path.bbox),
                        paint: path.paint,
                    })
                    .collect(),
            })
        })
    }

    #[napi]
    pub fn widgets(&self) -> Result<Vec<Widget>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .widgets(self.index)?
                .into_iter()
                .map(|widget| Widget {
                    kind: widget.kind,
                    name: widget.name,
                    value: widget.value,
                    filled: widget.filled,
                    read_only: widget.read_only,
                    required: widget.required,
                    bbox: bbox(widget.bbox),
                })
                .collect())
        })
    }

    #[napi]
    pub fn annotations(&self) -> Result<Vec<Annotation>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .annotations(self.index)?
                .into_iter()
                .map(|annotation| Annotation {
                    subtype: annotation.subtype,
                    contents: annotation.contents,
                    uri: annotation.uri,
                    bbox: bbox(annotation.bbox),
                })
                .collect())
        })
    }

    #[napi]
    pub fn links(&self) -> Result<Vec<Link>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .links(self.index)?
                .into_iter()
                .map(|link| Link {
                    uri: link.uri,
                    kind: link.kind,
                    dest_page: link.dest_page,
                    bbox: bbox(link.bbox),
                })
                .collect())
        })
    }

    #[napi]
    pub fn tables(&self, options: Option<TablesOptions>) -> Result<Vec<Table>> {
        let strategy = strategy_of(options.as_ref().and_then(|o| o.strategy.as_deref()))?;
        with_doc(&self.shared, |doc| {
            Ok(doc
                .tables(self.index, strategy)?
                .into_iter()
                .map(|table| Table {
                    bbox: bbox(table.bbox),
                    rows: table.rows,
                    row_count: table.row_count,
                    col_count: table.col_count,
                    confidence: table.confidence,
                })
                .collect())
        })
    }

    #[napi]
    pub fn render(&self, options: Option<RenderOptions>) -> Result<Buffer> {
        let render = render_of(options)?;
        with_doc(&self.shared, |doc| doc.render(self.index, &render)).map(Buffer::from)
    }

    #[napi(ts_return_type = "Promise<Buffer>")]
    pub fn render_async(&self, options: Option<RenderOptions>) -> Result<AsyncTask<RenderTask>> {
        Ok(AsyncTask::new(RenderTask {
            shared: Arc::clone(&self.shared),
            index: self.index,
            render: render_of(options)?,
        }))
    }

    /// Add OCR text only where the native text layer is missing or unusable and return the
    /// page text and Markdown including the new invisible layer (the document is modified
    /// in memory). Rejects with `NATIVE_PDF_UNSUPPORTED` when no OCR models are configured.
    #[napi(ts_return_type = "Promise<OcrFillResult>")]
    pub fn ocr_fill_async(&self, options: Option<OcrFillOptions>) -> AsyncTask<OcrFillTask> {
        let options = options.unwrap_or(OcrFillOptions {
            policy: None,
            dpi: None,
            lang: None,
            min_confidence: None,
            model_dir: None,
            threads: None,
            tile_size: None,
            overlap: None,
            table_strategy: None,
        });
        AsyncTask::new(OcrFillTask {
            shared: Arc::clone(&self.shared),
            index: self.index,
            options,
        })
    }
}

pub struct MarkdownTask {
    shared: Shared,
    index: u32,
    strategy: TableStrategy,
}

impl Task for MarkdownTask {
    type Output = String;
    type JsValue = String;

    fn compute(&mut self) -> Result<Self::Output> {
        with_doc(&self.shared, |doc| doc.markdown(self.index, self.strategy))
    }

    fn resolve(&mut self, _env: Env, output: Self::Output) -> Result<Self::JsValue> {
        Ok(output)
    }
}

pub struct RenderTask {
    shared: Shared,
    index: u32,
    render: NativeRender,
}

impl Task for RenderTask {
    type Output = Vec<u8>;
    type JsValue = Buffer;

    fn compute(&mut self) -> Result<Self::Output> {
        let result = with_doc(&self.shared, |doc| doc.render(self.index, &self.render));
        release_heap();
        result
    }

    fn resolve(&mut self, _env: Env, output: Self::Output) -> Result<Self::JsValue> {
        Ok(Buffer::from(output))
    }
}

pub struct OcrFillTask {
    shared: Shared,
    index: u32,
    options: OcrFillOptions,
}

impl OcrFillTask {
    /// Validate options inside the task so bad input rejects the promise instead of throwing.
    fn resolve_options(&self) -> Result<(String, NativeOcrOptions)> {
        let options = &self.options;
        let policy = options.policy.clone().unwrap_or_else(|| "fill".to_owned());
        let adaptive = match policy.as_str() {
            "fill" => false,
            "adaptive" => true,
            other => {
                return Err(Error::new(
                    Status::InvalidArg,
                    format!("[INVALID_ARGUMENT] policy must be 'fill' or 'adaptive': {other:?}"),
                ));
            }
        };
        let defaults = NativeOcrOptions::default();
        Ok((
            policy,
            NativeOcrOptions {
                adaptive,
                dpi: options.dpi.unwrap_or(defaults.dpi),
                min_confidence: options.min_confidence.map(|value| value as f32),
                tile_size: options.tile_size.map_or(defaults.tile_size, |v| v as usize),
                overlap: options.overlap.map_or(defaults.overlap, |v| v as usize),
                table_strategy: strategy_of(options.table_strategy.as_deref())?,
            },
        ))
    }
}

impl Task for OcrFillTask {
    type Output = (NativeOcrFill, &'static str, String);
    type JsValue = OcrFillResult;

    fn compute(&mut self) -> Result<Self::Output> {
        let (policy, ocr) = self.resolve_options()?;
        let engine = NativeOcrEngine::load(
            self.options.model_dir.as_deref(),
            self.options.threads.map(|threads| threads as usize),
        )
        .map_err(fail)?;
        let name = engine.name();
        let filled = with_doc(&self.shared, |doc| doc.ocr_fill(self.index, &engine, &ocr))?;
        release_heap();
        Ok((filled, name, policy))
    }

    fn resolve(
        &mut self,
        _env: Env,
        (filled, engine, policy): Self::Output,
    ) -> Result<Self::JsValue> {
        Ok(OcrFillResult {
            text: filled.text,
            markdown: filled.markdown,
            filled_regions: filled.filled_words,
            engine: engine.to_owned(),
            policy,
            recognized: filled.recognized,
            replaced_pages: filled.replaced_pages,
            regions: filled.regions,
            unmapped_native: filled.unmapped_native,
        })
    }
}
