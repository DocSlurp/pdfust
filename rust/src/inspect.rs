//! Read-only structural inspection of a PDF object graph: font inventory,
//! JavaScript, optional content groups, attachments and per-page form widgets.
//!
//! Everything operates on a borrowed `lopdf::Document` and returns owned,
//! plain records, so Python and Node bindings can share it. Walks are bounded
//! (depth, node counts, cycle sets) because the input is untrusted.

use lopdf::{Dictionary, Document, Object, ObjectId};
use std::collections::{BTreeSet, HashSet};

const MAX_FONTS: usize = 4096;
const MAX_FORMS: usize = 4096;
const MAX_FORM_DEPTH: usize = 8;
const MAX_TREE_NODES: usize = 65_536;
const MAX_ATTACHMENTS: usize = 4096;
const MAX_OCGS: usize = 4096;
const MAX_ANNOTS_SCANNED: usize = 65_536;
const MAX_PARENT_DEPTH: usize = 64;
const MAX_NAME_BYTES: usize = 4096;
const MAX_JS_LOCATIONS: usize = 64;

/// Follow indirect references to a direct object, bounded against cycles.
fn resolve<'a>(doc: &'a Document, object: &'a Object) -> Option<&'a Object> {
    let mut current = object;
    for _ in 0..32 {
        match current {
            Object::Reference(id) => current = doc.get_object(*id).ok()?,
            other => return Some(other),
        }
    }
    None
}

fn resolve_dict<'a>(doc: &'a Document, object: &'a Object) -> Option<&'a Dictionary> {
    match resolve(doc, object)? {
        Object::Dictionary(dict) => Some(dict),
        Object::Stream(stream) => Some(&stream.dict),
        _ => None,
    }
}

fn get<'a>(doc: &'a Document, dict: &'a Dictionary, key: &[u8]) -> Option<&'a Object> {
    resolve(doc, dict.get(key).ok()?)
}

fn name_of(object: &Object) -> Option<String> {
    object.as_name().ok().map(|bytes| {
        String::from_utf8_lossy(&bytes[..bytes.len().min(MAX_NAME_BYTES)]).into_owned()
    })
}

/// Decode a PDF text string: UTF-16BE/LE with BOM, UTF-8 with BOM, else Latin-1.
pub(crate) fn pdf_text(bytes: &[u8]) -> String {
    let bytes = &bytes[..bytes.len().min(MAX_NAME_BYTES)];
    if let Some(rest) = bytes.strip_prefix(&[0xFE, 0xFF]) {
        let units: Vec<u16> = rest
            .chunks_exact(2)
            .map(|pair| u16::from_be_bytes([pair[0], pair[1]]))
            .collect();
        return String::from_utf16_lossy(&units);
    }
    if let Some(rest) = bytes.strip_prefix(&[0xFF, 0xFE]) {
        let units: Vec<u16> = rest
            .chunks_exact(2)
            .map(|pair| u16::from_le_bytes([pair[0], pair[1]]))
            .collect();
        return String::from_utf16_lossy(&units);
    }
    if let Some(rest) = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]) {
        return String::from_utf8_lossy(rest).into_owned();
    }
    bytes.iter().map(|&b| char::from(b)).collect()
}

fn text_of(object: &Object) -> Option<String> {
    object.as_str().ok().map(pdf_text)
}

// ---------------------------------------------------------------- fonts ----

/// One distinct font dictionary found in page (or form XObject) resources.
pub(crate) struct FontEntry {
    /// Indirect object id, when the font is an indirect object.
    pub(crate) object: Option<ObjectId>,
    /// `BaseFont` (or the font's `Name`), possibly with a subset tag.
    pub(crate) name: String,
    /// PDF font subtype: Type1, MMType1, TrueType, Type0, Type3.
    pub(crate) subtype: String,
    /// CIDFontType0 or CIDFontType2 for a composite font.
    pub(crate) descendant_subtype: Option<String>,
    /// Whether the font program is embedded. Type 3 glyphs live in the
    /// document, so Type 3 fonts count as embedded.
    pub(crate) embedded: bool,
    pub(crate) has_to_unicode: bool,
    pub(crate) is_type3: bool,
    /// True when `BaseFont` carries a six-letter subset tag (`ABCDEF+Name`).
    pub(crate) subset: bool,
    /// Encoding name, `custom` for a dictionary with `Differences`, or none.
    pub(crate) encoding: Option<String>,
    /// One-based pages whose resources reference this font.
    pub(crate) pages: BTreeSet<u32>,
}

fn is_subset_tag(name: &str) -> bool {
    let bytes = name.as_bytes();
    bytes.len() > 7 && bytes[6] == b'+' && bytes[..6].iter().all(u8::is_ascii_uppercase)
}

fn descriptor_embeds(doc: &Document, font: &Dictionary) -> bool {
    let Some(descriptor) = get(doc, font, b"FontDescriptor").and_then(|o| match o {
        Object::Dictionary(d) => Some(d),
        _ => None,
    }) else {
        return false;
    };
    [&b"FontFile"[..], b"FontFile2", b"FontFile3"]
        .iter()
        .any(|key| descriptor.get(key).is_ok())
}

fn describe_font(doc: &Document, id: Option<ObjectId>, font: &Dictionary) -> FontEntry {
    let subtype = font
        .get(b"Subtype")
        .ok()
        .and_then(name_of)
        .unwrap_or_default();
    let name = font
        .get(b"BaseFont")
        .ok()
        .and_then(name_of)
        .or_else(|| font.get(b"Name").ok().and_then(name_of))
        .unwrap_or_default();
    let is_type3 = subtype == "Type3";
    let mut descendant_subtype = None;
    let mut embedded = is_type3 || descriptor_embeds(doc, font);
    if subtype == "Type0"
        && let Some(descendant) = get(doc, font, b"DescendantFonts")
            .and_then(|o| o.as_array().ok())
            .and_then(|items| items.first())
            .and_then(|o| resolve_dict(doc, o))
    {
        descendant_subtype = descendant.get(b"Subtype").ok().and_then(name_of);
        embedded = descriptor_embeds(doc, descendant);
    }
    let encoding = match get(doc, font, b"Encoding") {
        Some(Object::Name(bytes)) => Some(String::from_utf8_lossy(bytes).into_owned()),
        Some(Object::Dictionary(_)) => Some("custom".to_owned()),
        Some(Object::Stream(_)) => Some("cmap".to_owned()),
        _ => None,
    };
    FontEntry {
        object: id,
        subset: is_subset_tag(&name),
        name,
        subtype,
        descendant_subtype,
        embedded,
        has_to_unicode: font.get(b"ToUnicode").is_ok(),
        is_type3,
        encoding,
        pages: BTreeSet::new(),
    }
}

struct FontWalk<'a> {
    doc: &'a Document,
    fonts: Vec<FontEntry>,
    by_object: std::collections::HashMap<ObjectId, usize>,
    forms_seen: HashSet<ObjectId>,
    forms_total: usize,
}

impl<'a> FontWalk<'a> {
    fn add_font(&mut self, page: u32, id: Option<ObjectId>, font: &Dictionary) {
        if let Some(id) = id
            && let Some(&index) = self.by_object.get(&id)
        {
            self.fonts[index].pages.insert(page);
            return;
        }
        if self.fonts.len() >= MAX_FONTS {
            return;
        }
        let mut entry = describe_font(self.doc, id, font);
        if id.is_none()
            && let Some(existing) = self.fonts.iter_mut().find(|f| {
                f.object.is_none()
                    && f.name == entry.name
                    && f.subtype == entry.subtype
                    && f.has_to_unicode == entry.has_to_unicode
            })
        {
            existing.pages.insert(page);
            return;
        }
        entry.pages.insert(page);
        if let Some(id) = id {
            self.by_object.insert(id, self.fonts.len());
        }
        self.fonts.push(entry);
    }

    fn walk_resources(&mut self, page: u32, resources: &'a Dictionary, depth: usize) {
        if let Some(fonts) = get(self.doc, resources, b"Font").and_then(|o| match o {
            Object::Dictionary(d) => Some(d),
            _ => None,
        }) {
            for (_, value) in fonts.iter() {
                let id = value.as_reference().ok();
                if let Some(dict) = resolve_dict(self.doc, value) {
                    self.add_font(page, id, dict);
                }
            }
        }
        if depth >= MAX_FORM_DEPTH {
            return;
        }
        let Some(xobjects) = get(self.doc, resources, b"XObject").and_then(|o| match o {
            Object::Dictionary(d) => Some(d),
            _ => None,
        }) else {
            return;
        };
        for (_, value) in xobjects.iter() {
            let id = value.as_reference().ok();
            let Some(Object::Stream(stream)) = resolve(self.doc, value) else {
                continue;
            };
            if stream
                .dict
                .get(b"Subtype")
                .ok()
                .and_then(name_of)
                .as_deref()
                != Some("Form")
            {
                continue;
            }
            if let Some(id) = id
                && !self.forms_seen.insert(id)
            {
                continue;
            }
            self.forms_total += 1;
            if self.forms_total > MAX_FORMS {
                return;
            }
            if let Some(nested) =
                get(self.doc, &stream.dict, b"Resources").and_then(|o| o.as_dict().ok())
            {
                self.walk_resources(page, nested, depth + 1);
            }
        }
    }
}

/// Resources dictionary of a page, resolving inheritance through `Parent`.
pub(crate) fn page_resources(doc: &Document, page_id: ObjectId) -> Option<&Dictionary> {
    let mut current = page_id;
    for _ in 0..MAX_PARENT_DEPTH {
        let node = doc.get_dictionary(current).ok()?;
        if let Some(resources) = get(doc, node, b"Resources").and_then(|o| o.as_dict().ok()) {
            return Some(resources);
        }
        current = node.get(b"Parent").ok()?.as_reference().ok()?;
    }
    None
}

/// Inventory distinct fonts referenced by the given `(page number, page id)`
/// pairs, including fonts reached through Form XObjects.
pub(crate) fn collect_fonts(doc: &Document, pages: &[(u32, ObjectId)]) -> Vec<FontEntry> {
    let mut walk = FontWalk {
        doc,
        fonts: Vec::new(),
        by_object: std::collections::HashMap::new(),
        forms_seen: HashSet::new(),
        forms_total: 0,
    };
    for &(number, page_id) in pages {
        // Form XObjects shared by several pages are walked once per page so
        // the page list stays complete.
        walk.forms_seen.clear();
        walk.forms_total = 0;
        if let Some(resources) = page_resources(doc, page_id) {
            walk.walk_resources(number, resources, 0);
        }
    }
    walk.fonts
}

// ----------------------------------------------------------- JavaScript ----

/// One place a JavaScript action was found.
pub(crate) struct JavaScriptLocation {
    /// `names`, `open-action`, `catalog-actions`, `page-actions`,
    /// `annotation` or `form-field`.
    pub(crate) scope: &'static str,
    /// One-based page, for page-scoped locations.
    pub(crate) page: Option<u32>,
    /// Trigger such as `E`, `Fo`, `K` or `A`, when known.
    pub(crate) event: Option<String>,
}

fn action_is_javascript(doc: &Document, action: &Object, depth: usize) -> bool {
    let Some(dict) = resolve_dict(doc, action) else {
        return false;
    };
    if get(doc, dict, b"S").and_then(name_of_ref).as_deref() == Some("JavaScript") {
        return true;
    }
    // Follow the /Next chain (dictionary or array of actions).
    if depth < 8
        && let Some(next) = get(doc, dict, b"Next")
    {
        return match next {
            Object::Array(items) => items
                .iter()
                .any(|a| action_is_javascript(doc, a, depth + 1)),
            other => action_is_javascript(doc, other, depth + 1),
        };
    }
    false
}

fn name_of_ref(object: &Object) -> Option<String> {
    name_of(object)
}

/// Triggers in an additional-actions dictionary whose action is JavaScript.
fn javascript_triggers(doc: &Document, holder: &Dictionary) -> Vec<String> {
    let mut out = Vec::new();
    if let Some(aa) = get(doc, holder, b"AA").and_then(|o| o.as_dict().ok()) {
        for (key, value) in aa.iter() {
            if action_is_javascript(doc, value, 0) {
                out.push(String::from_utf8_lossy(key).into_owned());
            }
        }
    }
    out
}

fn name_tree_has_entries(doc: &Document, root: &Object) -> bool {
    let mut stack = vec![root];
    let mut visited: HashSet<ObjectId> = HashSet::new();
    let mut nodes = 0usize;
    while let Some(object) = stack.pop() {
        if let Object::Reference(id) = object
            && !visited.insert(*id)
        {
            continue;
        }
        nodes += 1;
        if nodes > MAX_TREE_NODES {
            return false;
        }
        let Some(node) = resolve_dict(doc, object) else {
            continue;
        };
        if get(doc, node, b"Names")
            .and_then(|o| o.as_array().ok())
            .is_some_and(|names| !names.is_empty())
        {
            return true;
        }
        if let Some(kids) = get(doc, node, b"Kids").and_then(|o| o.as_array().ok()) {
            stack.extend(kids.iter());
        }
    }
    false
}

/// Find JavaScript in the catalog, page and annotation actions and form
/// fields. Page-level scanning visits each page's annotation array once.
pub(crate) fn collect_javascript(
    doc: &Document,
    pages: &[(u32, ObjectId)],
) -> Vec<JavaScriptLocation> {
    let mut out = Vec::new();
    let push = |out: &mut Vec<JavaScriptLocation>, location: JavaScriptLocation| {
        if out.len() < MAX_JS_LOCATIONS {
            out.push(location);
        }
    };
    if let Ok(catalog) = doc.catalog() {
        if get(doc, catalog, b"Names")
            .and_then(|o| o.as_dict().ok())
            .and_then(|names| names.get(b"JavaScript").ok())
            .is_some_and(|root| name_tree_has_entries(doc, root))
        {
            push(
                &mut out,
                JavaScriptLocation {
                    scope: "names",
                    page: None,
                    event: None,
                },
            );
        }
        if let Some(action) = catalog.get(b"OpenAction").ok()
            && action_is_javascript(doc, action, 0)
        {
            push(
                &mut out,
                JavaScriptLocation {
                    scope: "open-action",
                    page: None,
                    event: None,
                },
            );
        }
        for event in javascript_triggers(doc, catalog) {
            push(
                &mut out,
                JavaScriptLocation {
                    scope: "catalog-actions",
                    page: None,
                    event: Some(event),
                },
            );
        }
    }
    let mut scanned = 0usize;
    for &(number, page_id) in pages {
        let Ok(page) = doc.get_dictionary(page_id) else {
            continue;
        };
        for event in javascript_triggers(doc, page) {
            push(
                &mut out,
                JavaScriptLocation {
                    scope: "page-actions",
                    page: Some(number),
                    event: Some(event),
                },
            );
        }
        let Some(annots) = get(doc, page, b"Annots").and_then(|o| o.as_array().ok()) else {
            continue;
        };
        for annot in annots {
            scanned += 1;
            if scanned > MAX_ANNOTS_SCANNED {
                return out;
            }
            let Some(dict) = resolve_dict(doc, annot) else {
                continue;
            };
            let widget = dict.get(b"Subtype").ok().and_then(name_of).as_deref() == Some("Widget");
            let scope = if widget { "form-field" } else { "annotation" };
            if let Some(action) = dict.get(b"A").ok()
                && action_is_javascript(doc, action, 0)
            {
                push(
                    &mut out,
                    JavaScriptLocation {
                        scope,
                        page: Some(number),
                        event: Some("A".to_owned()),
                    },
                );
            }
            for event in javascript_triggers(doc, dict) {
                push(
                    &mut out,
                    JavaScriptLocation {
                        scope,
                        page: Some(number),
                        event: Some(event),
                    },
                );
            }
        }
    }
    out
}

// ------------------------------------------------------- optional content ----

/// One optional content group (layer) and its default visibility.
pub(crate) struct OptionalContentGroup {
    pub(crate) object: ObjectId,
    pub(crate) name: String,
    /// Visibility in the default configuration (`BaseState`, `ON`, `OFF`).
    pub(crate) visible: bool,
    /// Intent names, normally `View` and/or `Design`.
    pub(crate) intent: Vec<String>,
}

pub(crate) fn collect_optional_content(doc: &Document) -> Vec<OptionalContentGroup> {
    let Ok(catalog) = doc.catalog() else {
        return Vec::new();
    };
    let Some(props) = get(doc, catalog, b"OCProperties").and_then(|o| o.as_dict().ok()) else {
        return Vec::new();
    };
    let Some(groups) = get(doc, props, b"OCGs").and_then(|o| o.as_array().ok()) else {
        return Vec::new();
    };
    let config = get(doc, props, b"D").and_then(|o| o.as_dict().ok());
    let ids = |key: &[u8]| -> HashSet<ObjectId> {
        config
            .and_then(|c| get(doc, c, key))
            .and_then(|o| o.as_array().ok())
            .map(|items| items.iter().filter_map(|o| o.as_reference().ok()).collect())
            .unwrap_or_default()
    };
    let on = ids(b"ON");
    let off = ids(b"OFF");
    let base_off = config
        .and_then(|c| get(doc, c, b"BaseState"))
        .and_then(name_of_ref)
        .as_deref()
        == Some("OFF");
    let mut out = Vec::new();
    for group in groups.iter().take(MAX_OCGS) {
        let Ok(id) = group.as_reference() else {
            continue;
        };
        let Some(dict) = doc.get_dictionary(id).ok() else {
            continue;
        };
        let name = get(doc, dict, b"Name")
            .and_then(text_of)
            .unwrap_or_default();
        let visible = if base_off {
            on.contains(&id) && !off.contains(&id)
        } else {
            !off.contains(&id)
        };
        let intent = match get(doc, dict, b"Intent") {
            Some(Object::Name(bytes)) => vec![String::from_utf8_lossy(bytes).into_owned()],
            Some(Object::Array(items)) => items
                .iter()
                .filter_map(|o| resolve(doc, o).and_then(name_of_ref))
                .collect(),
            _ => Vec::new(),
        };
        out.push(OptionalContentGroup {
            object: id,
            name,
            visible,
            intent,
        });
    }
    out
}

// ----------------------------------------------------------- attachments ----

pub(crate) struct AttachmentInfo {
    pub(crate) name: String,
    /// Stored (compressed) size in bytes of the embedded file stream.
    pub(crate) stored_size: usize,
    /// Declared uncompressed size from `Params/Size`, when present.
    pub(crate) size: Option<u64>,
    /// MIME type from the embedded stream's `Subtype`, when present.
    pub(crate) mime: Option<String>,
    pub(crate) description: Option<String>,
}

fn attachment_from_filespec(doc: &Document, name: String, spec: &Object) -> AttachmentInfo {
    let mut info = AttachmentInfo {
        name,
        stored_size: 0,
        size: None,
        mime: None,
        description: None,
    };
    let Some(dict) = resolve_dict(doc, spec) else {
        return info;
    };
    info.description = get(doc, dict, b"Desc").and_then(text_of);
    let ef = get(doc, dict, b"EF").and_then(|o| o.as_dict().ok());
    let stream = ef.and_then(|ef| {
        [&b"UF"[..], b"F", b"DOS", b"Mac", b"Unix"]
            .iter()
            .find_map(|key| get(doc, ef, key))
    });
    if let Some(Object::Stream(stream)) = stream {
        info.stored_size = stream.content.len();
        info.mime = stream
            .dict
            .get(b"Subtype")
            .ok()
            .and_then(name_of)
            .map(|raw| raw.replace("#2F", "/"));
        info.size = get(doc, &stream.dict, b"Params")
            .and_then(|o| o.as_dict().ok())
            .and_then(|params| params.get(b"Size").ok())
            .and_then(|o| o.as_i64().ok())
            .and_then(|n| u64::try_from(n).ok());
    }
    info
}

/// List files in the `EmbeddedFiles` name tree, ordered by name.
pub(crate) fn collect_attachments(doc: &Document) -> Vec<AttachmentInfo> {
    let mut out = Vec::new();
    let Some(root) = doc
        .catalog()
        .ok()
        .and_then(|catalog| get(doc, catalog, b"Names"))
        .and_then(|names| names.as_dict().ok())
        .and_then(|names| names.get(b"EmbeddedFiles").ok())
    else {
        return out;
    };
    let mut stack = vec![root];
    let mut visited: HashSet<ObjectId> = HashSet::new();
    let mut nodes = 0usize;
    while let Some(object) = stack.pop() {
        if let Object::Reference(id) = object
            && !visited.insert(*id)
        {
            continue;
        }
        nodes += 1;
        if nodes > MAX_TREE_NODES {
            break;
        }
        let Some(node) = resolve_dict(doc, object) else {
            continue;
        };
        if let Some(pairs) = get(doc, node, b"Names").and_then(|o| o.as_array().ok()) {
            for pair in pairs.chunks_exact(2) {
                if out.len() >= MAX_ATTACHMENTS {
                    break;
                }
                let name = resolve(doc, &pair[0]).and_then(text_of).unwrap_or_default();
                out.push(attachment_from_filespec(doc, name, &pair[1]));
            }
        }
        if let Some(kids) = get(doc, node, b"Kids").and_then(|o| o.as_array().ok()) {
            stack.extend(kids.iter());
        }
    }
    out.sort_by(|a, b| a.name.cmp(&b.name));
    out
}

// --------------------------------------------------------------- widgets ----

/// One form-field widget placed on a page.
pub(crate) struct WidgetInfo {
    /// `text`, `checkbox`, `radio`, `button`, `combobox`, `listbox`,
    /// `signature` or `unknown`.
    pub(crate) kind: &'static str,
    /// Fully qualified field name (`parent.child`).
    pub(crate) name: String,
    /// Field value rendered as text; none when the field has no value.
    pub(crate) value: Option<String>,
    /// Whether the field has a non-empty value (for checkboxes and radios,
    /// anything other than `Off`).
    pub(crate) filled: bool,
    pub(crate) read_only: bool,
    pub(crate) required: bool,
    /// Widget rectangle in the caller's display space.
    pub(crate) bbox: [f64; 4],
}

fn inherited<'a>(doc: &'a Document, widget: &'a Dictionary, key: &[u8]) -> Option<&'a Object> {
    let mut current = widget;
    for _ in 0..MAX_PARENT_DEPTH {
        if let Some(value) = get(doc, current, key) {
            return Some(value);
        }
        current = get(doc, current, b"Parent").and_then(|o| o.as_dict().ok())?;
    }
    None
}

fn qualified_name(doc: &Document, widget: &Dictionary) -> String {
    let mut parts = Vec::new();
    let mut current = Some(widget);
    for _ in 0..MAX_PARENT_DEPTH {
        let Some(dict) = current else { break };
        if let Some(part) = get(doc, dict, b"T").and_then(text_of) {
            parts.push(part);
        }
        current = get(doc, dict, b"Parent").and_then(|o| o.as_dict().ok());
    }
    parts.reverse();
    parts.join(".")
}

fn value_text(doc: &Document, value: &Object) -> Option<String> {
    match value {
        Object::String(bytes, _) => Some(pdf_text(bytes)),
        Object::Name(bytes) => Some(String::from_utf8_lossy(bytes).into_owned()),
        Object::Array(items) => {
            let parts: Vec<String> = items
                .iter()
                .filter_map(|o| resolve(doc, o).and_then(|o| value_text(doc, o)))
                .collect();
            Some(parts.join(", "))
        }
        Object::Stream(stream) => {
            let bytes = stream
                .decompressed_content()
                .unwrap_or_else(|_| stream.content.clone());
            Some(pdf_text(&bytes[..bytes.len().min(MAX_NAME_BYTES)]))
        }
        _ => None,
    }
}

/// Widgets in a page's `Annots`. `to_display` maps a PDF-space rectangle
/// `[x0, y0, x1, y1]` to the caller's display space.
pub(crate) fn collect_widgets(
    doc: &Document,
    page_id: ObjectId,
    to_display: &dyn Fn([f64; 4]) -> [f64; 4],
) -> Vec<WidgetInfo> {
    let mut out = Vec::new();
    let Ok(page) = doc.get_dictionary(page_id) else {
        return out;
    };
    let Some(annots) = get(doc, page, b"Annots").and_then(|o| o.as_array().ok()) else {
        return out;
    };
    for annot in annots.iter().take(MAX_ANNOTS_SCANNED) {
        let Some(dict) = resolve_dict(doc, annot) else {
            continue;
        };
        if dict.get(b"Subtype").ok().and_then(name_of).as_deref() != Some("Widget") {
            continue;
        }
        let rect = get(doc, dict, b"Rect")
            .and_then(|o| o.as_array().ok())
            .map(|items| {
                items
                    .iter()
                    .filter_map(|o| resolve(doc, o))
                    .filter_map(|o| {
                        o.as_float()
                            .map(f64::from)
                            .ok()
                            .or_else(|| o.as_i64().ok().map(|n| n as f64))
                    })
                    .collect::<Vec<f64>>()
            })
            .filter(|values| values.len() == 4);
        let Some(rect) = rect else { continue };
        let flags = inherited(doc, dict, b"Ff")
            .and_then(|o| o.as_i64().ok())
            .unwrap_or(0);
        let field_type = inherited(doc, dict, b"FT").and_then(name_of_ref);
        let kind = match field_type.as_deref() {
            Some("Tx") => "text",
            Some("Btn") if flags & (1 << 16) != 0 => "button",
            Some("Btn") if flags & (1 << 15) != 0 => "radio",
            Some("Btn") => "checkbox",
            Some("Ch") if flags & (1 << 17) != 0 => "combobox",
            Some("Ch") => "listbox",
            Some("Sig") => "signature",
            _ => "unknown",
        };
        let value = inherited(doc, dict, b"V").and_then(|v| value_text(doc, v));
        let filled = match (kind, value.as_deref()) {
            ("signature", _) => inherited(doc, dict, b"V").is_some(),
            ("checkbox" | "radio", Some(v)) => v != "Off" && !v.is_empty(),
            (_, Some(v)) => !v.trim().is_empty(),
            _ => false,
        };
        out.push(WidgetInfo {
            kind,
            name: qualified_name(doc, dict),
            value,
            filled,
            read_only: flags & 1 != 0,
            required: flags & (1 << 1) != 0,
            bbox: to_display([rect[0], rect[1], rect[2], rect[3]]),
        });
    }
    out
}
