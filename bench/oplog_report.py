"""Report retained edit-session scores and provider rates without new inference."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean

from bench.decision_hosted import ARTIFACTS


def main() -> None:
    """Keep slot denominators and stopping outcomes beside efficiency measures."""
    result = json.loads((ARTIFACTS / "oplog-pilot-512/results.json").read_bytes())
    lines = [
        "# R002 coordinate edit-session pilot",
        "",
        (
            "Ten prespecified DEV regions per model, whole-region 512 px images, bounded edit menus. "
            "Initial header band and column hypotheses are supplied by the harness. "
            "This is conditional cell assembly, not independent page extraction. Candidate oracle is unmeasured."
        ),
        "",
        "| Model | Group exact | Slot exact / scorable | Source placement | Mean pair P/R | Conserved |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    rates = []
    for model in sorted({session["model"] for session in result["sessions"]}):
        sessions = [s for s in result["sessions"] if s["model"] == model]
        scores = [s["score"] for s in sessions]
        calls = [c for c in result["calls"] if c["model"] == model]
        unique = {c["entry"]["index"]: c for c in calls if "entry" in c}
        costs = [c["cost"]["effective_usd"] for c in unique.values()]
        cost = sum(costs) if all(c is not None for c in costs) else None
        elapsed = [c["http_elapsed_ms"] for c in unique.values() if not c.get("replayed")]
        seconds = sum(elapsed) / 1000 if elapsed and all(x is not None for x in elapsed) else None
        scorable = sum(s["row_column_exact"] is not None for s in scores)
        lines.append(
            f"| {model} | {sum(s['source_group_exact'] for s in scores)}/{len(scores)} | "
            f"{sum(s['row_column_exact'] is True for s in scores)}/{scorable} | "
            f"{sum(s['placement_correct_sources'] for s in scores if s['placement_correct_sources'] is not None)}/"
            f"{sum(s['placement_scored_sources'] for s in scores)} | "
            f"{mean(s['pair_precision'] for s in scores if s['pair_precision'] is not None):.3f}/"
            f"{mean(s['pair_recall'] for s in scores if s['pair_recall'] is not None):.3f} | "
            f"{sum(s['conservation'] for s in scores)}/{len(scores)} |"
        )
        money = f"{cost:.6f}" if cost is not None else "unknown"
        ppd = f"{len(sessions) / cost:,.0f}" if cost else "unknown"
        ppm = f"{len(sessions) * 60 / seconds:.1f}" if seconds else "unmeasured"
        rates.append(
            f"| {model} | {len(unique)} | {money} | {ppd} | {ppm} | "
            f"{dict(Counter(s['stop_reason'] for s in sessions))} |"
        )
    lines += [
        "",
        "| Model | Provider requests | USD | Region-pages/$ | Region-pages/min | Session endings |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        *rates,
        "",
        (
            "Region-pages count complete attempted sessions, including failures to finish, per summed provider charges "
            "and serial HTTP time for all edits. Each is a region task, not a full-page conversion. "
            "Positive reported charges take precedence; zero/missing charges use retained catalog prices and observed "
            "tokens. Local replay does not establish provider caching. "
            "Preparation CPU/RAM was not measured in this pilot."
        ),
        "",
        (
            "The missing slot annotation stays outside the nine-region slot denominator, "
            "with all ten in group exactness. "
            "Abstention and loop stops retain words but do not count as successful extraction."
        ),
        "",
    ]
    Path("bench/results/oplog-pilot.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
