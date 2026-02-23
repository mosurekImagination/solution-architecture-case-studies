#!/usr/bin/env bash
# ============================================================================
# render.sh — Generate HTML from all AsciiDoc files
# ============================================================================
#
# Prerequisites:
#   1. Node.js + npm (for npx)
#   2. npm install asciidoctor asciidoctor-kroki  (or use npx)
#   3. Docker containers running: docker-compose up -d
#
# Usage:
#   ./render.sh              # Render all .adoc files
#   ./render.sh template     # Render only template/ folder
#   ./render.sh 01           # Render only 01/ case study
#   ./render.sh --check      # Check prerequisites only
#
# ============================================================================

set -euo pipefail

# --- Colors ----------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Configuration ---------------------------------------------------------
KROKI_URL="http://localhost:8000"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/output"
OUTPUT_SUFFIX=".html"
FAILED=0
RENDERED=0
SKIPPED=0

# --- Functions -------------------------------------------------------------

log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_prerequisites() {
  local ok=true

  # Check npx
  if ! command -v npx &>/dev/null; then
    log_error "npx not found. Install Node.js: https://nodejs.org/"
    ok=false
  else
    log_ok "npx found: $(npx --version 2>/dev/null || echo 'unknown')"
  fi

  # Check Docker containers (Kroki)
  if curl -sf "${KROKI_URL}/health" &>/dev/null; then
    log_ok "Kroki server reachable at ${KROKI_URL}"
  else
    log_warn "Kroki server not reachable at ${KROKI_URL}"
    log_warn "Diagrams will fail. Start with: docker-compose up -d"
    # Don't fail — non-diagram rendering still works
  fi

  # Check asciidoctor-kroki availability
  if npx --yes asciidoctor --version &>/dev/null 2>&1; then
    log_ok "asciidoctor available via npx"
  else
    log_warn "asciidoctor not found. Will attempt: npx asciidoctor"
    log_warn "If this fails, run: npm install asciidoctor asciidoctor-kroki"
  fi

  if [ "$ok" = false ]; then
    log_error "Prerequisites check failed."
    exit 1
  fi
}

render_file() {
  local input_file="$1"
  local relative_path="${input_file#"$SCRIPT_DIR/"}"
  local relative_dir
  relative_dir="$(dirname "$relative_path")"
  local basename
  basename="$(basename "$input_file" .adoc)"

  # Mirror source directory structure inside output/
  local output_dir="${OUTPUT_DIR}/${relative_dir}"
  mkdir -p "$output_dir"
  local output_file="${output_dir}/${basename}${OUTPUT_SUFFIX}"

  log_info "Rendering: ${relative_path}"

  if npx --yes asciidoctor \
    -r asciidoctor-kroki \
    -a kroki-server-url="${KROKI_URL}" \
    -a kroki-fetch-diagram \
    -a imagesdir=diagrams \
    -a toc=left \
    -a icons=font \
    -a source-highlighter=highlight.js \
    -a sectanchors \
    -o "${output_file}" \
    "${input_file}" 2>&1; then
    log_ok "  → output/${relative_dir}/${basename}${OUTPUT_SUFFIX}"
    RENDERED=$((RENDERED + 1))
  else
    log_error "  ✗ Failed: ${relative_path}"
    FAILED=$((FAILED + 1))
  fi
}

# --- Main ------------------------------------------------------------------

cd "$SCRIPT_DIR"

# Handle --check flag
if [[ "${1:-}" == "--check" ]]; then
  log_info "Checking prerequisites..."
  check_prerequisites
  exit 0
fi

log_info "============================================"
log_info "  AsciiDoc → HTML Renderer"
log_info "============================================"
echo

# Prerequisites
check_prerequisites
echo

# Determine scope
SCOPE="${1:-}"
if [[ -n "$SCOPE" && -d "$SCOPE" ]]; then
  SEARCH_DIR="$SCRIPT_DIR/$SCOPE"
  log_info "Scope: ${SCOPE}/"
elif [[ -n "$SCOPE" && -f "$SCOPE" ]]; then
  log_info "Rendering single file: ${SCOPE}"
  render_file "$(realpath "$SCOPE")"
  echo
  log_info "Done. ${RENDERED} rendered, ${FAILED} failed."
  exit $FAILED
else
  SEARCH_DIR="$SCRIPT_DIR"
  log_info "Scope: entire workspace"
fi

echo

# Find and render all .adoc files
while IFS= read -r -d '' adoc_file; do
  render_file "$adoc_file"
done < <(find "$SEARCH_DIR" -name '*.adoc' -type f -print0 | sort -z)

# --- Summary ---------------------------------------------------------------
echo
log_info "============================================"
log_info "  Summary"
log_info "============================================"
log_ok   "Rendered: ${RENDERED}"
if [[ $FAILED -gt 0 ]]; then
  log_error "Failed:   ${FAILED}"
else
  log_ok   "Failed:   ${FAILED}"
fi
echo

if [[ $FAILED -gt 0 ]]; then
  log_warn "Some files failed to render. Check errors above."
  exit 1
fi

log_ok "All files rendered successfully! 🎉"
