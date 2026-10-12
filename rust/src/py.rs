//! Python-or-plain-Rust facade for the document engine.
//!
//! With the `python` feature (the wheel build) this re-exports PyO3 unchanged.
//! Without it (the Node binding) it provides the small subset the engine uses:
//! an error type, a result alias, a GIL-less `Python` token and no-op attribute
//! macros, so one body of Rust serves both bindings.

#[cfg(feature = "python")]
pub use pyo3::exceptions::{PyTypeError, PyValueError};
#[cfg(feature = "python")]
pub use pyo3::prelude::*;

#[cfg(not(feature = "python"))]
pub use pdfust_shim::*;
#[cfg(not(feature = "python"))]
pub use plain::*;

/// Define an exception class: `pyo3::create_exception!` under Python, a plain
/// error constructor otherwise.
#[cfg(feature = "python")]
macro_rules! define_exception {
    ($name:ident, $base:ident, $doc:literal) => {
        pyo3::create_exception!(pdfust, $name, $base, $doc);
    };
}
#[cfg(not(feature = "python"))]
macro_rules! define_exception {
    ($name:ident, $base:ident, $doc:literal) => {
        #[doc = $doc]
        pub struct $name;
        impl $name {
            pub fn new_err(args: impl crate::py::ErrArgs) -> crate::py::PyErr {
                crate::py::PyErr::from_args(stringify!($name), args)
            }
        }
    };
}
pub(crate) use define_exception;

#[cfg(not(feature = "python"))]
mod plain {
    use std::marker::PhantomData;

    /// Constructor arguments accepted by `Exception::new_err`.
    pub trait ErrArgs {
        fn into_parts(self) -> (Option<&'static str>, String);
    }
    impl ErrArgs for String {
        fn into_parts(self) -> (Option<&'static str>, String) {
            (None, self)
        }
    }
    impl ErrArgs for &str {
        fn into_parts(self) -> (Option<&'static str>, String) {
            (None, self.to_owned())
        }
    }
    impl ErrArgs for (&'static str, String) {
        fn into_parts(self) -> (Option<&'static str>, String) {
            (Some(self.0), self.1)
        }
    }

    /// Engine error: exception class name, optional stable limit code, message.
    #[derive(Debug, Clone)]
    pub struct PyErr {
        pub class: &'static str,
        pub code: Option<&'static str>,
        pub message: String,
    }

    impl PyErr {
        pub fn from_args(class: &'static str, args: impl ErrArgs) -> Self {
            let (code, message) = args.into_parts();
            Self {
                class,
                code,
                message,
            }
        }
    }

    impl std::fmt::Display for PyErr {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.write_str(&self.message)
        }
    }
    impl std::error::Error for PyErr {}

    pub type PyResult<T> = Result<T, PyErr>;

    macro_rules! plain_exception {
        ($($name:ident),*) => {$(
            pub struct $name;
            impl $name {
                pub fn new_err(args: impl ErrArgs) -> PyErr {
                    PyErr::from_args(stringify!($name), args)
                }
            }
        )*};
    }
    plain_exception!(PyValueError, PyTypeError, PyBufferError);

    /// Stand-in for the interpreter token; work is never detached.
    #[derive(Clone, Copy)]
    pub struct Python<'py>(PhantomData<&'py ()>);

    impl<'py> Python<'py> {
        /// Token for callers that have no interpreter.
        pub fn none() -> Self {
            Python(PhantomData)
        }
        pub fn detach<T, F: FnOnce() -> T>(self, f: F) -> T {
            f()
        }
    }
}
