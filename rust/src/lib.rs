#![cfg_attr(not(feature = "python"), allow(dead_code, unused_imports))]
#[cfg(feature = "python")]
use pyo3::prelude::*;
pub(crate) mod py;
mod actual_text;
mod cjk_radicals;
pub mod document;
mod draw;
mod extract;
mod font_cache;
mod form;
mod generate;
mod image_compression;
mod inspect;
mod layout;
pub mod markdown;
mod ocr;
#[cfg(all(feature = "python", not(target_os = "emscripten")))]
mod ocr_engine;
#[cfg(all(feature = "python", target_os = "emscripten"))]
#[path = "ocr_engine_emscripten.rs"]
mod ocr_engine;
#[cfg_attr(not(feature = "python"), allow(dead_code))]
mod pixmap;
#[cfg(feature = "python")]
mod python_writer;
mod text_replace;
#[cfg(feature = "python")]
use document::{_Document, LimitError, PasswordError, PdfError, UnsupportedEncryptionError};
#[cfg(feature = "python")]
use ocr_engine::{_OcrEngine, OcrError};
#[cfg(feature = "python")]
use pixmap::Pixmap;

#[cfg(feature = "python")]
#[pymodule(gil_used = false)]
fn pdfust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<_Document>()?;
    m.add_class::<_OcrEngine>()?;
    m.add_class::<Pixmap>()?;
    m.add("PdfError", m.py().get_type::<PdfError>())?;
    m.add("LimitError", m.py().get_type::<LimitError>())?;
    m.add("PasswordError", m.py().get_type::<PasswordError>())?;
    m.add("UnsupportedEncryptionError", m.py().get_type::<UnsupportedEncryptionError>())?;
    m.add("OcrError", m.py().get_type::<OcrError>())?;
    Ok(())
}
