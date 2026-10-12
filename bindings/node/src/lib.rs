//! N-API binding for the pdfust Rust core.
//!
//! The shape follows the frozen `PdfustNode` adapter interface. Errors carry a
//! `[CODE] message` prefix that `index.js` turns into `error.code`.

#![deny(clippy::all)]

use std::sync::{Arc, Mutex};

use napi::bindgen_prelude::*;
use napi_derive::napi;
use pdfust::document::native::{
    ImageFormat, NativeDoc, NativeError, NativeLimits, NativeRender, TableStrategy,
};

type Shared = Arc<Mutex<Option<NativeDoc>>>;

fn fail(error: NativeError) -> Error {
    let limit = error.limit.map(|limit| format!(":{limit}")).unwrap_or_default();
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

fn unsupported(method: &str) -> Error {
    Error::new(
        Status::GenericFailure,
        format!("[NATIVE_PDF_UNSUPPORTED] {method} is not implemented by this binding"),
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
    value.filter(|value| value.is_finite() && *value >= 0.0).map(|value| value as usize)
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
    #[napi(ts_type = "'web'")]
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
    options.as_ref().and_then(|options| options.password.as_deref())
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
            "ocr:unsupported",
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
    pub name: String,
    pub visible: bool,
}

#[napi(object)]
pub struct Attachment {
    pub name: String,
    pub size: f64,
}

#[napi(object)]
pub struct FontInfo {
    pub name: String,
    pub r#type: String,
    pub embedded: bool,
    pub has_to_unicode: bool,
    pub is_type3: bool,
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
        with_doc(&self.shared, |doc| Ok(doc.has_java_script()))
    }

    #[napi]
    pub fn optional_content(&self) -> Result<Vec<OptionalContentGroup>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .optional_content()
                .into_iter()
                .map(|(name, visible)| OptionalContentGroup { name, visible })
                .collect())
        })
    }

    #[napi]
    pub fn attachments(&self) -> Result<Vec<Attachment>> {
        with_doc(&self.shared, |doc| {
            Ok(doc
                .attachments()?
                .into_iter()
                .map(|(name, size)| Attachment {
                    name,
                    size: size as f64,
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
                    name: font.name,
                    r#type: font.kind,
                    embedded: font.embedded,
                    has_to_unicode: font.has_to_unicode,
                    is_type3: font.is_type3,
                })
                .collect())
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
pub struct Drawings {
    pub line_count: u32,
    pub rect_count: u32,
    pub long_rule_count: u32,
    pub path_count: u32,
    pub vector_area: f64,
}

#[napi(object)]
pub struct Widget {
    pub kind: String,
    pub name: Option<String>,
    pub value: Option<String>,
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
    #[napi(ts_type = "'fill' | 'adaptive'")]
    pub policy: Option<String>,
    pub dpi: Option<f64>,
    pub lang: Option<String>,
}

#[napi(object)]
pub struct OcrFillResult {
    pub text: String,
    pub markdown: String,
    pub filled_regions: u32,
    pub engine: String,
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
    pub fn markdown_async(&self, options: Option<MarkdownOptions>) -> Result<AsyncTask<MarkdownTask>> {
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
                path_count: stats.path_count,
                vector_area: stats.vector_area,
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

    /// OCR fill is not available in this binding yet; throws `NATIVE_PDF_UNSUPPORTED`.
    #[napi(ts_return_type = "Promise<OcrFillResult>")]
    pub fn ocr_fill_async(
        &self,
        _options: Option<OcrFillOptions>,
    ) -> AsyncTask<UnsupportedTask> {
        AsyncTask::new(UnsupportedTask)
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
        with_doc(&self.shared, |doc| doc.render(self.index, &self.render))
    }

    fn resolve(&mut self, _env: Env, output: Self::Output) -> Result<Self::JsValue> {
        Ok(Buffer::from(output))
    }
}

pub struct UnsupportedTask;

impl Task for UnsupportedTask {
    type Output = ();
    type JsValue = OcrFillResult;

    fn compute(&mut self) -> Result<Self::Output> {
        Err(unsupported("ocrFillAsync"))
    }

    fn resolve(&mut self, _env: Env, _output: Self::Output) -> Result<Self::JsValue> {
        Err(unsupported("ocrFillAsync"))
    }
}
