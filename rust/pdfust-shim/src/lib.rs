//! No-op replacements for the PyO3 attribute macros.
//!
//! `pdfust-core` keeps its document engine in `#[pymethods]` blocks. When the
//! `python` feature is off (the Node binding), these attributes pass the item
//! through unchanged so the same Rust source compiles without PyO3 or libpython.

use proc_macro::TokenStream;

macro_rules! passthrough {
    ($($name:ident),* $(,)?) => {
        $(
            #[proc_macro_attribute]
            pub fn $name(_attr: TokenStream, item: TokenStream) -> TokenStream {
                item
            }
        )*
    };
}

passthrough!(pyclass, pymethods, pyo3, staticmethod, classmethod, new, getter, setter, pyfunction);
