"""Image-only multimodal embedding retrieval DEV fixtures and local scoring.

No credentials, network requests, model inference or native text are used when
constructing image embedding request bodies. Native extraction is a separate
literal baseline only. All fixtures are repository-authored MIT synthetic PDFs.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

from bench.feature_cases import page_pdf, text_op

FAMILIES = (
    ("invoice", "payment", "Payment due within 30 days", "Payment due within 60 days"),
    ("invoice", "subtotal", "Invoice subtotal 125 USD", "Invoice subtotal 125 EUR"),
    ("financial", "growth", "Net revenue growth 12 percent", "Net revenue growth 21 percent"),
    ("financial", "cash", "Operating cash flow 500 million", "Cash operating flow 500 million"),
    ("scientific", "wavelength", "Measured wavelength 550 nm", "Measured wavelength 550 mm"),
    ("scientific", "dose", "Recommended dosage 20 mg daily", "Daily mg 20 dosage recommended"),
)


def retrieval_cases() -> dict[str, Any]:
    """Build 24 pages, six positive queries and two deliberate no-match controls."""
    documents = []
    queries = []
    for domain, name, phrase, near in FAMILIES:
        family = f"{domain}-{name}"
        words = phrase.split()
        for variant in ("wrapped", "hyphenated", "separate-cells", "near-phrase"):
            doc_id = f"{family}-{variant}"
            operations = [
                text_op(f"{domain.title()} report", 40, 740, size=22, font="F2"),
                text_op("Period 2026 | Approved record", 40, 710, size=12),
                "0.92 0.95 0.98 rg 40 540 520 120 re f 0 0 0 rg",
            ]
            if variant == "separate-cells":
                # Exact same ordered words as wrapped positive, physically split
                # across separately ruled cells. These are independent entries.
                step = 500 / len(words)
                for i, word in enumerate(words):
                    x = 45 + i * step
                    operations.extend((f"0 0 0 RG {x} 570 {step} 65 re S", text_op(word, x + 3, 600, size=12)))
            elif variant == "near-phrase":
                middle = len(near.split()) // 2
                operations.extend(
                    (
                        text_op(" ".join(near.split()[:middle]), 55, 620, size=18),
                        text_op(" ".join(near.split()[middle:]), 55, 588, size=18),
                    )
                )
            elif variant == "hyphenated":
                first, rest = words[0], words[1:]
                split = max(2, len(first) // 2)
                operations.extend(
                    (
                        text_op(first[:split] + "-", 55, 632, size=18),
                        text_op(first[split:] + " " + " ".join(rest[:2]), 55, 608, size=18),
                        text_op(" ".join(rest[2:]), 55, 584, size=18),
                    )
                )
            else:
                middle = len(words) // 2
                operations.extend(
                    (
                        text_op(" ".join(words[:middle]), 55, 620, size=18),
                        text_op(" ".join(words[middle:]), 55, 588, size=18),
                    )
                )
            operations.extend(
                (
                    text_op("Archive reference | Internal review", 40, 460),
                    text_op("Notes unrelated to the highlighted record", 40, 430),
                )
            )
            documents.append(
                {
                    "id": doc_id,
                    "pdf_bytes": page_pdf("\n".join(operations)),
                    "bbox": [35, 122, 570, 262],
                    "domain": domain,
                    "family": family,
                    "variant": variant,
                    "source": "Repository-authored synthetic PDF; MIT",
                    "equal_word_pair": f"{family}-wrapped" if variant == "separate-cells" else None,
                }
            )
        queries.append(
            {
                "id": family,
                "text": phrase,
                "positive_ids": [f"{family}-wrapped", f"{family}-hyphenated"],
                "hard_negative_ids": [f"{family}-separate-cells", f"{family}-near-phrase"],
            }
        )
    for name, phrase in (
        ("no-match-tax", "Tax refund 9999 JPY"),
        ("no-match-temperature", "Critical temperature 450 kelvin"),
    ):
        queries.append({"id": name, "text": phrase, "positive_ids": [], "hard_negative_ids": []})
    return {"split": "DEV", "documents": documents, "queries": queries}


def image_embedding_body(model: str, data_urls: Sequence[str]) -> dict[str, Any]:
    """Build the documented OpenRouter image-only embedding request shape."""
    if not data_urls or any(not url.startswith("data:image/") for url in data_urls):
        message = "image inputs must be nonempty image data URLs"
        raise ValueError(message)
    return {
        "model": model,
        "input": [{"content": [{"type": "image_url", "image_url": {"url": url}}]} for url in data_urls],
        "encoding_format": "float",
    }


def query_embedding_body(model: str, queries: Sequence[str]) -> dict[str, Any]:
    """Build plain-string query inputs without undocumented provider fields."""
    if not queries or any(not isinstance(query, str) or not query.strip() for query in queries):
        message = "query inputs must be nonempty strings"
        raise ValueError(message)
    return {"model": model, "input": list(queries), "encoding_format": "float"}


def _unit(vector: Sequence[float], dimension: int | None = None) -> list[float]:
    if not vector or (dimension is not None and len(vector) != dimension):
        message = "empty or mismatched embedding dimension"
        raise ValueError(message)
    values = [float(value) for value in vector]
    if not all(math.isfinite(value) for value in values):
        message = "nonfinite embedding"
        raise ValueError(message)
    scale = max(abs(value) for value in values)
    if not scale:
        message = "zero embedding"
        raise ValueError(message)
    values = [value / scale for value in values]
    norm = math.sqrt(math.fsum(value * value for value in values))
    return [value / norm for value in values]


def _metrics(scores: Mapping[str, Mapping[str, float]], cases: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    doc_ids = {doc["id"] for doc in cases["documents"]}
    expected_queries = {query["id"] for query in cases["queries"]}
    if set(scores) != expected_queries:
        message = "query score IDs do not match fixture IDs"
        raise ValueError(message)
    for query in cases["queries"]:
        score = scores[query["id"]]
        if set(score) != doc_ids or not all(math.isfinite(value) for value in score.values()):
            message = "missing, extra or nonfinite document scores"
            raise ValueError(message)
        positives = set(query["positive_ids"])
        hard = set(query["hard_negative_ids"])
        if not positives <= doc_ids or not hard <= doc_ids or positives & hard:
            message = "invalid relevance IDs"
            raise ValueError(message)
        ranking = sorted(score, key=lambda doc_id: (-score[doc_id], doc_id))
        rank = next((i + 1 for i, doc_id in enumerate(ranking) if doc_id in positives), None)
        comparisons = [score[p] - score[n] for p in positives for n in hard]
        rows.append(
            {
                "id": query["id"],
                "ranking": ranking,
                "scores": dict(score),
                "first_positive_rank": rank,
                "hit_at_1": rank == 1 if positives else None,
                "hit_at_3": rank is not None and rank <= 3 if positives else None,  # noqa: PLR2004 - reported cutoff.
                "recall_at_1": len(positives.intersection(ranking[:1])) / len(positives) if positives else None,
                "recall_at_3": len(positives.intersection(ranking[:3])) / len(positives) if positives else None,
                "reciprocal_rank": 1 / rank if rank else None,
                "pair_wins": sum(delta > 0 for delta in comparisons),
                "pair_ties": sum(delta == 0 for delta in comparisons),
                "pair_comparisons": len(comparisons),
                "top_tie_count": sum(value == score[ranking[0]] for value in score.values()),
                "forced_no_match_false_hit": not positives,
            }
        )
    matched = [row for row in rows if row["reciprocal_rank"] is not None]
    count = len(matched)
    pairs = sum(row["pair_comparisons"] for row in rows)
    return {
        "split": "DEV",
        "matched_queries": count,
        "no_match_queries": len(rows) - count,
        "hit_at_1": sum(row["hit_at_1"] for row in matched) / count if count else None,
        "hit_at_3": sum(row["hit_at_3"] for row in matched) / count if count else None,
        "recall_at_1": sum(row["recall_at_1"] for row in matched) / count if count else None,
        "recall_at_3": sum(row["recall_at_3"] for row in matched) / count if count else None,
        "mrr": sum(row["reciprocal_rank"] for row in matched) / count if count else None,
        "pair_win_rate": sum(row["pair_wins"] for row in rows) / pairs if pairs else None,
        "pair_ties": sum(row["pair_ties"] for row in rows),
        "forced_no_match_false_hits": sum(row["forced_no_match_false_hit"] for row in rows),
        "abstention_threshold": None,
        "rows": rows,
    }


def evaluate(
    vectors: Mapping[str, Sequence[float]], query_vectors: Mapping[str, Sequence[float]], cases: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate vectors and report cosine rankings, recall, MRR and strict pair wins."""
    expected_docs = {doc["id"] for doc in cases["documents"]}
    expected_queries = {query["id"] for query in cases["queries"]}
    if not vectors or set(vectors) != expected_docs or set(query_vectors) != expected_queries:
        message = "embedding IDs must match complete fixture IDs"
        raise ValueError(message)
    dimension = len(next(iter(vectors.values())))
    docs = {key: _unit(value, dimension) for key, value in vectors.items()}
    queries = {key: _unit(value, dimension) for key, value in query_vectors.items()}
    scores = {
        query_id: {doc_id: math.fsum(a * b for a, b in zip(query, doc, strict=True)) for doc_id, doc in docs.items()}
        for query_id, query in queries.items()
    }
    return _metrics(scores, cases)


def normalized_literal(text: str) -> str:
    """Join producer line-wrap hyphens then collapse whitespace and case."""
    return " ".join(re.sub(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)", "", text).casefold().split())


def literal_baseline(cases: Mapping[str, Any]) -> dict[str, Any]:
    """Run native extraction only for the independently labeled literal baseline."""
    import pdfust  # noqa: PLC0415 - only baseline extraction loads the extension.

    texts = {}
    for doc in cases["documents"]:
        with pdfust.Document(stream=doc["pdf_bytes"]) as document:
            texts[doc["id"]] = normalized_literal(document.get_text())
    scores = {
        query["id"]: {doc_id: float(normalized_literal(query["text"]) in text) for doc_id, text in texts.items()}
        for query in cases["queries"]
    }
    result = _metrics(scores, cases)
    result["normalized_texts"] = texts
    result["literal_match_counts"] = {
        query_id: sum(value > 0 for value in row.values()) for query_id, row in scores.items()
    }
    return result
