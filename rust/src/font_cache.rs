//! Weak sharing for immutable bundled locale font bytes across Documents.

#[cfg(unix)]
use std::os::unix::fs::MetadataExt;
#[cfg(windows)]
use std::os::windows::fs::MetadataExt;
use std::{
    fs::{self, Metadata},
    path::PathBuf,
    sync::{Arc, Mutex, Weak},
    time::SystemTime,
};

use crate::py::PyResult;

use crate::document::{PdfError, read_font_input, validate_font_input};

const MAX_SHARED_FONTS: usize = 8;
static SHARED_FONTS: Mutex<Vec<FontEntry>> = Mutex::new(Vec::new());

#[derive(PartialEq, Eq)]
struct FontIdentity {
    path: PathBuf,
    size: u64,
    modified: Option<SystemTime>,
    #[cfg(unix)]
    device: u64,
    #[cfg(unix)]
    inode: u64,
    #[cfg(unix)]
    changed: (i64, i64),
    #[cfg(windows)]
    created: u64,
}

struct FontEntry {
    identity: FontIdentity,
    data: Weak<Vec<u8>>,
}

fn identity(path: &str) -> PyResult<FontIdentity> {
    let canonical = fs::canonicalize(path).map_err(|error| {
        PdfError::new_err(format!("failed to locate bundled font {path}: {error}"))
    })?;
    let metadata = fs::metadata(&canonical).map_err(|error| {
        PdfError::new_err(format!("failed to inspect bundled font {path}: {error}"))
    })?;
    Ok(metadata_identity(canonical, metadata))
}

fn metadata_identity(path: PathBuf, metadata: Metadata) -> FontIdentity {
    FontIdentity {
        path,
        size: metadata.len(),
        modified: metadata.modified().ok(),
        #[cfg(unix)]
        device: metadata.dev(),
        #[cfg(unix)]
        inode: metadata.ino(),
        #[cfg(unix)]
        changed: (metadata.ctime(), metadata.ctime_nsec()),
        #[cfg(windows)]
        created: metadata.creation_time(),
    }
}

/// Share only still-live bytes with an unchanged file identity.
/// Explicit user font setters deliberately bypass this registry.
pub(crate) fn read_shared_font(path: &str, max_size: Option<usize>) -> PyResult<Arc<Vec<u8>>> {
    validate_font_input(None, max_size)?;
    // Serialize lookup and loading so concurrent Documents do not read the
    // same newly discovered locale font into independent allocations.
    let mut entries = SHARED_FONTS
        .lock()
        .map_err(|_| PdfError::new_err("bundled font registry lock was poisoned"))?;
    let before = identity(path)?;
    entries.retain(|entry| entry.data.strong_count() != 0);
    // Some virtual filesystems do not expose modification timestamps. Keep
    // their existing bounded-read behavior without reusing uncertain identities.
    if before.modified.is_none() {
        return Ok(Arc::new(read_font_input(path, max_size)?));
    }
    if let Some(data) = entries
        .iter()
        .find(|entry| entry.identity == before)
        .and_then(|entry| entry.data.upgrade())
    {
        // A previous unbounded or larger-budget load never bypasses this caller's policy.
        validate_font_input(Some(data.as_slice()), max_size)?;
        return Ok(data);
    }
    entries.retain(|entry| entry.identity.path != before.path);
    let data = Arc::new(read_font_input(path, max_size)?);
    let after = identity(path)?;
    // A file replaced or modified during reading must not leave a reusable entry.
    if before != after {
        return Ok(data);
    }
    if entries.len() == MAX_SHARED_FONTS {
        entries.remove(0);
    }
    entries.try_reserve(1).map_err(|error| {
        PdfError::new_err(format!(
            "failed to allocate bundled font registry entry: {error}"
        ))
    })?;
    entries.push(FontEntry {
        identity: after,
        data: Arc::downgrade(&data),
    });
    Ok(data)
}
