#!/usr/bin/env bash
# Fetch the official WordCraft and PdfCraft web builds into offiz_craft/static/lib/.
#
# The payloads are ~130 MB of WASM and are not committed (see .gitignore): only the
# provenance README.md of offiz_craft/static/lib/<app>/ is tracked. Run this script
# once after cloning, and again whenever a pinned version below changes, before the
# browser tests (offiz_craft/tests/test_host_page.py) or the chatter dialog run.
#
# Per build the script:
#   1. downloads the release asset unless the cache already holds it (CRAFT_WEB_CACHE,
#      default /tmp/craft-web);
#   2. verifies its SHA-256 against the pinned value, the one published in the
#      release's SHA256SUMS.txt;
#   3. unzips it into offiz_craft/static/lib/<app>/, dropping the archive's single
#      top-level directory. Nothing inside the build is rewritten (all its URLs are
#      relative), except that the build's own README.md is unpacked as
#      UPSTREAM-README.md so that it does not replace this directory's README.md.
#
# Re-running is safe: the same verified bytes are unpacked over the same paths.
#
# Usage:
#   offiz_craft/scripts/fetch_web_builds.sh
#   CRAFT_WEB_CACHE=/path/to/cache offiz_craft/scripts/fetch_web_builds.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LIB_DIR="$ROOT/offiz_craft/static/lib"
CACHE_DIR="${CRAFT_WEB_CACHE:-/tmp/craft-web}"

# app | version | release asset | SHA-256 of the asset (releases/download/v<version>/SHA256SUMS.txt)
BUILDS=(
  "wordcraft|0.18.1|wordcraft-web-0.18.1.zip|3daa7c2d1f209a7eeb2527fcefa3fe31e875848fb1970d68f54edae55fe0bc9f"
  "pdfcraft|0.22.0|pdfcraft-web-0.22.0.zip|5da6db0d6d0d5ae517e9bb62c39eb57285f8befd81ef6555e9a807ccf5da5954"
  "gridcraft|0.19.1|gridcraft-web-0.19.1.zip|48c5d1b101befebb3c5ba3b7a14914f01c3207934813ed07dc4251b7ae116a78"
  "deckcraft|0.18.1|deckcraft-web-0.18.1.zip|3196e537fcfab538aaa2e88584bc74e29bb584459b916ab584ac22fbafe32db5"
)

log() { printf '==> %s\n' "$*"; }

verify() {  # verify <zip> <sha256>
  local actual
  actual="$(shasum -a 256 "$1" | awk '{print $1}')"
  if [ "$actual" != "$2" ]; then
    printf 'SHA-256 mismatch for %s\n  expected %s\n  actual   %s\n' "$1" "$2" "$actual" >&2
    return 1
  fi
  log "sha256 OK  $2  $(basename "$1")"
}

fetch() {  # fetch <url> <zip> <sha256>
  local url="$1" zip="$2" sha256="$3"
  if [ -f "$zip" ] && verify "$zip" "$sha256"; then
    log "from cache: $zip"
  else
    log "download: $url"
    curl --fail --location --retry 3 --output "$zip.part" "$url"
    verify "$zip.part" "$sha256"
    mv "$zip.part" "$zip"
  fi
}

mkdir -p "$LIB_DIR" "$CACHE_DIR"

# The archive is unpacked into a staging directory inside the tree (nothing is written
# elsewhere) and copied over the target; the staging directory is removed on exit.
STAGING="$(mktemp -d "$LIB_DIR/.unpack.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT

for build in "${BUILDS[@]}"; do
  IFS='|' read -r app version asset sha256 <<<"$build"
  name="${asset%.zip}"
  url="https://github.com/storytold/$app/releases/download/v$version/$asset"
  target="$LIB_DIR/$app"

  log "$app $version"
  fetch "$url" "$CACHE_DIR/$asset" "$sha256"

  unzip -q "$CACHE_DIR/$asset" -d "$STAGING"
  payload="$STAGING/$name"
  # Keep the build's own README.md without letting it shadow our provenance README.md.
  mv "$payload/README.md" "$payload/UPSTREAM-README.md"

  mkdir -p "$target"
  cp -R "$payload/." "$target/"

  for required in index.html LICENSE-MIT LICENSE-APACHE NOTICE; do
    if [ ! -f "$target/$required" ]; then
      printf 'missing %s after unpacking %s\n' "$target/$required" "$asset" >&2
      exit 1
    fi
  done
  log "unpacked into ${target#"$ROOT"/}: $(find "$target" -type f | wc -l | tr -d ' ') files, $(du -sh "$target" | cut -f1)"
done
