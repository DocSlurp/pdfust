"""UI mockups for screenshots, SVG charts and photo selection for wild-v1 documents.

Mockups are small standalone HTML pages rendered to PNG by headless Chromium
(``--disable-gpu``). Their text exists only as pixels in the final PDF and is
recorded as ``text_in_image`` or as a ``rendering: "screenshot"`` table.
"""

# ruff: noqa: E501, ISC004, PLC0415, UP031
from __future__ import annotations

import hashlib
import html
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

FONT_STACK = ("'Noto Sans', 'Noto Sans CJK JP', 'Noto Sans Arabic', 'Noto Sans Hebrew', 'Noto Sans Devanagari', "
              "'Noto Sans Thai', 'Noto Color Emoji', sans-serif")


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _page(body: str, css: str, *, lang: str = "en", direction: str = "ltr") -> str:
    return (f"<!doctype html><html lang='{lang}' dir='{direction}'><head><meta charset='utf-8'><style>"
            f"html,body{{margin:0;padding:0;background:#fff}}body{{font-family:{FONT_STACK};font-size:13px;color:#202124}}"
            f"{css}</style></head><body>{body}</body></html>")


# ------------------------------------------------------------------ mockups


def spreadsheet(spec: dict[str, Any]) -> tuple[str, tuple[int, int], list[str]]:
    """Spreadsheet window with column letters, row numbers and a formula bar."""
    rows = spec["rows"]
    width = spec.get("width", 760)
    letters = "ABCDEFGHIJ"
    head = "".join(f"<th class='col'>{letters[i]}</th>" for i in range(len(rows[0])))
    body = ""
    for index, row in enumerate(rows, start=1):
        cells = "".join(
            f"<td class='{'hdr' if index == 1 else ('num' if spec.get('numeric', [False] * len(row))[c] else '')}'>{_e(v)}</td>"
            for c, v in enumerate(row))
        selected = " class='sel'" if index == spec.get("selected_row") else ""
        body += f"<tr{selected}><th class='rn'>{index}</th>{cells}</tr>"
    for index in range(len(rows) + 1, len(rows) + 4):
        body += f"<tr><th class='rn'>{index}</th>" + "<td></td>" * len(rows[0]) + "</tr>"
    tabs = "".join(f"<span class='tab{' on' if i == 0 else ''}'>{_e(t)}</span>" for i, t in enumerate(spec["tabs"]))
    menu = "".join(f"<span>{_e(m)}</span>" for m in spec["menu"])
    css = (".win{border:1px solid #c7c7c7;border-radius:8px;overflow:hidden;width:%dpx}"
           ".title{background:#f1f3f4;padding:8px 12px;font-weight:600;display:flex;gap:8px;align-items:center}"
           ".dot{width:11px;height:11px;border-radius:50%%;display:inline-block}"
           ".menu{padding:4px 12px;border-bottom:1px solid #ddd;color:#444}.menu span{margin-right:14px}"
           ".fx{display:flex;border-bottom:1px solid #ddd;font-size:12px}.fx b{width:60px;padding:4px 8px;border-right:1px solid #ddd;color:#555}"
           ".fx i{padding:4px 8px;font-style:normal}"
           "table{border-collapse:collapse;width:100%%;font-size:12.5px}td,th{border:1px solid #e0e0e0;padding:3px 7px;white-space:nowrap}"
           "th.col,th.rn{background:#f8f9fa;color:#5f6368;font-weight:400;text-align:center}th.rn{width:28px}"
           "td.hdr{font-weight:700;background:#e8f0fe}td.num{text-align:right;font-variant-numeric:tabular-nums}"
           "tr.sel td{background:#fef7e0}.tabs{background:#f1f3f4;padding:5px 8px;border-top:1px solid #ddd}"
           ".tab{padding:3px 12px;margin-right:4px;color:#555}.tab.on{background:#fff;border-radius:3px;color:#188038;font-weight:600}") % width
    page = ("<div class='win'><div class='title'><span class='dot' style='background:#ff5f57'></span>"
            "<span class='dot' style='background:#febc2e'></span><span class='dot' style='background:#28c840'></span>"
            f"&nbsp;{_e(spec['title'])}</div><div class='menu'>{menu}</div>"
            f"<div class='fx'><b>{_e(spec['cell'])}</b><i>{_e(spec['formula'])}</i></div>"
            f"<table><tr><th class='rn'></th>{head}</tr>{body}</table><div class='tabs'>{tabs}</div></div>")
    height = 220 + 30 * (len(rows) + 3)
    text = [spec["title"], *spec["menu"], spec["cell"], spec["formula"], *spec["tabs"]]
    return _page(page, css, lang=spec.get("lang", "en")), (width + 2, height), text


def dashboard(spec: dict[str, Any]) -> tuple[str, tuple[int, int], list[str]]:
    """Analytics dashboard with KPI tiles, a sparkline and a small table."""
    tiles = "".join(f"<div class='tile'><div class='lab'>{_e(k)}</div><div class='val'>{_e(v)}</div>"
                    f"<div class='d {'up' if d.startswith('+') else 'dn'}'>{_e(d)}</div></div>" for k, v, d in spec["kpis"])
    rows = spec["rows"]
    head = "".join(f"<th>{_e(h)}</th>" for h in rows[0])
    body = "".join("<tr>" + "".join(f"<td>{_e(v)}</td>" for v in row) + "</tr>" for row in rows[1:])
    series = spec["series"]
    top, bottom = max(series), min(series)
    points = " ".join(f"{10 + i * 520 / (len(series) - 1):.1f},{90 - (v - bottom) / ((top - bottom) or 1) * 70:.1f}" for i, v in enumerate(series))
    nav = "".join(f"<div class='nav{' on' if i == 0 else ''}'>{_e(n)}</div>" for i, n in enumerate(spec["nav"]))
    css = (".app{display:flex;width:900px;min-height:%dpx;background:#f6f7fb}.side{width:150px;background:#1f2a44;color:#c9d3ea;padding:14px 0}"
           ".brand{font-weight:700;color:#fff;padding:0 16px 14px}.nav{padding:7px 16px}.nav.on{background:#2f3d61;color:#fff}"
           ".main{flex:1;padding:16px 20px}.h{display:flex;justify-content:space-between;align-items:center}"
           ".h h2{margin:0;font-size:18px}.range{border:1px solid #cdd3e0;border-radius:6px;padding:4px 10px;background:#fff;font-size:12px}"
           ".tiles{display:flex;gap:12px;margin:14px 0}.tile{flex:1;background:#fff;border-radius:8px;padding:10px 12px;box-shadow:0 1px 2px #0002}"
           ".lab{color:#6b7280;font-size:12px}.val{font-size:21px;font-weight:700;margin:2px 0}.d{font-size:12px}.up{color:#0a7d38}.dn{color:#c5221f}"
           ".card{background:#fff;border-radius:8px;padding:10px 12px;box-shadow:0 1px 2px #0002;margin-bottom:12px}"
           ".card h3{margin:0 0 6px;font-size:13px;color:#374151}table{border-collapse:collapse;width:100%%;font-size:12.5px}"
           "th{text-align:left;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;padding:4px 6px}"
           "td{border-bottom:1px solid #f0f1f4;padding:4px 6px}") % (spec.get("height", 520))
    page = (f"<div class='app'><div class='side'><div class='brand'>{_e(spec['brand'])}</div>{nav}</div><div class='main'>"
            f"<div class='h'><h2>{_e(spec['title'])}</h2><span class='range'>{_e(spec['range'])}</span></div>"
            f"<div class='tiles'>{tiles}</div><div class='card'><h3>{_e(spec['series_title'])}</h3>"
            f"<svg width='540' height='100'><polyline fill='none' stroke='#3b6fd8' stroke-width='2.5' points='{points}'/></svg></div>"
            f"<div class='card'><h3>{_e(spec['table_title'])}</h3><table><tr>{head}</tr>{body}</table></div></div></div>")
    text = [spec["brand"], *spec["nav"], spec["title"], spec["range"]]
    for k, v, d in spec["kpis"]:
        text += [k, v, d]
    text += [spec["series_title"], spec["table_title"]]
    return _page(page, css), (900, spec.get("height", 520) + 80), text


def email(spec: dict[str, Any]) -> tuple[str, tuple[int, int], list[str]]:
    """Email client reading pane."""
    folders = "".join(f"<div class='f{' on' if i == 0 else ''}'>{_e(f)}</div>" for i, f in enumerate(spec["folders"]))
    body = "".join(f"<p>{_e(p)}</p>" for p in spec["body"])
    direction = spec.get("dir", "ltr")
    css = (".app{display:flex;width:820px;min-height:%dpx;border:1px solid #d0d4da}.nav{width:150px;background:#f3f4f6;padding:12px 0}"
           ".f{padding:6px 14px;color:#374151}.f.on{background:#dbe7fb;color:#1a56db;font-weight:600}"
           ".read{flex:1;padding:16px 22px}.subj{font-size:18px;font-weight:600;margin-bottom:10px}"
           ".meta{display:flex;justify-content:space-between;color:#4b5563;font-size:12.5px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}"
           ".meta b{color:#111827}p{margin:10px 0;line-height:1.45}.att{display:inline-block;border:1px solid #d1d5db;border-radius:6px;padding:6px 10px;font-size:12px;margin-top:6px}") % spec.get("height", 430)
    attachment = f"<div class='att'>📎 {_e(spec['attachment'])}</div>" if spec.get("attachment") else ""
    page = (f"<div class='app'><div class='nav'>{folders}</div><div class='read'><div class='subj'>{_e(spec['subject'])}</div>"
            f"<div class='meta'><div><b>{_e(spec['from'])}</b><br>{_e(spec['to'])}</div><div>{_e(spec['date'])}</div></div>"
            f"{body}{attachment}</div></div>")
    text = [*spec["folders"], spec["subject"], spec["from"], spec["to"], spec["date"], *spec["body"]]
    if spec.get("attachment"):
        text.append(spec["attachment"])
    return _page(page, css, lang=spec.get("lang", "en"), direction=direction), (822, spec.get("height", 430) + 80), text


def chat(spec: dict[str, Any]) -> tuple[str, tuple[int, int], list[str]]:
    """Team chat channel with message bubbles."""
    messages = ""
    text = [spec["channel"], spec["topic"]]
    for name, time, message in spec["messages"]:
        initials = "".join(part[0] for part in name.split()[:2])
        messages += (f"<div class='m'><div class='av'>{_e(initials)}</div><div><div class='who'><b>{_e(name)}</b>"
                     f"<span>{_e(time)}</span></div><div class='tx'>{_e(message)}</div></div></div>")
        text += [name, time, message]
    css = (".app{width:640px;min-height:%dpx;border:1px solid #d6d6d6;border-radius:8px;overflow:hidden}"
           ".top{background:#4a154b;color:#fff;padding:10px 14px}.top b{font-size:15px}.top div{font-size:12px;opacity:.85}"
           ".m{display:flex;gap:10px;padding:8px 14px}.av{width:34px;height:34px;border-radius:6px;background:#7c9a5e;color:#fff;"
           "display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;flex:none}"
           ".who span{color:#6b7280;font-size:11.5px;margin-left:8px}.tx{line-height:1.4}") % spec.get("height", 360)
    page = f"<div class='app'><div class='top'><b>{_e(spec['channel'])}</b><div>{_e(spec['topic'])}</div></div>{messages}</div>"
    return _page(page, css), (642, spec.get("height", 360) + 80), text


# ------------------------------------------------------------------ charts


def bar_chart_svg(spec: dict[str, Any], *, width: int = 520, height: int = 230, font: str = "Noto Sans") -> str:
    """Draw a grouped vertical bar chart with axis labels, gridlines and a legend as real SVG text."""
    categories, series = spec["categories"], spec["series"]
    colors = spec.get("colors", ["#2f5d8a", "#e0a43a", "#6a9b5e", "#b0453f"])
    top = spec.get("max") or max(max(values) for _, values in series) * 1.15
    left, right, upper, lower = 54, 12, 30, 34
    plot_w, plot_h = width - left - right, height - upper - lower
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}' "
             f"font-family=\"{font}\" font-size='11' role='img'>"]
    if spec.get("title"):
        parts.append(f"<text x='{left}' y='16' font-size='12.5' font-weight='700' fill='#222'>{_e(spec['title'])}</text>")
    ticks = spec.get("ticks", 4)
    for index in range(ticks + 1):
        value = top * index / ticks
        y = upper + plot_h - plot_h * index / ticks
        parts.append(f"<line x1='{left}' x2='{width - right}' y1='{y:.1f}' y2='{y:.1f}' stroke='#e3e3e3'/>")
        parts.append(f"<text x='{left - 6}' y='{y + 4:.1f}' text-anchor='end' fill='#555'>{_e(spec['tick_format'](value))}</text>")
    group = plot_w / len(categories)
    bar = group * 0.72 / len(series)
    for ci, category in enumerate(categories):
        for si, (_, values) in enumerate(series):
            h = plot_h * values[ci] / top
            x = left + ci * group + group * 0.14 + si * bar
            parts.append(f"<rect x='{x:.1f}' y='{upper + plot_h - h:.1f}' width='{bar - 1:.1f}' height='{h:.1f}' fill='{colors[si]}'/>")
        parts.append(f"<text x='{left + ci * group + group / 2:.1f}' y='{height - lower + 15}' text-anchor='middle' fill='#333'>{_e(category)}</text>")
    lx = left
    for si, (name, _) in enumerate(series):
        parts.append(f"<rect x='{lx}' y='{height - 11}' width='9' height='9' fill='{colors[si]}'/>")
        parts.append(f"<text x='{lx + 13}' y='{height - 3}' fill='#333'>{_e(name)}</text>")
        lx += 24 + 7 * len(name)
    parts.append("</svg>")
    return "".join(parts)


def line_chart_svg(spec: dict[str, Any], *, width: int = 520, height: int = 230, font: str = "Noto Sans") -> str:
    """Multi-series line chart with point markers."""
    categories, series = spec["categories"], spec["series"]
    colors = spec.get("colors", ["#2f5d8a", "#c8553d", "#6a9b5e"])
    low = spec.get("min", 0)
    top = spec.get("max") or max(max(values) for _, values in series) * 1.15
    left, right, upper, lower = 54, 30, 30, 34
    plot_w, plot_h = width - left - right, height - upper - lower
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}' "
             f"font-family=\"{font}\" font-size='11' role='img'>"]
    if spec.get("title"):
        parts.append(f"<text x='{left}' y='16' font-size='12.5' font-weight='700' fill='#222'>{_e(spec['title'])}</text>")
    ticks = spec.get("ticks", 4)
    for index in range(ticks + 1):
        value = low + (top - low) * index / ticks
        y = upper + plot_h - plot_h * index / ticks
        parts.append(f"<line x1='{left}' x2='{width - right}' y1='{y:.1f}' y2='{y:.1f}' stroke='#e3e3e3'/>")
        parts.append(f"<text x='{left - 6}' y='{y + 4:.1f}' text-anchor='end' fill='#555'>{_e(spec['tick_format'](value))}</text>")
    step = plot_w / max(len(categories) - 1, 1)
    for ci, category in enumerate(categories):
        parts.append(f"<text x='{left + ci * step:.1f}' y='{height - lower + 15}' text-anchor='middle' fill='#333'>{_e(category)}</text>")
    for si, (_, values) in enumerate(series):
        points = [(left + i * step, upper + plot_h - plot_h * (v - low) / (top - low)) for i, v in enumerate(values)]
        parts.append(f"<polyline fill='none' stroke='{colors[si]}' stroke-width='2.2' points='{' '.join(f'{x:.1f},{y:.1f}' for x, y in points)}'/>")
        parts.extend(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3' fill='{colors[si]}'/>" for x, y in points)
    lx = left
    for si, (name, _) in enumerate(series):
        parts.append(f"<rect x='{lx}' y='{height - 11}' width='9' height='9' fill='{colors[si]}'/>")
        parts.append(f"<text x='{lx + 13}' y='{height - 3}' fill='#333'>{_e(name)}</text>")
        lx += 24 + 7 * len(name)
    parts.append("</svg>")
    return "".join(parts)


def chart_labels(spec: dict[str, Any], *, ticks: bool = True) -> list[str]:
    """Visible strings of a chart (for raster charts' ``text_in_image``)."""
    text = [spec["title"]] if spec.get("title") else []
    if ticks:
        count = spec.get("ticks", 4)
        low = spec.get("min", 0)
        top = spec.get("max") or max(max(v) for _, v in spec["series"]) * 1.15
        text += [spec["tick_format"](low + (top - low) * i / count) for i in range(count + 1)]
    return text + list(spec["categories"]) + [name for name, _ in spec["series"]]


def raster_chart_page(svg: str) -> tuple[str, tuple[int, int]]:
    """Wrap one SVG for a PNG screenshot."""
    width = int(svg.split("width='")[1].split("'", maxsplit=1)[0])
    height = int(svg.split("height='")[1].split("'", maxsplit=1)[0])
    return _page(f"<div style='padding:6px'>{svg}</div>", ""), (width + 12, height + 60)


MOCKUPS = {"spreadsheet": spreadsheet, "dashboard": dashboard, "email": email, "chat": chat}


# ------------------------------------------------------------------ photos


def load_photos(directory: Path) -> list[dict[str, Any]]:
    """Read ``photos/photos.json`` when present; missing or malformed manifests yield no photos."""
    manifest = directory / "photos" / "photos.json"
    if not manifest.is_file():
        return []
    try:
        records = json.loads(manifest.read_text(encoding="utf-8")).get("photos", [])
    except (OSError, ValueError):
        return []
    return sorted((r for r in records if (directory / r.get("path", "")).is_file()), key=lambda r: r["id"])


def choose_photo(photos: list[dict[str, Any]], prefer: list[str], tags: list[str], used: set[str]) -> dict[str, Any] | None:
    """Pick by preferred slug, then by shared tag, then any unused photo; deterministic by id."""
    available = [p for p in photos if p["id"] not in used]
    for slug in prefer:
        for photo in available:
            if photo["id"].split("-", 1)[-1] == slug:
                return photo
    for tag in tags:
        for photo in available:
            if tag in photo.get("tags", []):
                return photo
    return available[0] if available else None


def placeholder_photo(path: Path, key: str, size: tuple[int, int] = (960, 640)) -> None:
    """Write a deterministic photo-like JPEG (sky/ground gradient and soft shapes) without text."""
    from PIL import Image, ImageDraw, ImageFilter

    digest = hashlib.sha256(key.encode()).digest()
    width, height = size
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    sky = (90 + digest[0] % 60, 130 + digest[1] % 60, 170 + digest[2] % 70)
    ground = (60 + digest[3] % 70, 90 + digest[4] % 60, 50 + digest[5] % 50)
    horizon = int(height * (0.45 + digest[6] % 20 / 100))
    for y in range(height):
        base, end, t = (sky, (225, 230, 235), y / horizon) if y < horizon else (ground, (30, 40, 30), (y - horizon) / (height - horizon))
        draw.line([(0, y), (width, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(base, end, strict=True)))
    for index in range(7):
        x, y = digest[7 + index] * width // 256, horizon - digest[14 + index] % 120
        r = 40 + digest[21 + index] % 90
        draw.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=(40 + digest[index] % 50, 70 + index * 9, 45))
    image.filter(ImageFilter.GaussianBlur(3)).save(path, quality=88)
