//! Per-page scan for fast routing probes: positioned text spans with render
//! mode, glyphs lacking Unicode, and image placements read without decoding.
//!
//! One interpretation pass serves both products. Everything here is pure Rust
//! so the Python and Node bindings can share it; Python only converts the
//! owned records. Span grouping is a coarse run segmentation of the raw glyph
//! callback stream (same font, size, render mode, baseline and contiguous
//! advance), not the line/word assembly used by `get_text`.

use super::*;

/// Resource and product selection for one scan.
#[derive(Clone, Copy)]
pub(crate) struct ScanLimits {
    pub(crate) max_text_size: usize,
    pub(crate) max_glyphs: usize,
    pub(crate) max_images: usize,
    pub(crate) spans: bool,
    pub(crate) images: bool,
    /// Image area, as a share of the page, at which an image counts as a text
    /// host for the per-span `over_image` count.
    pub(crate) host_coverage: f64,
}

/// One run of glyphs sharing font, size, render mode and baseline.
pub(crate) struct SpanRecord {
    /// Unicode text. Empty when every glyph lacked a Unicode mapping.
    pub(crate) text: String,
    pub(crate) bbox: BBox,
    pub(crate) font: String,
    pub(crate) size: f64,
    /// pymupdf-compatible font flags (italic 2, serif 4, monospace 8, bold 16).
    pub(crate) flags: i64,
    /// PDF text rendering mode: 0 fill, 1 stroke, 2 fill+stroke, 3 invisible.
    pub(crate) render_mode: u8,
    /// Glyphs without any Unicode mapping (not present in `text`).
    pub(crate) unmapped: u32,
    /// Glyphs in the run, including unmapped ones.
    pub(crate) glyphs: u32,
    pub(crate) type3: bool,
    /// Glyphs whose text is a C0/C1 control character other than TAB/LF/CR.
    pub(crate) control_chars: u32,
    /// Mapped glyphs whose centre lies inside a host image.
    pub(crate) over_image: u32,
    pub(crate) direction: (f64, f64),
}

/// One raster or stencil placement; pixel size comes from the image
/// dictionary, so no pixel data is decoded.
pub(crate) struct ImagePlacement {
    pub(crate) bbox: BBox,
    pub(crate) width_px: u32,
    pub(crate) height_px: u32,
    /// Pixels per inch along the image's own width and height axes.
    pub(crate) dpi_x: f64,
    pub(crate) dpi_y: f64,
    pub(crate) stencil: bool,
}

pub(crate) struct PageScan {
    pub(crate) width: f64,
    pub(crate) height: f64,
    pub(crate) spans: Vec<SpanRecord>,
    pub(crate) images: Vec<ImagePlacement>,
    /// Total glyphs hayro delivered without a Unicode mapping.
    pub(crate) unmapped_glyphs: usize,
    pub(crate) glyph_count: usize,
    pub(crate) text_size: usize,
}

#[derive(Clone, Copy)]
struct Meta {
    mode: u8,
    type3: bool,
    /// Index among all accepted glyphs before ActualText compaction.
    pre_index: usize,
}

#[derive(Clone, Copy, PartialEq)]
enum LastDraw {
    None,
    Mapped,
    Unmapped,
}

struct ScanDevice {
    text: TextCollector,
    meta: Vec<Meta>,
    unmapped: Vec<(usize, GlyphRecord, Meta)>,
    unmapped_fonts: HashMap<u128, FontInfo>,
    images: Vec<ImagePlacement>,
    spans: bool,
    want_images: bool,
    max_images: usize,
    /// Combined glyph transform of the last Fill call, to fold the Stroke half
    /// of render mode 2 into one record.
    last_fill: Option<[f64; 6]>,
    last_kind: LastDraw,
    /// Glyphs delivered so far, mapped and unmapped, before compaction.
    seen: usize,
    limit_error: Option<TextPageLimit>,
}

impl<'a> Device<'a> for ScanDevice {
    fn begin_marked_content(&mut self, tag: &[u8], _: Option<i32>) {
        self.text.marked_begin(tag);
    }
    fn end_marked_content(&mut self) {
        self.text.marked_end();
    }
    fn set_soft_mask(&mut self, _: Option<SoftMask<'a>>) {}
    fn set_blend_mode(&mut self, _: BlendMode) {}
    fn draw_path(&mut self, _: &kurbo::BezPath, _: Affine, _: &Paint<'a>, _: &PathDrawMode) {}
    fn push_clip_path(&mut self, _: &ClipPath) {}
    fn pop_clip_path(&mut self) {}
    fn push_transparency_group(&mut self, _: f32, _: Option<SoftMask<'a>>, _: BlendMode) {}
    fn pop_transparency_group(&mut self) {}

    fn draw_image(&mut self, image: Image<'a, '_>, transform: Affine) {
        if !self.want_images || self.limit_error.is_some() {
            return;
        }
        if self.images.len() >= self.max_images {
            self.limit_error = Some(TextPageLimit::GlyphCount(self.max_images));
            return;
        }
        let (width, height) = (image.width(), image.height());
        if width == 0 || height == 0 {
            return;
        }
        let stencil = matches!(image, Image::Stencil(_));
        // Pixel space maps to display space through `transform`; the length of
        // each basis vector is points per pixel along that image axis.
        let [a, b, c, d, _, _] = transform.as_coeffs();
        let pt_x = (a * a + b * b).sqrt();
        let pt_y = (c * c + d * d).sqrt();
        if !pt_x.is_finite() || !pt_y.is_finite() || pt_x <= 0.0 || pt_y <= 0.0 {
            return;
        }
        let bbox = image_bbox(transform, f64::from(width), f64::from(height));
        if self.images.try_reserve(1).is_err() {
            self.limit_error = Some(TextPageLimit::Allocation("image placements".into()));
            return;
        }
        self.images.push(ImagePlacement {
            bbox,
            width_px: width,
            height_px: height,
            dpi_x: 72.0 / pt_x,
            dpi_y: 72.0 / pt_y,
            stencil,
        });
    }

    fn draw_glyph(
        &mut self,
        glyph: &Glyph<'a>,
        transform: Affine,
        glyph_transform: Affine,
        paint: &Paint<'a>,
        mode: &GlyphDrawMode,
    ) {
        if !self.spans || self.limit_error.is_some() {
            return;
        }
        let combined = transform * glyph_transform;
        let coeffs = combined.as_coeffs();
        if matches!(mode, GlyphDrawMode::Stroke(_)) && self.last_fill == Some(coeffs) {
            match self.last_kind {
                LastDraw::Mapped => {
                    if let Some(meta) = self.meta.last_mut() {
                        meta.mode = 2;
                    }
                }
                LastDraw::Unmapped => {
                    if let Some((_, _, meta)) = self.unmapped.last_mut() {
                        meta.mode = 2;
                    }
                }
                LastDraw::None => {}
            }
            self.last_fill = None;
            return;
        }
        self.last_fill = matches!(mode, GlyphDrawMode::Fill).then_some(coeffs);
        let render_mode = match mode {
            GlyphDrawMode::Fill => 0,
            GlyphDrawMode::Stroke(_) => 1,
            GlyphDrawMode::Invisible => 3,
        };
        let before_glyphs = self.text.glyphs.len();
        let before_skipped = self.text.skipped_no_unicode;
        self.text
            .draw_glyph(glyph, transform, glyph_transform, paint, mode);
        let type3 = matches!(glyph, Glyph::Type3(_));
        if self.text.glyphs.len() > before_glyphs {
            let meta = Meta {
                mode: render_mode,
                type3,
                pre_index: self.seen,
            };
            self.seen += 1;
            if let Err(error) = try_push_text(&mut self.meta, meta, "scan glyph metadata") {
                self.limit_error = Some(error);
            }
            self.last_kind = LastDraw::Mapped;
        } else if self.text.skipped_no_unicode > before_skipped {
            let meta = Meta {
                mode: render_mode,
                type3,
                pre_index: self.seen,
            };
            let record = self.unmapped_record(glyph, combined);
            let entry = (self.seen, record, meta);
            self.seen += 1;
            if let Err(error) = try_push_text(&mut self.unmapped, entry, "unmapped glyph log") {
                self.limit_error = Some(error);
            }
            self.last_kind = LastDraw::Unmapped;
        } else {
            self.last_kind = LastDraw::None;
        }
    }
}

impl ScanDevice {
    /// Build a text-less glyph record carrying only geometry and font identity.
    fn unmapped_record(&mut self, glyph: &Glyph<'_>, combined: Affine) -> GlyphRecord {
        let origin = combined * Point::ZERO;
        let [a, b, c, d, _, _] = combined.as_coeffs();
        let mut size = (c * c + d * d).sqrt() * 1000.0;
        if !size.is_finite() || size <= 0.0 {
            size = 1.0;
        }
        let length = (a * a + b * b).sqrt();
        let direction = if length.is_finite() && length > f64::EPSILON {
            normalize_direction((a / length, b / length))
        } else {
            (1.0, 0.0)
        };
        let (advance_width, font_key, font) = match glyph {
            Glyph::Outline(g) => {
                let key = g.font_cache_key();
                let info = self
                    .unmapped_fonts
                    .entry(key)
                    .or_insert_with(|| font_info_of(g))
                    .clone();
                (g.advance_width().map(f64::from), key, info)
            }
            Glyph::Type3(g) => (g.advance_width().map(f64::from), 0, FontInfo::default()),
        };
        let advance = advance_width
            .map(|adv| {
                let moved = combined * Point::new(adv, 0.0);
                ((moved.x - origin.x).powi(2) + (moved.y - origin.y).powi(2)).sqrt()
            })
            .filter(|a| a.is_finite() && *a > 0.0)
            .unwrap_or(size * 0.5);
        GlyphRecord {
            text: GlyphText::Heap(Box::from("")),
            bidi_flags: 0,
            x: if origin.x.is_finite() { origin.x } else { 0.0 },
            y: if origin.y.is_finite() { origin.y } else { 0.0 },
            size,
            advance,
            direction,
            writing_mode: 0,
            font_key,
            font,
            source_order: self.seen,
            actual_span: NO_ACTUAL_SPAN,
        }
    }
}

/// Whether `next` continues the run that `previous` ended.
fn continues_run(previous: &GlyphRecord, pm: &Meta, next: &GlyphRecord, nm: &Meta) -> bool {
    if previous.font_key != next.font_key || pm.mode != nm.mode || pm.type3 != nm.type3 {
        return false;
    }
    if (previous.size - next.size).abs() > previous.size.max(next.size) * 0.05 {
        return false;
    }
    let (dx, dy) = previous.direction;
    let (nx, ny) = next.direction;
    if (dx * ny - dy * nx).abs() > 1e-3 || dx * nx + dy * ny < 0.0 {
        return false;
    }
    let (ox, oy) = (next.x - previous.x, next.y - previous.y);
    let along = ox * dx + oy * dy;
    let across = -ox * dy + oy * dx;
    if across.abs() > previous.size * 0.1 {
        return false;
    }
    let gap = along - previous.advance;
    gap >= -previous.size * 0.5 && gap <= previous.size * 0.5
}

fn count_controls(text: &GlyphText) -> u32 {
    text.chars()
        .filter(|c| c.is_control() && !matches!(c, '\t' | '\n' | '\r'))
        .count() as u32
}

fn grow(bbox: &mut BBox, add: BBox) {
    bbox.0 = bbox.0.min(add.0);
    bbox.1 = bbox.1.min(add.1);
    bbox.2 = bbox.2.max(add.2);
    bbox.3 = bbox.3.max(add.3);
}

/// Interpret one page once and return spans and/or image placements.
pub(crate) fn scan_page<'a>(
    pdf: &'a Pdf,
    page: &Page<'a>,
    cache: &InterpreterCache<'a>,
    settings: InterpreterSettings,
    limits: ScanLimits,
) -> Result<PageScan, TextPageLimit> {
    let mut context = extraction_context(pdf, page, cache, settings);
    let mut device = ScanDevice {
        text: TextCollector::new(
            page,
            false,
            Some(limits.max_text_size),
            Some(limits.max_glyphs),
        ),
        meta: Vec::new(),
        unmapped: Vec::new(),
        unmapped_fonts: HashMap::new(),
        images: Vec::new(),
        spans: limits.spans,
        want_images: limits.images,
        max_images: limits.max_images,
        last_fill: None,
        last_kind: LastDraw::None,
        seen: 0,
        limit_error: None,
    };
    interpret_page(page, &mut context, &mut device);
    if let Some(error) = device.limit_error {
        return Err(error);
    }
    if let Some(error) = device.text.limit_error {
        return Err(error);
    }
    device.text.apply_actual_text(Some(&mut device.meta))?;
    let (width, height) = page.render_dimensions();
    let (width, height) = (f64::from(width), f64::from(height));

    let host_area = limits.host_coverage * width * height;
    let hosts: Vec<BBox> = device
        .images
        .iter()
        .filter(|image| (image.bbox.2 - image.bbox.0) * (image.bbox.3 - image.bbox.1) >= host_area)
        .map(|image| image.bbox)
        .collect();

    let glyphs = std::mem::take(&mut device.text.glyphs);
    let metas = std::mem::take(&mut device.meta);
    let unmapped = std::mem::take(&mut device.unmapped);
    let glyph_count = glyphs.len() + unmapped.len();
    let mut spans: Vec<SpanRecord> = Vec::new();
    // Merge mapped glyphs with the unmapped log in callback order.
    let mut mapped = glyphs.iter().zip(metas.iter()).peekable();
    let mut missing = unmapped.iter().peekable();
    let mut previous: Option<(&GlyphRecord, &Meta)> = None;
    loop {
        let take_missing = match (mapped.peek(), missing.peek()) {
            (None, None) => break,
            (Some(_), None) => false,
            (None, Some(_)) => true,
            (Some((_, meta)), Some((before, _, _))) => *before <= meta.pre_index,
        };
        let (glyph, meta, is_unmapped) = if take_missing {
            let (_, record, meta) = missing.next().expect("peeked");
            (record, meta, true)
        } else {
            let (record, meta) = mapped.next().expect("peeked");
            (record, meta, false)
        };
        let extend = previous.is_some_and(|(pg, pm)| continues_run(pg, pm, glyph, meta));
        let bbox = glyph_bbox(glyph);
        if !extend {
            let mut font = String::new();
            try_push_str_text(&mut font, &glyph.font.name, "scan font name")?;
            spans.try_reserve(1).map_err(|error| {
                TextPageLimit::Allocation(format!("failed to grow scan spans: {error}"))
            })?;
            spans.push(SpanRecord {
                text: String::new(),
                bbox,
                font,
                size: glyph.size,
                flags: glyph.font.flags,
                render_mode: meta.mode,
                unmapped: 0,
                glyphs: 0,
                type3: meta.type3,
                control_chars: 0,
                over_image: 0,
                direction: glyph.direction,
            });
        }
        let span = spans.last_mut().expect("span exists");
        grow(&mut span.bbox, bbox);
        span.glyphs += 1;
        if is_unmapped {
            span.unmapped += 1;
        } else {
            try_push_glyph_text(&mut span.text, &glyph.text, "scan span text")?;
            span.control_chars += count_controls(&glyph.text);
            let (cx, cy) = ((bbox.0 + bbox.2) / 2.0, (bbox.1 + bbox.3) / 2.0);
            if hosts
                .iter()
                .any(|h| h.0 <= cx && cx <= h.2 && h.1 <= cy && cy <= h.3)
            {
                span.over_image += 1;
            }
        }
        previous = Some((glyph, meta));
    }
    Ok(PageScan {
        width,
        height,
        spans,
        images: std::mem::take(&mut device.images),
        unmapped_glyphs: device.text.skipped_no_unicode,
        glyph_count,
        text_size: device.text.text_size,
    })
}
