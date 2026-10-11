"""Frozen public native decision catalog for separately named extension experiments.

Public GET snapshot: 2026-10-11 05:13 UTC. Catalog presence is advertised
availability, not successful account access. Prices are exact USD/token strings.
No credentials or paid transport are implemented here.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
VERCEL_D1_ENDPOINT = "https://ai-gateway.vercel.sh/v1/decisions"
VERCEL_TYPESAFE_ENDPOINT = "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
CATALOG_SHA256 = {
    "openrouter": "fcbc4e7f5112541265888fd8a91625f6e1061f082b205731f9d51c607f17c2c7",
    "vercel": "35fdf51d7f0dd6ece4e68e99797ae89090799d1c2ede8edb28c686044c004959",
}

# Distinct checkpoints/tiers only: latest aliases and free duplicate routes omitted.
OPENROUTER = {
    "microsoft/microsoft-decision-1": {
        "canonical_ids": ["microsoft/microsoft-decision-1", "microsoft/microsoft-decision-1-20261009"],
        "input_modalities": ["text"],
        "context_tokens": 32768,
        "rates_per_token": {"prompt": "0.000000042", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "nace-ai/drex-v1.5": {
        "canonical_ids": ["nace-ai/drex-v1.5", "nace-ai/drex-v1.5-20261009"],
        "input_modalities": ["text"],
        "context_tokens": 131072,
        "rates_per_token": {"prompt": "0.00000004", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "cloudflare/clef-omni": {
        "canonical_ids": ["cloudflare/clef-omni", "cloudflare/clef-omni-20261009"],
        "input_modalities": ["text", "image"],
        "context_tokens": 65536,
        "rates_per_token": {"prompt": "0.00000015", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "upstage/solar-decide-flash": {
        "canonical_ids": ["upstage/solar-decide-flash", "upstage/solar-decide-flash-20261008"],
        "input_modalities": ["text"],
        "context_tokens": 524288,
        "rates_per_token": {"prompt": "0.00000005", "completion": "0", "input_cache_read": "0.00000005"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "perplexity/pplx-decider-v1.1-27b": {
        "canonical_ids": ["perplexity/pplx-decider-v1.1-27b", "perplexity/pplx-decider-v1.1-27b-20261006"],
        "input_modalities": ["text", "image"],
        "context_tokens": 262144,
        "rates_per_token": {"prompt": "0.00000002", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "openai/gpt-6-luna-decisions": {
        "canonical_ids": ["openai/gpt-6-luna-decisions", "openai/gpt-6-luna-decisions-20261006"],
        "input_modalities": ["text", "image"],
        "context_tokens": 1050000,
        "rates_per_token": {
            "prompt": "0.0000001",
            "completion": "0",
            "web_search": "0.01",
            "input_cache_read": "0",
            "input_cache_write": "0",
        },
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "liquid/d1": {
        "canonical_ids": ["liquid/d1", "liquid/d1-20260930"],
        "input_modalities": ["text"],
        "context_tokens": 65536,
        "rates_per_token": {"prompt": "0.00000004", "completion": "0", "input_cache_read": "0.00000004"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "cloudflare/clef-flash": {
        "canonical_ids": ["cloudflare/clef-flash", "cloudflare/clef-flash"],
        "input_modalities": ["text", "image"],
        "context_tokens": 65536,
        "rates_per_token": {"prompt": "0.000000038", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "cloudflare/clef": {
        "canonical_ids": ["cloudflare/clef", "cloudflare/clef"],
        "input_modalities": ["text", "image"],
        "context_tokens": 65536,
        "rates_per_token": {"prompt": "0.00000024", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "togethercomputer/tev1-4b-experimental": {
        "canonical_ids": ["togethercomputer/tev1-4b-experimental", "togethercomputer/tev1-4b-experimental-20260923"],
        "input_modalities": ["text"],
        "context_tokens": 32768,
        "rates_per_token": {"prompt": "0.000000042", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "inception/mercury-decide": {
        "canonical_ids": ["inception/mercury-decide", "inception/mercury-decide-20260930"],
        "input_modalities": ["text"],
        "context_tokens": 65536,
        "rates_per_token": {"prompt": "0.00000002", "completion": "0", "input_cache_read": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "upstage/solar-decide": {
        "canonical_ids": ["upstage/solar-decide", "upstage/solar-decide-20260928"],
        "input_modalities": ["text"],
        "context_tokens": 524288,
        "rates_per_token": {"prompt": "0.00000005", "completion": "0", "input_cache_read": "0.00000005"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "respan/span-01": {
        "canonical_ids": ["respan/span-01", "respan/span-01-20260925"],
        "input_modalities": ["text"],
        "context_tokens": None,
        "rates_per_token": {"prompt": "0.00000002", "completion": "0"},
        "compatibility_only": True,
        "wire_kind": "openrouter_native",
    },
    "respan/span-01-lite": {
        "canonical_ids": ["respan/span-01-lite", "respan/span-01-lite-20260925"],
        "input_modalities": ["text"],
        "context_tokens": None,
        "rates_per_token": {"prompt": "0", "completion": "0"},
        "compatibility_only": True,
        "wire_kind": "openrouter_native",
    },
    "jaredpalmer/kev-4b": {
        "canonical_ids": ["jaredpalmer/kev-4b", "jaredpalmer/kev-4b-20260924"],
        "input_modalities": ["text"],
        "context_tokens": 8192,
        "rates_per_token": {"prompt": "0.000000042", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
    "typesafe/jev-1.13": {
        "canonical_ids": ["typesafe/jev-1.13", "typesafe/jev-1.13-20260917"],
        "input_modalities": ["text"],
        "context_tokens": 64000,
        "rates_per_token": {"prompt": "0.000000042", "completion": "0"},
        "compatibility_only": False,
        "wire_kind": "openrouter_native",
    },
}
VERCEL = {
    "convaiinnovations/laya": {
        "canonical_ids": ["convaiinnovations/laya"],
        "input_modalities": ["text"],
        "context_tokens": 8192,
        "rates_per_token": {"input": "0", "output": "0"},
        "compatibility_only": False,
        "wire_kind": "vercel_typesafe",
    },
    "liquid/d1": {
        "canonical_ids": ["liquid/d1"],
        "input_modalities": ["text", "image"],
        "context_tokens": 65536,
        "rates_per_token": {"input": "0.00000004", "output": "0"},
        "compatibility_only": False,
        "wire_kind": "vercel_native_d1",
    },
    "microsoft/microsoft-decision-1": {
        "canonical_ids": ["microsoft/microsoft-decision-1"],
        "input_modalities": ["text"],
        "context_tokens": 32768,
        "rates_per_token": {"input": "0.000000042", "output": "0"},
        "compatibility_only": True,
        "wire_kind": "vercel_typesafe",
    },
    "openai/gpt-6-luna-decisions": {
        "canonical_ids": ["openai/gpt-6-luna-decisions"],
        "input_modalities": ["text"],
        "context_tokens": 1050000,
        "rates_per_token": {"input": "0.0000001"},
        "compatibility_only": True,
        "wire_kind": "vercel_typesafe",
    },
    "typesafe-ai/jev": {
        "canonical_ids": ["typesafe-ai/jev"],
        "input_modalities": ["text"],
        "context_tokens": 32000,
        "rates_per_token": {"input": "0.000000042", "output": "0"},
        "compatibility_only": True,
        "wire_kind": "vercel_typesafe",
    },
}


def model_spec(model_id: str, provider: str = "openrouter") -> dict[str, Any]:
    """Return a detached exact model contract, rejecting unknown providers/IDs."""
    registries = {"openrouter": OPENROUTER, "vercel": VERCEL}
    if provider not in registries or model_id not in registries[provider]:
        message = "Unknown extension model/provider identity"
        raise ValueError(message)
    spec = deepcopy(registries[provider][model_id])
    spec.update(model=model_id, provider=provider, catalog_sha256=CATALOG_SHA256[provider])
    spec["endpoint"] = (
        OPENROUTER_ENDPOINT
        if provider == "openrouter"
        else VERCEL_D1_ENDPOINT
        if model_id == "liquid/d1"
        else VERCEL_TYPESAFE_ENDPOINT
    )
    return spec
