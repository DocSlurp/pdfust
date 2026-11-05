# Releasing pdfust

Pushing a `v<version>` tag runs [`.github/workflows/release.yml`](.github/workflows/release.yml).
It builds every artifact, publishes it, and creates the GitHub release. Every registry
uses Trusted Publishing (GitHub OIDC). No long-lived registry token is stored in the
repository or in GitHub secrets.

| Registry | Package | Job | GitHub environment |
|---|---|---|---|
| PyPI | `pdfust` (wheels + sdist) | `publish` | `pypi` |
| npm | `@docslurp/pdfust` (N-API binding, `linux-x64-gnu`) | `publish-npm` | `npm` |
| crates.io | `pdfust-shim`, then `pdfust` | `publish-crates` (only when the repository variable `PUBLISH_CRATES` is `true`) | `crates-io` |
| GitHub | release with wheels, sdist, npm tarball, `sbom.spdx.json` and `SHA256SUMS` | `github-release` | none |

Locale font packages (`pdfust-fonts-*`, tags `fonts-<locale>-v*`) and the OCR model
package (`pdfust-ocr-models`, `release-ocr-models.yml`) release separately. The
`pdfust[<locale>]` and `pdfust[ocr]` extras resolve only after those packages are on
PyPI.

## One-time setup

1. **GitHub Actions.** Enable Actions for `DocSlurp/pdfust` (Settings → Actions → General).
2. **Environments.** Create the environments `pypi`, `npm` and `crates-io` (Settings →
   Environments). Restrict each to tags matching `v*` and add a required reviewer.
3. **PyPI.** On pypi.org, open Account → Publishing and add a *pending publisher*
   (the project does not exist yet):
   - PyPI project name: `pdfust`
   - Owner: `DocSlurp`
   - Repository name: `pdfust`
   - Workflow name: `release.yml`
   - Environment name: `pypi`

   Add the same publisher for each data package with its own workflow:
   `pdfust-fonts-{ar,he,hi,jp,ko,th,zh-cn,zh-tw}` with `release-fonts.yml`, and
   `pdfust-ocr-models` with `release-ocr-models.yml`. All use environment `pypi`.
4. **npm.** The package is published under the existing `@docslurp` organization. On
   npmjs.com, open the package `@docslurp/pdfust` → Settings → Trusted Publisher →
   GitHub Actions:
   - Organization or user: `DocSlurp`
   - Repository: `pdfust`
   - Workflow filename: `release.yml`
   - Environment name: `npm`

   If npmjs.com does not offer this before the package exists, publish the first
   version once by hand from an organization owner account with 2FA, add the
   trusted publisher, and then set *Publishing access* to require 2FA and disallow
   tokens. The `repository.url` in `bindings/node/package.json` must keep pointing at
   `https://github.com/DocSlurp/pdfust`.
5. **crates.io.** Trusted Publishing is configured on an existing crate, under the
   crate's Settings → Trusted Publishing → GitHub:
   - Repository owner: `DocSlurp`
   - Repository name: `pdfust`
   - Workflow filename: `release.yml`
   - Environment: `crates-io`

   `pdfust` already exists (a 0.0.1 placeholder). `pdfust-shim` needs one manual first
   publish (`cargo publish -p pdfust-shim` from `rust/`, with a short-lived, scoped
   token that you revoke afterwards) before its trusted publisher can be added. Then
   set the repository variable `PUBLISH_CRATES` to `true`.

## Publishing the `pdfust` crate (blocked)

`rust/Cargo.toml` keeps `publish = false`. The engine builds against a vendored
`hayro-interpret` 0.7.0 through `[patch.crates-io]`, and crates.io ignores patches.
`cargo publish --dry-run` packages the crate but fails verification because upstream
`hayro-interpret` lacks four methods the extractor calls: `Type3Glyph::advance_width`
(upstream since 0.8), `OutlineGlyph::base_font_name`, `OutlineGlyph::is_vertical` and
`Glyph::as_unicode_declared` (not upstream as of 0.9). To unblock it, either get those
accessors into a hayro release and upgrade, or stop depending on them. Then remove
`publish = false`, confirm `cargo publish --workspace --dry-run` from `rust/` succeeds,
and set `PUBLISH_CRATES`.

## Cutting a release

1. Set the same version in `pyproject.toml`, `rust/Cargo.toml`,
   `rust/pdfust-shim/Cargo.toml`, the `pdfust-shim` version requirement in `rust/Cargo.toml`
   and `bindings/node/package.json`; refresh `rust/Cargo.lock`,
   `bindings/node/Cargo.lock`, `bindings/node/package-lock.json` and `uv.lock`.
   The `verify` job rejects a tag that does not match all of them.
2. Move the `[Unreleased]` changelog entries under the new version.
3. Push the tag `v<version>` from `main` and approve each environment when asked.

Before tagging, the following checks run locally without credentials:

```sh
(cd bindings/node && npm pack --dry-run --ignore-scripts)
(cd rust && cargo publish -p pdfust-shim --dry-run)
bindings/node/scripts/pack.sh   # reproducible tarball via Docker, prints sha256
```
