//! Page-level `/ActualText` marked-content spans for text extraction.
//!
//! hayro's `Device` receives only a marked-content tag and MCID, not the
//! property dictionary. Producers such as Chromium/Skia map contextual glyphs
//! (Arabic joining forms, Devanagari conjuncts, Thai clusters) to U+0000 in
//! ToUnicode and carry the real text in `/Span << /ActualText (...) >> BDC`.
//! This module pre-scans the page content stream with hayro's own parser so
//! the collector can match each begin event, in order, to its ActualText.
//! Inline property dictionaries are supported; named `/Properties` resources
//! are counted but carry no text. Callers must verify that the interpreter
//! reported exactly the scanned begin events before applying any replacement.

use hayro::hayro_syntax::content::ops::TypedInstruction;
use hayro::hayro_syntax::object::String as PdfString;
use hayro::hayro_syntax::object::{Dict, Name, Stream};
use hayro::hayro_syntax::page::Page;

/// Begin events retained per page before the scan gives up.
const MAX_MARKED_EVENTS: usize = 65_536;
/// Decoded ActualText bytes retained per page before the scan gives up.
const MAX_ACTUAL_TEXT_BYTES: usize = 1_048_576;
/// Marker searched in decoded content before any instruction parsing.
const ACTUAL_TEXT_KEY: &[u8] = b"ActualText";

/// One BMC/BDC begin event in content order.
pub(crate) struct MarkedEvent {
    pub(crate) tag: Box<[u8]>,
    pub(crate) actual_text: Option<Box<str>>,
}

/// Scan a page for marked-content events when any ActualText is present.
///
/// Returns `None` when the page has no ActualText, when a bound is exceeded,
/// or when allocation fails, so extraction falls back to glyph Unicode.
pub(crate) fn scan(page: &Page<'_>) -> Option<Vec<MarkedEvent>> {
    let stream = page.page_stream()?;
    if !stream
        .windows(ACTUAL_TEXT_KEY.len())
        .any(|window| window == ACTUAL_TEXT_KEY)
    {
        return None;
    }
    let mut events: Vec<MarkedEvent> = Vec::new();
    let mut text_bytes = 0usize;
    let mut any_text = false;
    // TypedIter lends each instruction from its operand stack.
    let mut instructions = page.typed_operations();
    while let Some(instruction) = instructions.next() {
        let (tag, actual_text) = match instruction {
            TypedInstruction::BeginMarkedContent(bmc) => (bmc.0.as_ref(), None),
            TypedInstruction::BeginMarkedContentWithProperties(bdc) => {
                let text = bdc
                    .1
                    .clone()
                    .into_dict()
                    .and_then(|props| props.get::<PdfString<'_>>(ACTUAL_TEXT_KEY))
                    .and_then(|value| decode_text_string(value.as_bytes()));
                (bdc.0.as_ref(), text)
            }
            _ => continue,
        };
        if events.len() >= MAX_MARKED_EVENTS {
            return None;
        }
        if let Some(text) = &actual_text {
            text_bytes = text_bytes.checked_add(text.len())?;
            if text_bytes > MAX_ACTUAL_TEXT_BYTES {
                return None;
            }
            any_text = true;
        }
        let mut owned_tag = Vec::new();
        owned_tag.try_reserve_exact(tag.len()).ok()?;
        owned_tag.extend_from_slice(tag);
        if events.len() == events.capacity() {
            events.try_reserve(1).ok()?;
        }
        events.push(MarkedEvent {
            tag: owned_tag.into_boxed_slice(),
            actual_text,
        });
    }
    any_text.then_some(events)
}

/// Decode a PDF text string: UTF-16BE/LE with BOM, UTF-8 with BOM (PDF 2.0),
/// or PDFDocEncoding approximated by Latin-1 for its printable range.
fn decode_text_string(bytes: &[u8]) -> Option<Box<str>> {
    let mut text = String::new();
    if let Some(rest) = bytes.strip_prefix(&[0xFE, 0xFF]) {
        let units = rest
            .as_chunks::<2>()
            .0
            .iter()
            .map(|pair| u16::from_be_bytes(*pair));
        push_utf16(&mut text, units, rest.len())?;
    } else if let Some(rest) = bytes.strip_prefix(&[0xFF, 0xFE]) {
        let units = rest
            .as_chunks::<2>()
            .0
            .iter()
            .map(|pair| u16::from_le_bytes(*pair));
        push_utf16(&mut text, units, rest.len())?;
    } else if let Some(rest) = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]) {
        let decoded = std::str::from_utf8(rest).ok()?;
        text.try_reserve_exact(decoded.len()).ok()?;
        text.push_str(decoded);
    } else {
        text.try_reserve_exact(bytes.len().checked_mul(2)?).ok()?;
        text.extend(bytes.iter().map(|&byte| char::from(byte)));
    }
    // Control characters other than whitespace never carry readable text.
    if text.chars().any(|c| c.is_control() && !c.is_whitespace()) {
        return None;
    }
    Some(text.into_boxed_str())
}

fn push_utf16(text: &mut String, units: impl Iterator<Item = u16>, byte_len: usize) -> Option<()> {
    // Each UTF-16 unit yields at most three UTF-8 bytes.
    text.try_reserve_exact((byte_len / 2).checked_mul(3)?)
        .ok()?;
    for decoded in char::decode_utf16(units) {
        text.push(decoded.unwrap_or(char::REPLACEMENT_CHARACTER));
    }
    Some(())
}

/// Form XObjects visited per page by [`forms_mention_actual_text`].
const MAX_FORMS: usize = 64;
/// Decoded form bytes inspected per page.
const MAX_FORM_BYTES: usize = 8 * 1024 * 1024;
/// Form nesting followed from the page resources.
const MAX_FORM_DEPTH: usize = 4;

/// Whether any Form XObject reachable from the page resources mentions `/ActualText`.
///
/// The collector only matches page-level marked content ([`scan`]); ActualText inside a
/// form is invisible to it. Glyph-level Unicode recovery from the font program would then
/// add text for glyphs the producer deliberately left unmapped, so callers disable that
/// recovery on such pages. Bounded; reports `true` (the conservative answer) when a bound is hit.
pub(crate) fn forms_mention_actual_text(page: &Page<'_>) -> bool {
    let mut visited: Vec<u128> = Vec::new();
    let mut bytes = 0usize;
    walk_forms(&page.resources().x_objects, 0, &mut visited, &mut bytes)
}

fn walk_forms(
    x_objects: &Dict<'_>,
    depth: usize,
    visited: &mut Vec<u128>,
    bytes: &mut usize,
) -> bool {
    for (name, _) in x_objects.entries() {
        let Some(form) = x_objects.get::<Stream<'_>>(name.as_ref()) else {
            continue;
        };
        if form
            .dict()
            .get::<Name<'_>>(b"Subtype")
            .is_none_or(|s| s.as_ref() != &b"Form"[..])
        {
            continue;
        }
        let id = form.obj_id();
        let key = u128::from(id.obj_number as u64) << 32 | u128::from(id.gen_number as u64);
        if visited.contains(&key) {
            continue;
        }
        if visited.len() >= MAX_FORMS || depth >= MAX_FORM_DEPTH {
            return true;
        }
        visited.push(key);
        let Ok(data) = form.decoded() else {
            continue;
        };
        *bytes = bytes.saturating_add(data.len());
        if *bytes > MAX_FORM_BYTES
            || data
                .windows(ACTUAL_TEXT_KEY.len())
                .any(|w| w == ACTUAL_TEXT_KEY)
        {
            return true;
        }
        if let Some(resources) = form.dict().get::<Dict<'_>>(b"Resources")
            && let Some(nested) = resources.get::<Dict<'_>>(b"XObject")
            && walk_forms(&nested, depth + 1, visited, bytes)
        {
            return true;
        }
    }
    false
}
