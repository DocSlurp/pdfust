#!/usr/bin/env bash
# Build the private @pdfust/node tarball reproducibly from committed sources and print
# its sha256. Never publishes: the package is `private` and this script only calls `npm pack`.
#
#   bindings/node/scripts/pack.sh [output-dir]      (default: bindings/node/dist)
#
# Needs docker (BuildKit) and npm. The addon is compiled inside node:22-trixie so its
# glibc requirement matches worker/Dockerfile.lean; sources come from `git archive HEAD`,
# so uncommitted edits are not packed.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd "$here/../.." && pwd)"
out="${1:-$here/dist}"
mkdir -p "$out"
out="$(cd "$out" && pwd)"

sha="$(git -C "$repo" rev-parse HEAD)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

git -C "$repo" archive --format=tar HEAD rust bindings/node LICENSE > "$work/context.tar"
DOCKER_BUILDKIT=1 docker build \
  --build-arg "PDFUST_GIT_SHA=$sha" \
  --target artifact \
  --output "type=local,dest=$work/artifact" \
  -f bindings/node/docker/Dockerfile - < "$work/context.tar"

# Assemble the package from the committed JS/TS plus the freshly built binary.
pkg="$work/package-src"
mkdir -p "$pkg"
tar -xf "$work/context.tar" -C "$work" bindings/node
cp -r "$work/bindings/node/." "$pkg/"
rm -rf "$pkg/target" "$pkg/node_modules" "$pkg/docker" "$pkg/scripts" "$pkg/test" "$pkg/dist"
cp "$work/artifact/pdfust-node.linux-x64-gnu.node" "$work/artifact/native.js" "$work/artifact/native.d.ts" "$pkg/"
cp "$repo/LICENSE" "$pkg/LICENSE"

# Pin source timestamps so repeated packs of one commit hash identically.
find "$pkg" -exec touch -d "@$(git -C "$repo" log -1 --format=%ct)" {} +
(cd "$pkg" && npm pack --pack-destination "$out" --ignore-scripts --silent >/dev/null)

tarball="$(ls -t "$out"/*.tgz | head -1)"
echo "commit:    $sha"
echo "glibc max: $(cat "$work/artifact/glibc-max.txt")"
echo "tarball:   $tarball"
echo "sha256:    $(sha256sum "$tarball" | cut -d' ' -f1)"
