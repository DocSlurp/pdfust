from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from bench import wild_photos
from PIL import Image


def _page(title: str, index: int, short: str, code: str, **info: object) -> dict[str, object]:
    image_info: dict[str, object] = {
        "width": 3000,
        "height": 2000,
        "mime": "image/jpeg",
        "thumburl": f"https://upload.wikimedia.org/thumb/{index}.jpg",
        "descriptionurl": f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}",
        "extmetadata": {
            "LicenseShortName": {"value": short},
            "License": {"value": code},
            "Artist": {"value": '<a href="https://example.org/u">Jane &amp; Co</a>'},
            "Restrictions": {"value": ""},
        },
    }
    image_info.update(info)
    return {"title": title, "index": index, "imageinfo": [image_info]}


CANNED = {
    "query": {
        "pages": [
            _page("File:Harbor CC BY.jpg", 1, "CC BY-SA 4.0", "cc-by-sa-4.0"),
            _page("File:Harbor PD.jpg", 3, "Public domain", "pd"),
            _page("File:Harbor CC0.jpg", 2, "CC0", "cc0"),
            _page("File:Harbor workers.jpg", 4, "CC0", "cc0"),
            _page("File:Harbor small.jpg", 5, "CC0", "cc0", width=640, height=480),
        ]
    }
}


def _jpeg(size: tuple[int, int] = (40, 20)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buffer, "JPEG")
    return buffer.getvalue()


def test_license_filter_and_metadata_parsing() -> None:
    pages = wild_photos.ordered_pages(CANNED)
    assert [page["title"] for page in pages][:3] == [
        "File:Harbor CC BY.jpg",
        "File:Harbor CC0.jpg",
        "File:Harbor PD.jpg",
    ]
    results = [wild_photos.candidate_reason(page) for page in pages]
    assert results[0][0] is None
    assert "license not PD/CC0" in results[0][1]
    cc0 = results[1][0]
    assert cc0 is not None
    assert cc0["license"] == "CC0 1.0"
    assert cc0["license_url"] == wild_photos.CC0_URL
    assert cc0["author"] == "Jane & Co"
    assert cc0["source_url"].startswith("https://commons.wikimedia.org/")
    pd = results[2][0]
    assert pd is not None
    assert pd["license"] == "Public domain"
    assert results[3][0] is None
    assert "people" in results[3][1]
    assert results[4][0] is None
    assert "too small" in results[4][1]


def test_rejects_personality_restriction_and_unknown_license() -> None:
    page = _page("File:Street.jpg", 1, "CC0", "cc0")
    page["imageinfo"][0]["extmetadata"]["Restrictions"] = {"value": "personality"}  # type: ignore[index]
    assert wild_photos.candidate_reason(page)[0] is None
    assert wild_photos.classify_license({}) is None
    assert wild_photos.classify_license({"LicenseShortName": {"value": "GFDL"}}) is None


def test_normalize_image_strips_exif_and_bounds_size(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    exif = Image.Exif()
    exif[0x010E] = "secret description"
    Image.new("RGBA", (3200, 1600), (10, 20, 30, 128)).convert("RGB").save(buffer, "JPEG", exif=exif)
    destination = tmp_path / "p01-test.jpg"
    assert wild_photos.normalize_image(buffer.getvalue(), destination) == (1600, 800)
    with Image.open(destination) as image:
        assert image.mode == "RGB"
        assert image.format == "JPEG"
        assert not image.getexif()
    assert list(tmp_path.iterdir()) == [destination]


def test_normalize_image_rejects_garbage(tmp_path: Path) -> None:
    destination = tmp_path / "bad.jpg"
    with pytest.raises(wild_photos.PhotoError):
        wild_photos.normalize_image(b"not an image" * 10, destination)
    assert not destination.exists()


def test_acquire_offline_is_idempotent(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetch(url: str, _max_bytes: int) -> tuple[bytes, str]:
        calls.append(url)
        if url.startswith(wild_photos.API_URL):
            return json.dumps(CANNED).encode(), "application/json"
        return _jpeg(), "image/jpeg"

    subject = wild_photos.Subject("harbor", "harbor", "harbor", ("harbor",))
    payload = wild_photos.acquire(tmp_path, [subject], fetch=fetch, pins={}, log=lambda _: None)
    assert [photo["id"] for photo in payload["photos"]] == ["p01-harbor"]
    photo = payload["photos"][0]
    assert photo["title"] == "File:Harbor CC0.jpg"
    assert photo["path"] == "photos/p01-harbor.jpg"
    assert (tmp_path / photo["path"]).is_file()
    assert {"wall_seconds", "cpu_seconds", "peak_rss_mib", "scope"} <= set(payload["resources"])
    count = len(calls)
    again = wild_photos.acquire(tmp_path, [subject], fetch=fetch, pins={}, log=lambda _: None)
    assert again["photos"] == payload["photos"]
    assert len(calls) == count


def test_acquire_prefers_pinned_title_and_falls_back(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetch(url: str, _max_bytes: int) -> tuple[bytes, str]:
        calls.append(url)
        if url.startswith(wild_photos.API_URL):
            return json.dumps(CANNED).encode(), "application/json"
        return _jpeg(), "image/jpeg"

    subjects = [
        wild_photos.Subject("harbor", "harbor", "harbor", ("harbor",)),
        wild_photos.Subject("pier", "pier", "pier", ("harbor",)),
    ]
    pins = {"harbor": "File:Harbor PD.jpg", "pier": "File:Harbor CC BY.jpg"}
    payload = wild_photos.acquire(tmp_path, subjects, fetch=fetch, refresh=True, pins=pins, log=lambda _: None)
    first, second = payload["photos"]
    assert (first["title"], first["selection"]) == ("File:Harbor PD.jpg", "pinned")
    # The CC BY pin fails the license screen, so the slot falls back to search order.
    assert (second["title"], second["selection"]) == ("File:Harbor CC0.jpg", "search")
    assert sum("titles=" in url for url in calls) == 1
