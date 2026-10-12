# Bundled locale font sharing

Measured on Linux x86-64, CPython 3.14.7, pdfust 0.13.0 with this hardening
branch's native extension. Each fresh process retained 16 empty Documents with
the same bundled Japanese sans/serif font pair. No pages were interpreted.

| Mode | Configuration time | Process peak RSS |
| --- | ---: | ---: |
| Explicit uncached pair setter | 0.0964 s | 189.06 MiB |
| Automatic locale setter with weak sharing | 0.00554 s | 35.42 MiB |

Reproduce with `uv run python bench/font_sharing.py`.

This is a focused comparison of two paths in the same build, not a measurement
against a historical wheel or a claim about rendering throughput. Timing includes
filesystem-cache effects and one run per mode; RSS includes the interpreter and
native extension. The weak registry adds metadata checks and a serial loading
lock. Different font files, short-lived documents, and concurrent first loads
can give different results. Explicit custom font setters retain their independent
ownership semantics. The registry holds no strong global reference to font bytes.
