//! Invisible OCR text-layer primitives for searchable PDFs.
//!
//! Following ocrmypdf's approach, assign a CID to each character in a
//! non-embedded Identity-H font with a ToUnicode CMap, then write text in
//! invisible rendering mode (`Tr 3`). It appears only through extraction and
//! search, and adds almost no file size in any language.

use std::collections::HashMap;
use std::fmt::{self, Write};

use lopdf::{Dictionary, Document, Object, ObjectId, Stream, dictionary};

use crate::draw;

/// One OCR word: display-coordinate bbox plus text.
pub type OcrWord = (f64, f64, f64, f64, String);

const MAX_OCR_CIDS: usize = 65_534;

/// Format directly into fallibly grown storage before any PDF mutation.
#[derive(Default)]
struct OcrText(String);

impl Write for OcrText {
    fn write_str(&mut self, text: &str) -> fmt::Result {
        self.0.try_reserve(text.len()).map_err(|_| fmt::Error)?;
        self.0.push_str(text);
        Ok(())
    }
}

fn output_error(_: fmt::Error) -> String {
    "failed to allocate OCR layer output".to_owned()
}

/// Assign one-based CIDs to all characters; CID 0 is `.notdef`.
pub fn assign_cids(words: &[OcrWord]) -> Result<HashMap<char, u16>, String> {
    let mut map = HashMap::new();
    for (_, _, _, _, text) in words {
        for ch in text.chars() {
            if map.contains_key(&ch) {
                continue;
            }
            if map.len() >= MAX_OCR_CIDS {
                return Err(
                    "too many distinct characters for the OCR layer (max 65,534 per call)"
                        .to_owned(),
                );
            }
            let cid =
                u16::try_from(map.len() + 1).expect("the OCR CID count is bounded below u16::MAX");
            map.try_reserve(1)
                .map_err(|error| format!("failed to grow OCR character map: {error}"))?;
            map.insert(ch, cid);
        }
    }
    Ok(map)
}

/// Build a CID-to-Unicode UTF-16BE ToUnicode CMap.
///
/// Split `bfchar` into specification-compliant blocks of 100 entries.
pub fn build_to_unicode(cid_map: &HashMap<char, u16>) -> Result<Vec<u8>, String> {
    let mut entries = Vec::new();
    entries
        .try_reserve_exact(cid_map.len())
        .map_err(|error| format!("failed to allocate OCR Unicode entries: {error}"))?;
    entries.extend(cid_map.iter().map(|(&ch, &cid)| (cid, ch)));
    entries.sort_unstable();
    let mut out = OcrText::default();
    out.write_str(
        "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n\
         /CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n\
         /CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n\
         1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n",
    )
    .map_err(output_error)?;
    for block in entries.chunks(100) {
        writeln!(out, "{} beginbfchar", block.len()).map_err(output_error)?;
        for &(cid, ch) in block {
            write!(out, "<{cid:04X}> <").map_err(output_error)?;
            let mut buf = [0u16; 2];
            for unit in ch.encode_utf16(&mut buf) {
                write!(out, "{unit:04X}").map_err(output_error)?;
            }
            out.write_str(">\n").map_err(output_error)?;
        }
        out.write_str("endbfchar\n").map_err(output_error)?;
    }
    out.write_str("endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n")
        .map_err(output_error)?;
    Ok(out.0.into_bytes())
}

/// Add the Type0/CIDFontType2/FontDescriptor/ToUnicode set for the OCR layer.
///
/// No FontFile is embedded. Every CID uses DW=1000 (1 em); a horizontal text
/// matrix scale fits each word to its actual width.
pub fn add_ocr_font(doc: &mut Document, to_unicode_data: Vec<u8>) -> ObjectId {
    let to_unicode =
        doc.add_object(Stream::new(Dictionary::new(), to_unicode_data).with_compression(false));
    let descriptor = doc.add_object(dictionary! {
        "Type" => "FontDescriptor",
        "FontName" => "PyloOCR-Gothic",
        "Flags" => 4,
        "FontBBox" => Object::Array(vec![0.into(), (-200).into(), 1000.into(), 800.into()]),
        "ItalicAngle" => 0,
        "Ascent" => 800,
        "Descent" => -200,
        "CapHeight" => 800,
        "StemV" => 80,
    });
    let cid_font = doc.add_object(dictionary! {
        "Type" => "Font",
        "Subtype" => "CIDFontType2",
        "BaseFont" => "PyloOCR-Gothic",
        "CIDSystemInfo" => dictionary! {
            "Registry" => Object::string_literal("Adobe"),
            "Ordering" => Object::string_literal("Identity"),
            "Supplement" => 0,
        },
        "FontDescriptor" => descriptor,
        "DW" => 1000,
        "CIDToGIDMap" => "Identity",
    });
    doc.add_object(dictionary! {
        "Type" => "Font",
        "Subtype" => "Type0",
        "BaseFont" => "PyloOCR-Gothic",
        "Encoding" => "Identity-H",
        "DescendantFonts" => vec![Object::Reference(cid_font)],
        "ToUnicode" => to_unicode,
    })
}

/// Build drawing operators for invisible text (`Tr 3`).
///
/// Font size follows the bbox cross-axis, the baseline sits one 0.2 descent
/// ratio inside the box, and horizontal scale fits the along-axis length.
pub fn ocr_ops(
    crop: [f64; 4],
    page_rotation: i64,
    words: &[OcrWord],
    cid_map: &HashMap<char, u16>,
    font_name: &str,
    text_rotation: u16,
) -> Result<Vec<u8>, String> {
    let mut out = OcrText::default();
    out.write_str("q\n").map_err(output_error)?;
    for (x0, y0, x1, y1, text) in words {
        let (w, h) = (x1 - x0, y1 - y0);
        #[allow(clippy::cast_precision_loss)]
        let chars = text.chars().count() as f64;
        let (origin, baseline, up, font_size, line_length) = match text_rotation {
            90 => ((x1 - 0.2 * w, *y1), (0.0, -1.0), (-1.0, 0.0), w, h),
            180 => ((*x1, y0 + 0.2 * h), (-1.0, 0.0), (0.0, 1.0), h, w),
            270 => ((x0 + 0.2 * w, *y0), (0.0, 1.0), (1.0, 0.0), w, h),
            _ => ((*x0, y1 - 0.2 * h), (1.0, 0.0), (0.0, -1.0), h, w),
        };
        let (ox, oy) = draw::display_to_pdf(crop, page_rotation, origin.0, origin.1);
        let (rx, ry) = {
            let p = draw::display_to_pdf(
                crop,
                page_rotation,
                origin.0 + baseline.0,
                origin.1 + baseline.1,
            );
            (p.0 - ox, p.1 - oy)
        };
        let (ux, uy) = {
            let p = draw::display_to_pdf(crop, page_rotation, origin.0 + up.0, origin.1 + up.1);
            (p.0 - ox, p.1 - oy)
        };
        // Scale the natural width of one em per character to the bbox width.
        let sx = line_length / (chars * font_size);
        write!(
            out,
            "BT\n/{font_name} {} Tf\n3 Tr\n{} {} {} {} {} {} Tm\n<",
            draw::fmt(font_size),
            draw::fmt(sx * rx),
            draw::fmt(sx * ry),
            draw::fmt(ux),
            draw::fmt(uy),
            draw::fmt(ox),
            draw::fmt(oy),
        )
        .map_err(output_error)?;
        for ch in text.chars() {
            let cid = cid_map.get(&ch).copied().unwrap_or(0);
            write!(out, "{cid:04X}").map_err(output_error)?;
        }
        out.write_str("> Tj\nET\n").map_err(output_error)?;
    }
    out.write_str("Q\n").map_err(output_error)?;
    Ok(out.0.into_bytes())
}

/// Which recognized words an OCR-fill pass should insert.
pub struct FillSelection {
    /// The native layer is unusable (glyphs without Unicode and fewer native
    /// than half as many characters as recognized), so every word is kept.
    pub replace_page: bool,
    /// Indexes into the recognized words to insert, in input order.
    pub keep: Vec<usize>,
}

/// Choose OCR words that add text the native layer lacks.
///
/// A recognized box is dropped when it contains the centre of any native word
/// (widened by `slack` points), because OCR boxes are usually whole lines while
/// native boxes approximate glyph bodies. When `unmapped_native` is set and the
/// native characters are fewer than `unreliable_ratio` times the recognized
/// characters (spaces excluded), the native layer cannot gate OCR and every
/// word is kept.
pub fn select_fill_words(
    native_boxes: &[[f64; 4]],
    native_chars: usize,
    unmapped_native: bool,
    ocr: &[OcrWord],
    slack: f64,
    unreliable_ratio: f64,
) -> FillSelection {
    let ocr_chars: usize = ocr
        .iter()
        .map(|(_, _, _, _, text)| text.chars().filter(|c| *c != ' ').count())
        .sum();
    if unmapped_native && (native_chars as f64) < unreliable_ratio * ocr_chars as f64 {
        return FillSelection {
            replace_page: true,
            keep: (0..ocr.len()).collect(),
        };
    }
    let centres: Vec<(f64, f64)> = native_boxes
        .iter()
        .map(|b| ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0))
        .collect();
    let keep = ocr
        .iter()
        .enumerate()
        .filter(|(_, (x0, y0, x1, y1, _))| {
            !centres.iter().any(|(cx, cy)| {
                *x0 - slack <= *cx && *cx <= *x1 + slack && *y0 - slack <= *cy && *cy <= *y1 + slack
            })
        })
        .map(|(index, _)| index)
        .collect();
    FillSelection {
        replace_page: false,
        keep,
    }
}
