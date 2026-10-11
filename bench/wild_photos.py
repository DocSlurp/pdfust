"""Acquire public-domain and CC0 photographs for the wild-v1 DEV corpus.

The library is written to ``photos/`` beneath the wild-v1 artifact directory:
one normalized JPEG per photo plus ``photos.json`` with license and provenance
records (schema in ``bench/WILD_CORPUS.md``). Candidates come from fixed
Wikimedia Commons searches; the first license-valid result per subject, in API
order, is selected. Only Public domain and CC0 files are accepted.

Downloads are untrusted data. They are written only into the photos directory,
validated and re-encoded with Pillow (RGB JPEG, quality 85, long edge at most
1600 px, no EXIF), and deleted on any failure. Nothing from that directory is
executed or imported.

Usage::

    .venv/bin/python -m bench.wild_photos --directory bench/results/pdf-master-artifacts/wild-v1
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import platform
import re
import resource
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image, ImageOps

from bench.silver import guard_path

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "jev-pdf-wild-corpus/1.0 (research DEV corpus)"
MAX_REQUESTS = 200
MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024
MAX_API_BYTES = 4 * 1024 * 1024
LONG_EDGE = 1600
MIN_SOURCE_LONG_EDGE = 1000
JPEG_QUALITY = 85
MAX_ASPECT_RATIO = 2.5
HTTP_TOO_MANY_REQUESTS = 429
REQUEST_DELAY_SECONDS = 2.0
MAX_RETRIES = 2
MAX_RETRY_AFTER_SECONDS = 60.0
DOWNLOAD_HOSTS = ("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/")
SEARCH_LIMIT = 20
# Commons structured data: copyright license CC0, or copyright status public domain.
LICENSE_STATEMENT_FILTER = "haswbstatement:P275=Q6938433|P6216=Q19652"
EXTMETADATA_FIELDS = "LicenseShortName|License|LicenseUrl|Artist|Restrictions|UsageTerms|Copyrighted"
CC0_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
PD_URL = "https://commons.wikimedia.org/wiki/Commons:Public_domain"
# Conservative title screen: these subjects usually put identifiable people first.
PEOPLE_TITLE_WORDS = frozenset(
    {
        "boy",
        "boys",
        "child",
        "children",
        "crowd",
        "girl",
        "girls",
        "man",
        "men",
        "people",
        "portrait",
        "scientist",
        "selfie",
        "student",
        "students",
        "team",
        "technician",
        "woman",
        "women",
        "worker",
        "workers",
    }
)

# Titles rejected after visual review of earlier deterministic selections, with reasons.
# Keeping them here makes the re-run select the next license-valid candidate in API order.
REVIEW_EXCLUSIONS: dict[str, str] = {
    "File:Thomas Edison with microscope in the Chemistry Laboratory. (19cf746ec847495392f3213b3a6f6370).jpg": (
        "identifiable person is the main subject"
    ),
    "File:Paul Hermann, German, baking loaves of Lithuanian rye 8d19630v.jpg": (
        "identifiable person is the main subject"
    ),
    "File:Blue Nets at Dusk (Greville Irwin).jpg": "painting reproduction, not a photograph",
    "File:Catering Osttribüne Ostseestadion Rostock 2024-08-03.jpg": (
        "crowd with recognizable faces is the main subject"
    ),
    "File:StateLibQld 1 51548 Machinists seated at industrial sewing machines at a Brisbane factory, ca. 1943.jpg": (
        "recognizable workers are the main subject"
    ),
    "File:Ticket for a privately operated public transport bus service in Kolkata.jpg": (
        "hand-held ticket; does not match the bus slot"
    ),
    "File:Outstanding Achievement- Janice Shepherd, Grand Junction Field Office, CO (34822596845).jpg": (
        "portrait of an identifiable person"
    ),
    "File:Hail Scars Alberta Farmland (154724 - tmo 20250824 lrg).jpg": (
        "satellite image; does not match the farm-field slot"
    ),
    "File:Van Gogh - Weizenfeld.jpeg": "painting reproduction, not a photograph",
    "File:Van Gogh - Saatfeld bei Sonnenaufgang.jpeg": "painting reproduction, not a photograph",
    "File:Machine Tool Collection Gilbert 1966 Plate 06.jpg": "book-plate scan with recognizable workers",
    "File:Secretary Kerry Straightens Papers at Hotel in Austria After Signing Documents to Lift Sanctions "
    "Following Implementation of Plan Controlling Iran's Nuclear Program (24398319546).jpg": (
        "identifiable public figure is the main subject"
    ),
    "File:Army Post Office 3, Boulogne, 1919 Art.IWMART2881.jpg": "painting reproduction, not a photograph",
    "File:Marie Stopes in her laboratory, 1904 - Restoration.jpg": "identifiable person is the main subject",
    "File:City Hall and County Building, Chicago (60782).jpg": "printed postcard illustration, not a photograph",
    "File:Manhattan 1931.jpg": "aerial view, does not match the city-street slot",
    "File:Covered board sidewalk in Tombstone, Arizona - May 1940 (cropped).jpg": "does not match the farm-field slot",
    "File:United Shoe Machinery Corporation factory - postcard.jpg": "printed postcard illustration, not a photograph",
    "File:Times Square Subway Mezzanine.jpg": "crowd with recognizable faces; does not match the bus slot",
    "File:AERIAL VIEW OF FARMLAND CONTOURS - NARA - 547349.jpg": "abstract dark scan; farmland not recognizable",
}
# Accepted selections after visual review, pinned so re-runs are reproducible even when
# Commons search ranking drifts. Pinned files are re-fetched by title in one batched
# imageinfo request and still pass the full license and title screen; a pin that fails
# falls back to the slot's search query.
PINNED_TITLES: dict[str, str] = {
    "farm-field": "File:Barley field, Ehrenbach, detail.jpg",
    "factory-machinery": "File:Machine workshop, railway workshops, Petone ATLIB 178942.png",
    "paper-documents": "File:European style folders dossiers.jpg",
    "harbor": "File:130916-G-SF967-001 (9817861766).jpg",
    "catering-buffet": "File:Buffet Food at the Fiesta Casino in Henderson, NV.jpg",
    "salad-bowl": "File:Salad bowl, Kiedrich.jpg",
    "bread-bakery": "File:Loaves of Bread (Unsplash).jpg",
    "coffee-cup": "File:Coffee Cup on Modern Table.jpg",
    "office-interior": "File:Office Inside the Federal Reserve Bank - DPLA - 0f6b611a7154a1a77f8d622f72f82eb2.jpg",
    "classroom": "File:Marines volunteer time at Filipino school (5093235541).jpg",
    "library-shelves": "File:Bookshelves in Hove Library 2025-08-20.jpg",
    "lab-pipettes": "File:Pipettes or Droppers; from a medical laboratory in Abuja, Nigeria.jpg",
    "microscope": "File:Laboratory, microscope Fortepan 3364.jpg",
    "lab-glassware": "File:Birnenkolben.jpg",
    "city-hall": "File:Exterior of City Hall, New York City LCCN95503557.jpg",
    "office-building": (
        "File:Construction of a new office-building near Beatrixkwartier in The Hague city; "
        "high resolution image by FotoDutch, June 2013.jpg"
    ),
    "school-building": "File:High school building exterior is pictured in a town or city landscape.jpg",
    "city-street": (
        "File:GD 廣東 Guangdong 中山 Zhongshan 東區 Dong District 康樂街 "
        "Kangle Street sidewalk shops February 2025 R12S 02.jpg"
    ),
    "park-path": "File:Tree-lined path in Asaf Ali Park, GK 1.jpg",
    "mountain-lake": "File:Lake Mountain Landscape.jpg",
    "garden-flowers": "File:Flower garden Hopewell Furnace.jpg",
    "potted-plants": "File:Ludisia discolor - Talcott Greenhouse - Mount Holyoke College - DSC04513.JPG",
    "hand-tools": "File:Jeweler's Workbench.jpg",
    "tractor": "File:Tractor cultivating a field in Brittany.jpg",
    "city-bus": "File:Mercedes Benz Conecto G na liniji 602.jpg",
    "train-station": "File:Dattapukur railway station platform 2 looking east.jpg",
    "container-port": "File:Aerial photograph of the Port of Miami Container Port.jpg",
    "aerial-city": "File:Aerial view of Medway City Estate (2).jpg",
    "aerial-farmland": (
        "File:AERIAL PHOTOGRAPH OF FARMLAND WITHIN A 15-MILE RADIUS OF NEW ULM, MINNESOTA, "
        "A COUNTY SEAT TRADING CENTER OF 13,000... - NARA - 558414.jpg"
    ),
    "laptop-desk": "File:Laptop on desk book stacks (Unsplash).jpg",
    "solar-panels": "File:Solar panels in Paysandú Department.jpg",
    "whiteboard": "File:67 Whiteboard 2025-11-09.jpg",
}
# Words in titles that usually mark reproductions of artworks or printed postcards.
NON_PHOTO_TITLE_WORDS = frozenset(
    {"clipart", "drawing", "illustration", "mascot", "painting", "plate", "postcard", "poster", "vector"}
)
# Evidence-release scans (EFTA numbering) are unsuitable provenance for business documents.
EXCLUDED_TITLE_PATTERN = re.compile(r"^File:EFTA\d")


@dataclass(frozen=True)
class Subject:
    """One fixed search slot; ``slug`` becomes part of the stable photo id."""

    slug: str
    query: str
    subject: str
    tags: tuple[str, ...]


SUBJECTS: tuple[Subject, ...] = (
    Subject("harbor", "harbor boats dusk", "harbor with boats", ("harbor", "transport", "outdoor", "landscape")),
    Subject("catering-buffet", "buffet food platters", "catering buffet dishes", ("food", "catering", "indoor")),
    Subject("salad-bowl", "salad bowl vegetables", "salad bowl", ("food", "catering", "product")),
    Subject("bread-bakery", "bread loaves bakery", "bread loaves", ("food", "product")),
    Subject("coffee-cup", "coffee cup table", "coffee cup on a table", ("food", "product", "office")),
    Subject("office-interior", "office interior desks chairs", "office interior", ("office", "interior", "business")),
    Subject("classroom", "empty classroom desks", "empty classroom", ("school", "interior", "education")),
    Subject("library-shelves", "library bookshelves interior", "library shelves", ("school", "interior", "civic")),
    Subject("lab-pipettes", "laboratory pipettes", "laboratory pipettes", ("science", "lab", "equipment")),
    Subject("microscope", "microscope laboratory", "microscope", ("science", "lab", "equipment")),
    Subject("lab-glassware", "laboratory glassware flasks", "laboratory glassware", ("science", "lab", "equipment")),
    Subject("city-hall", "city hall building exterior", "city hall exterior", ("civic", "building", "outdoor")),
    Subject(
        "office-building",
        "modern office building facade",
        "office building facade",
        ("business", "building", "outdoor"),
    ),
    Subject("school-building", "school building exterior", "school building", ("school", "building", "outdoor")),
    Subject("city-street", "street sidewalk shops", "city street", ("civic", "street", "outdoor")),
    Subject("park-path", "park path trees", "park path with trees", ("park", "landscape", "outdoor")),
    Subject("mountain-lake", "mountain lake landscape", "mountain lake", ("landscape", "outdoor", "nature")),
    Subject("farm-field", "barley field", "farm field", ("landscape", "agriculture", "outdoor")),
    Subject("garden-flowers", "flower garden", "flower garden", ("garden", "plants", "outdoor")),
    Subject(
        "potted-plants", "potted plants greenhouse", "potted plants in a greenhouse", ("garden", "plants", "indoor")
    ),
    Subject("hand-tools", "hand tools workbench", "hand tools on a workbench", ("tools", "workshop", "industry")),
    Subject("factory-machinery", "lathe machine workshop", "factory machinery", ("machinery", "industry", "indoor")),
    Subject("tractor", "tractor field", "tractor", ("vehicle", "machinery", "agriculture")),
    Subject("city-bus", "articulated bus", "city bus", ("vehicle", "transport", "civic")),
    Subject("train-station", "railway station platform train", "train at a station", ("vehicle", "transport", "civic")),
    Subject("container-port", "container ship port cranes", "container port", ("harbor", "transport", "industry")),
    Subject("aerial-city", "aerial view city", "aerial view of a city", ("aerial", "civic", "outdoor")),
    Subject(
        "aerial-farmland",
        "aerial photograph farmland fields",
        "aerial view of farmland",
        ("aerial", "landscape", "agriculture"),
    ),
    Subject("laptop-desk", "laptop computer desk", "laptop on a desk", ("office", "product", "technology")),
    Subject("solar-panels", "solar panels", "solar panels", ("energy", "science", "outdoor")),
    Subject("whiteboard", "whiteboard writing", "whiteboard with writing", ("document", "school", "office")),
    Subject("paper-documents", "file folders", "papers on a desk", ("document", "office", "business")),
)


class PhotoError(Exception):
    """A candidate failed download or validation."""


class RequestBudget:
    """Sequential, delayed HTTP access with a hard request ceiling."""

    def __init__(self, limit: int = MAX_REQUESTS, delay: float = REQUEST_DELAY_SECONDS) -> None:
        """Allow at most ``limit`` requests spaced by ``delay`` seconds."""
        self.limit = limit
        self.delay = delay
        self.used = 0
        self.retries = 0
        self._last = 0.0

    def fetch(self, url: str, max_bytes: int) -> tuple[bytes, str]:
        """Return ``(body, content_type)``, refusing bodies above ``max_bytes``."""
        if not url.startswith((API_URL, *DOWNLOAD_HOSTS)):
            message = f"refusing unexpected URL {url}"
            raise PhotoError(message)
        attempt = 0
        while True:
            try:
                data, content_type = self._once(url, max_bytes)
                break
            except urllib.error.HTTPError as error:
                if error.code != HTTP_TOO_MANY_REQUESTS or attempt >= MAX_RETRIES:
                    raise
                attempt += 1
                self.retries += 1
                time.sleep(_retry_after(error.headers.get("Retry-After")))
        if len(data) > max_bytes:
            message = f"response exceeds {max_bytes} bytes"
            raise PhotoError(message)
        return data, content_type

    def _once(self, url: str, max_bytes: int) -> tuple[bytes, str]:
        if self.used >= self.limit:
            message = f"request budget of {self.limit} exhausted"
            raise PhotoError(message)
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self.used += 1
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 - https allowlist
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - https allowlist
                return response.read(max_bytes + 1), response.headers.get("Content-Type", "")
        finally:
            self._last = time.monotonic()


def _retry_after(value: str | None) -> float:
    """Return a bounded Retry-After delay in seconds (default 10)."""
    try:
        seconds = float(value) if value else 10.0
    except ValueError:
        seconds = 10.0
    return min(max(seconds, 1.0), MAX_RETRY_AFTER_SECONDS)


def _api_url(params: dict[str, str]) -> str:
    base = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime",
        "iiurlwidth": str(LONG_EDGE),
        "iiextmetadatafilter": EXTMETADATA_FIELDS,
    }
    return f"{API_URL}?{urllib.parse.urlencode({**base, **params})}"


def search_url(query: str) -> str:
    """Return the Commons search URL for one fixed subject query."""
    return _api_url(
        {
            "generator": "search",
            "gsrnamespace": "6",
            "gsrlimit": str(SEARCH_LIMIT),
            "gsrsearch": f"{query} filetype:bitmap {LICENSE_STATEMENT_FILTER}",
        }
    )


def titles_url(titles: list[str]) -> str:
    """Return one batched imageinfo URL for at most 50 pinned file titles."""
    return _api_url({"titles": "|".join(titles[:50])})


def _meta(extmetadata: dict[str, Any], key: str) -> str:
    entry = extmetadata.get(key)
    if isinstance(entry, dict):
        value = entry.get("value", "")
        return value if isinstance(value, str) else str(value)
    return ""


def strip_html(value: str) -> str:
    """Return plain text from a Commons HTML metadata fragment."""
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def classify_license(extmetadata: dict[str, Any]) -> tuple[str, str] | None:
    """Return ``(license, license_url)`` for Public domain or CC0, else ``None``."""
    short = strip_html(_meta(extmetadata, "LicenseShortName")).lower()
    code = _meta(extmetadata, "License").strip().lower()
    url = _meta(extmetadata, "LicenseUrl").strip()
    if short in {"cc0", "cc0 1.0", "cc-zero"} or code in {"cc0", "cc0-1.0", "cc-zero"}:
        return "CC0 1.0", url or CC0_URL
    if short in {"public domain", "pd"} or short.startswith("public domain ") or code == "pd":
        return "Public domain", url or PD_URL
    return None


def _title_reason(title: str) -> str:
    """Return a rejection reason from the file title, or an empty string."""
    if title in REVIEW_EXCLUSIONS:
        return f"manual review: {REVIEW_EXCLUSIONS[title]}"
    if EXCLUDED_TITLE_PATTERN.match(title):
        return "excluded provenance (evidence-release scan)"
    words = set(re.findall(r"[a-z]+", title.lower()))
    if words & PEOPLE_TITLE_WORDS:
        return "title suggests people as the main subject"
    if words & NON_PHOTO_TITLE_WORDS:
        return "title suggests an artwork or postcard, not a photograph"
    return ""


def candidate_reason(page: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:  # noqa: PLR0911 - one reason per screen
    """Screen one search result; return parsed metadata or a rejection reason."""
    title = str(page.get("title", ""))
    infos = page.get("imageinfo")
    if not isinstance(infos, list) or not infos or not isinstance(infos[0], dict):
        return None, "missing imageinfo"
    info = infos[0]
    raw_metadata = info.get("extmetadata")
    extmetadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    license_info = classify_license(extmetadata)
    if license_info is None:
        short = strip_html(_meta(extmetadata, "LicenseShortName")) or "unknown"
        return None, f"license not PD/CC0: {short}"
    restrictions = _meta(extmetadata, "Restrictions").lower()
    if "personality" in restrictions:
        return None, "personality rights restriction"
    title_reason = _title_reason(title)
    if title_reason:
        return None, title_reason
    if info.get("mime") not in {"image/jpeg", "image/png"}:
        return None, f"unsupported mime {info.get('mime')}"
    width, height = int(info.get("width") or 0), int(info.get("height") or 0)
    if max(width, height) < MIN_SOURCE_LONG_EDGE:
        return None, f"source too small ({width}x{height})"
    if min(width, height) == 0 or max(width, height) / min(width, height) > MAX_ASPECT_RATIO:
        return None, f"extreme aspect ratio ({width}x{height})"
    thumb = str(info.get("thumburl") or info.get("url") or "")
    if not thumb.startswith(DOWNLOAD_HOSTS):
        return None, "unexpected download host"
    source_url = str(info.get("descriptionurl") or "")
    if not source_url.startswith("https://commons.wikimedia.org/"):
        return None, "unexpected source page host"
    author = strip_html(_meta(extmetadata, "Artist")) or "unknown"
    license_name, license_url = license_info
    return {
        "title": title,
        "download_url": thumb,
        "source_url": source_url,
        "author": author,
        "license": license_name,
        "license_url": license_url,
    }, ""


def ordered_pages(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Return search result pages in API ranking order."""
    query = response.get("query")
    pages = query.get("pages", []) if isinstance(query, dict) else []
    if isinstance(pages, dict):
        pages = list(pages.values())
    valid = [page for page in pages if isinstance(page, dict)]
    return sorted(valid, key=lambda page: (int(page.get("index", 1 << 30)), str(page.get("title", ""))))


def normalize_image(data: bytes, destination: Path) -> tuple[int, int]:
    """Validate untrusted image bytes and write a clean RGB JPEG without EXIF."""
    Image.MAX_IMAGE_PIXELS = 80_000_000
    try:
        with Image.open(io.BytesIO(data)) as probe:
            image_format = probe.format
            probe.verify()
        with Image.open(io.BytesIO(data)) as source:
            source.load()
            image = ImageOps.exif_transpose(source).convert("RGB")
    except Exception as error:  # Pillow raises many types for malformed input.
        message = f"image validation failed: {error}"
        raise PhotoError(message) from error
    if image_format not in {"JPEG", "PNG"}:
        message = f"unexpected image format {image_format}"
        raise PhotoError(message)
    image.thumbnail((LONG_EDGE, LONG_EDGE), Image.Resampling.LANCZOS)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        image.save(temporary, "JPEG", quality=JPEG_QUALITY, optimize=True)
        with Image.open(temporary) as check:
            check.verify()
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return image.size


def download_photo(fetcher: Callable[[str, int], tuple[bytes, str]], url: str, destination: Path) -> tuple[int, int]:
    """Download one untrusted image and write its normalized JPEG."""
    data, content_type = fetcher(url, MAX_DOWNLOAD_BYTES)
    if not content_type.startswith("image/"):
        message = f"unexpected content type {content_type}"
        raise PhotoError(message)
    return normalize_image(data, destination)


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 of one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def library_is_valid(photos_dir: Path, manifest: Path) -> bool:
    """Report whether every manifest record exists with its recorded hash."""
    try:
        records = json.loads(manifest.read_text(encoding="utf-8"))["photos"]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    if not records:
        return False
    for record in records:
        path = photos_dir / f"{record['id']}.jpg"
        if not path.is_file() or sha256_file(path) != record.get("sha256"):
            return False
    return True


def _rss_mib(scope: int) -> float:
    peak = resource.getrusage(scope).ru_maxrss
    # Linux reports KiB, macOS bytes.
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


@dataclass
class _Run:
    """Shared state of one acquisition run."""

    fetcher: Callable[[str, int], tuple[bytes, str]]
    photos_dir: Path
    retrieved_at: str
    log: Callable[[str], None]
    seen: set[str] = field(default_factory=set)
    rejected: list[dict[str, str]] = field(default_factory=list)

    def _pages(self, url: str) -> list[dict[str, Any]]:
        raw, _ = self.fetcher(url, MAX_API_BYTES)
        return ordered_pages(json.loads(raw))

    def pinned_pages(self, titles: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch pinned titles in one batched request, keyed by title."""
        if not titles:
            return {}
        try:
            pages = self._pages(titles_url(titles))
        except (PhotoError, OSError, ValueError) as error:
            self.log(f"pinned lookup failed: {error}")
            return {}
        return {str(page.get("title", "")): page for page in pages}

    def search(self, photo_id: str, query: str) -> list[dict[str, Any]]:
        """Return search results in API order, recording a failed search."""
        try:
            return self._pages(search_url(query))
        except (PhotoError, OSError, ValueError) as error:
            self.rejected.append({"id": photo_id, "title": "", "reason": f"search failed: {error}"})
            self.log(f"{photo_id}: search failed: {error}")
            return []

    def select(
        self, photo_id: str, subject: Subject, pages: list[dict[str, Any]], selection: str
    ) -> dict[str, Any] | None:
        """Download the first candidate that passes every screen."""
        for page in pages:
            parsed, reason = candidate_reason(page)
            title = str(page.get("title", ""))
            if parsed is None or title in self.seen:
                self.rejected.append({"id": photo_id, "title": title, "reason": reason or "already selected"})
                continue
            destination = self.photos_dir / f"{photo_id}.jpg"
            try:
                width, height = download_photo(self.fetcher, parsed["download_url"], destination)
            except (PhotoError, OSError) as error:
                destination.unlink(missing_ok=True)
                self.rejected.append({"id": photo_id, "title": title, "reason": str(error)})
                self.log(f"{photo_id}: rejected {title}: {error}")
                continue
            self.seen.add(title)
            return {
                "id": photo_id,
                "path": f"photos/{photo_id}.jpg",
                "sha256": sha256_file(destination),
                "width": width,
                "height": height,
                "subject": subject.subject,
                "tags": list(subject.tags),
                "source_url": parsed["source_url"],
                "author": parsed["author"],
                "license": parsed["license"],
                "license_url": parsed["license_url"],
                "retrieved_at": self.retrieved_at,
                "title": title,
                "query": subject.query,
                "selection": selection,
            }
        return None


def acquire(  # noqa: PLR0913 - CLI options plus test injection points
    directory: Path,
    subjects: Iterable[Subject] = SUBJECTS,
    fetch: Callable[[str, int], tuple[bytes, str]] | None = None,
    *,
    refresh: bool = False,
    pins: dict[str, str] | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Build or reuse the photo library and return the manifest payload."""
    pins = PINNED_TITLES if pins is None else pins
    base = guard_path(directory)
    photos_dir = guard_path(base / "photos")
    photos_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = photos_dir / "photos.json"
    if not refresh and library_is_valid(photos_dir, manifest_path):
        log(f"photos.json is valid; skipping download (use --refresh): {manifest_path}")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    wall_start, cpu_start = time.perf_counter(), time.process_time()
    budget = RequestBudget()
    run = _Run(
        fetcher=fetch or budget.fetch,
        photos_dir=photos_dir,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        log=log,
    )
    subject_list = list(subjects)
    pinned_pages = run.pinned_pages([pins[s.slug] for s in subject_list if s.slug in pins])
    photos: list[dict[str, Any]] = []
    for number, subject in enumerate(subject_list, start=1):
        photo_id = f"p{number:02d}-{subject.slug}"
        chosen = None
        pin = pins.get(subject.slug)
        if pin is not None:
            pages = [pinned_pages[pin]] if pin in pinned_pages else []
            chosen = run.select(photo_id, subject, pages, "pinned")
            if chosen is None:
                log(f"{photo_id}: pinned title unavailable or rejected; searching")
        if chosen is None:
            chosen = run.select(photo_id, subject, run.search(photo_id, subject.query), "search")
        if chosen is None:
            log(f"{photo_id}: no license-valid photo found")
            continue
        photos.append(chosen)
        log(f"{photo_id}: {chosen['title']} ({chosen['license']}, {chosen['selection']})")
    rejected = run.rejected

    selected = {f"{photo['id']}.jpg" for photo in photos}
    for stale in photos_dir.glob("p[0-9][0-9]-*.jpg"):
        if stale.name not in selected:
            stale.unlink()
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    payload: dict[str, Any] = {
        "version": 1,
        "photos": photos,
        "rejected": rejected,
        "resources": {
            "wall_seconds": round(time.perf_counter() - wall_start, 3),
            "cpu_seconds": round(time.process_time() - cpu_start, 3),
            "child_cpu_seconds": round(children.ru_utime + children.ru_stime, 3),
            "peak_rss_mib": round(_rss_mib(resource.RUSAGE_SELF), 1),
            "requests": budget.used if fetch is None else None,
            "rate_limit_retries": budget.retries if fetch is None else None,
            "scope": (
                "Single Python process for the complete acquisition run, including sequential "
                "Commons API/download network waits and Pillow normalization. CPU via "
                "time.process_time (process user+system); peak RSS via getrusage(RUSAGE_SELF) "
                "ru_maxrss, which includes interpreter startup. No worker subprocesses."
            ),
            "machine": f"{platform.system()} {platform.machine()} Python {platform.python_version()}",
        },
    }
    temporary = manifest_path.with_name(".photos.json.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(manifest_path)
    return payload


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--directory", type=Path, required=True, help="wild-v1 artifact directory")
    parser.add_argument("--refresh", action="store_true", help="re-download even when photos.json is valid")
    args = parser.parse_args(argv)
    payload = acquire(args.directory, refresh=args.refresh)
    print(f"{len(payload['photos'])} photos; resources: {json.dumps(payload.get('resources'))}")
    return 0 if payload["photos"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
