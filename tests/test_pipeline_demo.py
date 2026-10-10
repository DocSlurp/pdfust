"""Offline viewer source and model output remain inert after rendering."""

from html.parser import HTMLParser

from bench.pipeline_demo import document, render_markdown


class Elements(HTMLParser):
    """Record generated tags and network-capable attributes."""

    def __init__(self) -> None:
        """Initialize retained tag and attribute observations."""
        super().__init__()
        self.tags: list[str] = []
        self.urls: list[str] = []
        self.events: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Retain attributes that could execute code or fetch resources."""
        self.tags.append(tag)
        self.urls.extend(value for key, value in attrs if key in ("href", "src") and value is not None)
        self.events.extend(key for key, _ in attrs if key.startswith("on"))


def test_source_and_model_markup_cannot_execute_or_fetch() -> None:
    hostile = '</pre><script>alert("x")</script><img src="https://example.com/pixel" onerror="alert(1)">'
    markdown = (
        hostile + "\n\n![track](https://example.com/pixel)\n\n[execute](javascript:alert(1))\n\n<https://example.com>"
    )
    result = document(
        page_id=hostile,
        png=b"PNG",
        markdown=markdown,
        native={"values": [hostile]},
        output={"source_text": hostile},
        metadata={"note": hostile},
    )
    parser = Elements()
    parser.feed(result)
    assert "script" not in parser.tags
    assert parser.events == []
    assert parser.urls == ["data:image/png;base64,UE5H", "source.pdf"]
    assert "&lt;script&gt;" in result
    assert "default-src 'none'" in result


def test_markdown_tables_render_and_raw_html_stays_text() -> None:
    rendered = render_markdown("| Column | Value |\n| --- | --- |\n| Wrapped content | 10 |\n\n<b>literal</b>")
    assert "<table>" in rendered
    assert "Wrapped content" in rendered
    assert "&lt;b&gt;literal&lt;/b&gt;" in rendered


def test_static_html_merged_table_spans_survive_sanitization() -> None:
    rendered = render_markdown(
        '<table onclick="alert(1)"><tr><td rowspan="2" colspan="3" '
        'style="background:url(https://example.com)">Merged &amp; literal</td></tr></table>'
    )
    assert '<td rowspan="2" colspan="3">' in rendered
    assert "Merged &amp; literal" in rendered
    assert "onclick" not in rendered
    assert "style=" not in rendered
    assert "https://example.com" not in rendered
