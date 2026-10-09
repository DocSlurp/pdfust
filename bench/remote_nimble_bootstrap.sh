#!/usr/bin/env bash
# Coordinator-run staging only. No model load, GPU inference, or dataset-row downloads.
# Usage from repository root: bash bench/remote_nimble_bootstrap.sh /absolute/staging/nimble-v3
# Use the existing PPLX Python environment; PYTHON may select its interpreter.
set -euo pipefail
NIMBLE_PYTHON="${PYTHON:-python}"
NIMBLE_STAGE="${1:?Supply the absolute Nimble v3 staging directory}"
case "$NIMBLE_STAGE" in
  /*) ;;
  *) echo 'The staging directory must be absolute' >&2; exit 2 ;;
esac
# Preserve the tested host Torch/Transformers/FLA/kernel builds. PEFT and Decision
# Index dependencies are already present on the serving host; inspect pip check.
"$NIMBLE_PYTHON" -m pip install --no-deps 'peft==0.21.0' \
  'git+https://github.com/apolinario/decision-index.git@87d4650'
"$NIMBLE_PYTHON" - "$NIMBLE_STAGE" <<'PY'
import hashlib
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download
from bench.remote_nimble import (
    BASE_MODEL_ID, BASE_REVISION, MODEL_ID, MODEL_REVISION,
    REFERENCE_REPOSITORY, REFERENCE_REVISION, SOURCE_SHA256,
)

stage = Path(sys.argv[1])
stage.mkdir(parents=True, exist_ok=True)
# Download only model configuration/tokenizer/weights, not alternative exports.
snapshot_download(
    MODEL_ID, revision=MODEL_REVISION, local_dir=stage,
    allow_patterns=['adapter_config.json', 'adapter_model.safetensors',
                    'schema_config.json', 'README.md', 'LICENSE*'],
)
snapshot_download(
    BASE_MODEL_ID, revision=BASE_REVISION, local_dir=stage / 'base',
    allow_patterns=['*.json', '*.safetensors', 'tokenizer.model',
                    'vocab.txt', 'merges.txt', 'README.md', 'LICENSE*'],
)
# Exact publisher source allowlist: never snapshot_download the evaluation dataset.
files = {
    'code/nimble/__init__.py': hashlib.sha256(b'').hexdigest(),
    'code/nimble/evaluation/__init__.py': hashlib.sha256(b'').hexdigest(),
    **{f'code/nimble/evaluation/{name}': digest for name, digest in SOURCE_SHA256.items()},
}
for name, expected in files.items():
    downloaded = Path(hf_hub_download(
        REFERENCE_REPOSITORY, filename=name, repo_type='dataset', revision=REFERENCE_REVISION,
    ))
    if hashlib.sha256(downloaded.read_bytes()).hexdigest() != expected:
        raise ValueError(f'Publisher source hash mismatch: {name}')
    destination = stage / 'reference' / name.removeprefix('code/')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(downloaded, destination)
contract = json.loads((stage / 'schema_config.json').read_bytes())
assert contract['model'] == BASE_MODEL_ID and contract['revision'] == BASE_REVISION
assert contract['task'] == 'schema_candidate_classification_v2'
assert contract['prompt_source_sha256'] == {
    name: SOURCE_SHA256[name] for name in ('parallel_schema.py', 'extended_schema.py')
}
assert (stage / 'base' / 'model.safetensors.index.json').is_file()
assert (stage / 'adapter_model.safetensors').is_file()
packages = {}
for package in ('torch', 'transformers', 'peft', 'decision-index', 'flash-linear-attention',
                'kernels', 'causal-conv1d', 'accelerate', 'huggingface-hub', 'httpx'):
    try:
        packages[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        packages[package] = None
provenance = {
    'model': MODEL_ID, 'revision': MODEL_REVISION, 'base': BASE_MODEL_ID,
    'base_revision': BASE_REVISION, 'reference_repository': REFERENCE_REPOSITORY,
    'reference_revision': REFERENCE_REVISION, 'reference_files_sha256': files,
    'packages': packages, 'inference_performed': False,
    'causal_conv1d': 'optional Transformers fallback; bootstrap does not compile this package',
}
(stage / 'bootstrap-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print(json.dumps(provenance, indent=2))
PY
# Diagnose missing dependencies without upgrading or replacing the existing runtime.
"$NIMBLE_PYTHON" -m pip check
