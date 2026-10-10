# Guarded JSON codec comparison

The compatibility-preserving orjson adapter was slower than stdlib in this
synthetic financial-client workload. Retain this as a negative result for this
adapter, not a claim that orjson is generally slow. No production codec or
dependency was changed.

| 23k-history / 30 attempts / zero export | Workers / slots | Wall seconds | CPU seconds | Sampled peak RSS, MB |
| --- | ---: | ---: | ---: | ---: |
| stdlib, unchanged financial methods | 3 | 32.64 | 31.82 | 338.6 |
| guarded orjson, same financial methods | 3 | 37.80 | 36.67 | 416.5 |
| stdlib, unchanged financial methods | 6 | 33.36 | 32.52 | 543.6 |
| guarded orjson, same financial methods | 6 | 42.87 | 40.88 | 617.9 |
| SQLite/WAL prototype, fewer production guarantees | 3 | 0.542 | 0.039 | 198.5 |
| SQLite/WAL prototype, fewer production guarantees | 6 | 0.322 | 0.043 | 229.6 |

The adapter changes only `hosted.json` and `decision_concurrent.json` references
inside an isolated synthetic process, restoring both on every exit. Financial
reserve/settle/unknown-reservation/annotation methods and lock/checkpoint flow
remain unchanged. Provider request serialization always uses stdlib and must
match every original compact request byte exactly. The same 50 ms fake provider,
27 positive USD 0.001 receipts and three unknown USD 0.30 reservations are used.
All index, UUID, accounting-sum, capacity and single-transmission checks pass.
These amounts are synthetic; no inference or network request occurs.

orjson 3.13.0 was fetched from primary PyPI metadata and its CPython 3.14
manylinux wheel verified against SHA-256
`58a9619d88f8818d9ab6b39d70d203789457ba13c1ed5d274f33ce9ae7e81a36`.
It is extracted only under
`/home/dan/.cache/jev-pdf-p003-codec/orjson-3.13.0`; project dependencies are
unchanged. [Release metadata](https://pypi.org/pypi/orjson/3.13.0/json).

Raw substitution is not value-compatible. Native serialization turns nonfinite
floats into null, whereas stdlib permits nonfinite tokens by default; native
integer support is bounded. [Official orjson documentation](https://github.com/ijl/orjson#float).
The adapter therefore walks the entire dump tree before each native financial
checkpoint. Nonfinite values, oversized integers, non-string keys and extended
types explicitly fall back to the original stdlib behavior. `allow_nan=False`
still raises; it never quietly emits null. Unsupported Unicode/native parsing
also falls back. Tests preserve signed zero and exact float bits, booleans,
integer types around 53/63/64-bit boundaries, arbitrary larger integers,
nonfinite values, Unicode and lone surrogates.

The decoder conservatively falls back when text contains a 19-or-more-digit
run or nonfinite marker. Quoted strings can trigger this safe false refusal;
the synthetic history's hash strings trigger it on every ledger load. This
simple treatment avoids silently converting an oversized JSON integer to a
floating value, but sacrifices native decoding benefits. Each measured arm
records 91 native checkpoint encodes, 30 unchanged request encodes, 57 native
small request/receipt decodes and 90 stdlib financial-ledger decodes. Recursive
Python dump validation and decode screening are included in measured CPU.
They erase the raw native codec advantage in this adapter.

Before timing, the complete 23k-entry synthetic fixture must round-trip with
exact stdlib values and types. Unsafe boundary cases use explicit fallbacks,
not coercion. This gate does not authenticate or inspect a real financial
ledger. It also does not imply generic drop-in compatibility for arbitrary
Python objects or cyclic containers.

```sh
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
python -m bench.p003_json_codec_perf \
  --codec-directory /home/dan/.cache/jev-pdf-p003-codec/orjson-3.13.0 \
  --output /absolute/path/fresh-codec-control
```

Five codec tests and ten existing synthetic accounting tests pass. Resource
scope matches the preceding ledger experiment: Python 3.14.7, eight visible
CPUs, one process, three/six threads, process CPU and RSS sampled every 100 ms.
Fixture setup and compatibility gating precede the measured interval. OS cache
and allocator state are not reset; results are single bounded runs under local
contention and are not hosted throughput forecasts. No live ledger, credential,
API, GPU, source reference, or production client was accessed or changed.

A future codec treatment could use a reviewed schema with cheaper native
validation or a numeric-token-aware screening implementation. This experiment
provides no evidence to deploy the current guarded adapter. The SQLite result
still warrants further research, subject to its explicitly omitted production
guarantees and independent migration/crash testing.
