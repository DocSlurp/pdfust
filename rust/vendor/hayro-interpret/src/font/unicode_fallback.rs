//! Glyph to Unicode recovery for fonts whose `ToUnicode` map is missing or incomplete.
//!
//! (Local pdfust patch.) When a PDF provides no Unicode for a glyph, extractors such as
//! pdf.js, MuPDF and Poppler consult the embedded font program. This module builds that
//! reverse map once per font: PostScript glyph names (`post` or CFF charset) resolved with
//! the Adobe Glyph List rules, then the font's own Unicode `cmap` subtables. A mapping is
//! only reported when the font itself says what the glyph is; nothing is guessed.

use crate::font::generated::glyph_names;
use hayro_cmap::BfString;
use skrifa::GlyphId;
use skrifa::raw::TableProvider;
use skrifa::raw::tables::cmap::{CmapSubtable, PlatformId};
use std::collections::HashMap;

/// Resolve a PostScript glyph name to text following the Adobe Glyph List specification.
///
/// Handles `name.suffix` (suffix dropped), `a_b` ligature components, `uniXXXX[XXXX..]`
/// and `uXXXX[XX]`. Returns `None` for names that carry no Unicode (`glyph00012`, `g31`,
/// `cid00123`, `.notdef`).
pub(crate) fn glyph_name_to_text(name: &str) -> Option<String> {
    let base = name.split('.').next().unwrap_or_default();
    if base.is_empty() {
        return None;
    }
    let mut out = String::new();
    for component in base.split('_') {
        if component.is_empty() {
            return None;
        }
        if let Some(text) = glyph_names::get(component) {
            out.push_str(text);
        } else if let Some(hex) = component.strip_prefix("uni")
            && hex.len() >= 4
            && hex.len() % 4 == 0
            && hex.bytes().all(|b| b.is_ascii_hexdigit())
        {
            for chunk in hex.as_bytes().chunks(4) {
                let code = u32::from_str_radix(std::str::from_utf8(chunk).ok()?, 16).ok()?;
                // Surrogates are not valid scalar values; the spec excludes them.
                out.push(char::from_u32(code)?);
            }
        } else if let Some(hex) = component.strip_prefix('u')
            && (4..=6).contains(&hex.len())
            && hex.bytes().all(|b| b.is_ascii_hexdigit())
        {
            out.push(char::from_u32(u32::from_str_radix(hex, 16).ok()?)?);
        } else {
            return None;
        }
    }
    usable(out)
}

/// Keep only text that can stand for a glyph: non-empty, no NUL, no U+FFFD and no
/// private-use code points (names such as `uniF001` are producer-internal glyph ids).
fn usable(text: String) -> Option<String> {
    (!text.is_empty()
        && !text
            .chars()
            .any(|c| c == '\0' || c == '\u{FFFD}' || is_private_use(c as u32)))
    .then_some(text)
}

pub(crate) fn to_bf_string(text: String) -> BfString {
    let mut chars = text.chars();
    match (chars.next(), chars.next()) {
        (Some(c), None) => BfString::Char(c),
        _ => BfString::String(text),
    }
}

fn is_private_use(code: u32) -> bool {
    matches!(code, 0xE000..=0xF8FF | 0xF0000..=0xFFFFD | 0x100000..=0x10FFFD)
}

/// Record every `cmap` code point per glyph into `map`, never overriding existing entries.
///
/// The lowest code point wins; private-use code points are ignored because they say
/// nothing about the character.
pub(crate) fn add_cmap_reverse(
    font: &skrifa::FontRef<'_>,
    map: &mut HashMap<GlyphId, String>,
) {
    let Ok(cmap) = font.cmap() else {
        return;
    };
    let glyph_count = font.maxp().map(|m| m.num_glyphs() as u32).unwrap_or(u16::MAX as u32);
    let mut best: HashMap<GlyphId, u32> = HashMap::new();
    for record in cmap.encoding_records() {
        let unicode = match record.platform_id() {
            PlatformId::Unicode => true,
            PlatformId::Windows => matches!(record.encoding_id(), 1 | 10),
            _ => false,
        };
        if !unicode {
            continue;
        }
        let Ok(subtable) = record.subtable(cmap.offset_data()) else {
            continue;
        };
        // Format 14 holds variation selectors only.
        if matches!(subtable, CmapSubtable::Format14(_)) {
            continue;
        }
        let limits = skrifa::raw::tables::cmap::CmapIterLimits {
            max_char: char::MAX as u32,
            glyph_count,
        };
        for (code, gid) in subtable.iter_with_limits(limits) {
            if gid == GlyphId::NOTDEF
                || code < 0x20
                || char::from_u32(code).is_none()
                || is_private_use(code)
            {
                continue;
            }
            if map.contains_key(&gid) {
                continue;
            }
            match best.get(&gid) {
                Some(&existing) if existing <= code => {}
                _ => {
                    best.insert(gid, code);
                }
            }
        }
    }
    for (gid, code) in best {
        if let Some(c) = char::from_u32(code) {
            map.insert(gid, c.to_string());
        }
    }
}
