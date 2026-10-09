# Source-only table-presence gates

| Model / prompt | Borderless presence | Prose false presence | Unresolved/failed positives | Native | Ambiguous unscored | Actual effective USD |
|---|---:|---:|---:|---:|---:|---:|
| perplexity/pplx-decider-v1.1-27b/G001-record-schema | 12/12 | 10/12 | 0 | 4 | 0 | 0.00120408 |
| perplexity/pplx-decider-v1.1-27b/G002-prose-counterevidence | 12/12 | 6/12 | 0 | 4 | 0 | 0.00122136 |
| openai/gpt-6-luna-decisions/G001-record-schema | 12/12 | 2/12 | 0 | 4 | 0 | 0.0037473 |
| openai/gpt-6-luna-decisions/G002-prose-counterevidence | 12/12 | 0/12 | 0 | 4 | 0 | 0.0038361 |

Actual gate accounting perplexity/pplx-decider-v1.1-27b/G001-record-schema: {"unique_requests": 24, "effective_usd": 0.00120408, "known_partial_usd": 0.00120408, "unknown_cost_requests": 0, "http_elapsed_median_ms": 361.78816499887034, "http_elapsed_total_seconds": 9.373502460977761, "http_elapsed_measured_requests": 24}

Actual gate accounting perplexity/pplx-decider-v1.1-27b/G002-prose-counterevidence: {"unique_requests": 24, "effective_usd": 0.00122136, "known_partial_usd": 0.00122136, "unknown_cost_requests": 0, "http_elapsed_median_ms": 366.6105700103799, "http_elapsed_total_seconds": 10.272940593014937, "http_elapsed_measured_requests": 24}

Actual gate accounting openai/gpt-6-luna-decisions/G001-record-schema: {"unique_requests": 24, "effective_usd": 0.0037473, "known_partial_usd": 0.0037473, "unknown_cost_requests": 0, "http_elapsed_median_ms": 322.5261404950288, "http_elapsed_total_seconds": 9.881183098987094, "http_elapsed_measured_requests": 24}

Actual gate accounting openai/gpt-6-luna-decisions/G002-prose-counterevidence: {"unique_requests": 24, "effective_usd": 0.0038361, "known_partial_usd": 0.0038361, "unknown_cost_requests": 0, "http_elapsed_median_ms": 317.86359550460475, "http_elapsed_total_seconds": 9.911242561065592, "http_elapsed_measured_requests": 24}

{
  "unique_requests": 96,
  "effective_usd": 0.01000884,
  "known_partial_usd": 0.01000884,
  "unknown_cost_requests": 0,
  "http_elapsed_median_ms": 355.2193480063579,
  "http_elapsed_total_seconds": 39.438868714045384,
  "http_elapsed_measured_requests": 96,
  "pages": 28,
  "limits": "Presence labels only for borderless/prose. Native controls zero-call; other kinds unscored. No reconstruction or cached cascade performance claim.",
  "tag_prefix": "G001-source-gate/",
  "wave_limit_usd": 0.5,
  "stopped_models": [],
  "budget_stopped": false,
  "frozen_manifest_sha256": "3bb0e4fe51bb083f6957de0be07fa1f88d3182f96a79611bfad75494a14eef13",
  "catalog_provenance": {
    "fetched_at": 1791517626.747666,
    "prices": {
      "anthropic/claude-opus-4.6": {
        "input": 5e-06,
        "output": 2.5e-05
      },
      "cloudflare/clef": {
        "input": 2.4e-07,
        "output": 0.0
      },
      "cloudflare/clef-flash": {
        "input": 2.1e-08,
        "output": 0.0
      },
      "google/gemini-2.5-flash-lite": {
        "input": 1e-07,
        "output": 4e-07
      },
      "google/gemini-3.1-flash-lite": {
        "input": 2.5e-07,
        "output": 1.5e-06
      },
      "google/gemini-embedding-2": {
        "input": 2e-07,
        "output": 0.0
      },
      "inception/mercury-decide": {
        "input": 2e-08,
        "output": 0.0,
        "input_cache_read": 0.0
      },
      "liquid/d1": {
        "input": 4e-08,
        "output": 0.0,
        "input_cache_read": 4e-08
      },
      "nvidia/llama-nemotron-embed-vl-1b-v2:free": {
        "input": 0.0,
        "output": 0.0
      },
      "openai/gpt-6-luna-decisions": {
        "input": 1e-07,
        "output": 0.0,
        "input_cache_read": 0.0,
        "input_cache_write": 0.0
      },
      "perplexity/pplx-decider-v1.1-27b": {
        "input": 2e-08,
        "output": 0.0
      },
      "qwen/qwen3.5-9b": {
        "input": 1e-07,
        "output": 1.5e-07
      },
      "respan/span-01": {
        "input": 2e-08,
        "output": 0.0
      },
      "togethercomputer/tev1-4b-experimental": {
        "input": 4.2e-08,
        "output": 0.0
      },
      "typesafe/jev-1.13": {
        "input": 4.2e-08,
        "output": 0.0
      },
      "upstage/solar-decide-flash": {
        "input": 5e-08,
        "output": 0.0,
        "input_cache_read": 5e-08
      },
      "voyageai/voyage-multimodal-3.5": {
        "input": 1.2e-07,
        "output": 0.0
      }
    },
    "cache_pricing_source": "https://openrouter.ai/api/v1/models?output_modalities=decisions",
    "cache_pricing_fetched_at": 1791518109.7447846
  },
  "execution_resources": {
    "wall_seconds": 62.765214303988614,
    "cpu_seconds": 20.27101411,
    "peak_rss_bytes": 931897344,
    "measurement": "SELF process_time/perf_counter; process-lifetime getrusage RSS; serial requests, no children or periodic sampling; HTTP wait included in wall"
  },
  "preparation": {
    "wall_seconds": 0.05174017600074876,
    "cpu_seconds": 0.051507855000000005,
    "peak_rss_bytes": 931897344,
    "measurement": "perf_counter/process_time SELF; getrusage process-lifetime RSS; single CPU process; no children or periodic sampling"
  },
  "code_sha256": {
    "source_table_gate_run.py": "f8ef9aaae4b541fdb0936987ce140602485215a90c4bbe3c1032b16ad8d3d452",
    "source_table_gate.py": "37396e8a3a067adca4854d92eb9d6b5370df80ca2cfcc4e6086ab92892b10824",
    "decision_hosted.py": "01ea1c35796d81ce034a1b85dcfbaec399467efc9854fc60d23aa732dd65218f"
  }
}

Costs include retained failures. Positive provider charges take precedence; token/catalog estimates are labeled in retained cost records. Reservations are not actual gate costs. Missing costs and HTTP times stay unknown. No model confidence is calibrated correctness. Ambiguous references are unscored.

Gate costs and HTTP timings are actual retained gate measurements only. Applying gate decisions to prior admission answers would be an offline routing simulation, not fresh provider cache or cascade latency/saving measurements. No default PDF behavior changes.
