#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUNS=${OR_AUDIT_RUNS:-"$ROOT/.runs"}
REGISTRY=${OR_AUDIT_REGISTRY:-"$ROOT/registry.json"}
OR_AUDIT=${OR_AUDIT:-or-audit}

rm -rf "$RUNS" "$ROOT/site"
mkdir -p "$RUNS"

"$OR_AUDIT" run \
  -d seldingermed/lumen-nav@0 \
  -a seldingermed/lumen-linear@0 \
  -n 30 \
  --registry "$REGISTRY" \
  --out "$RUNS/lumen-linear"

"$OR_AUDIT" run \
  -d seldingermed/video-nextstep@0 \
  -a example/video-predictor@0 \
  --registry "$REGISTRY" \
  --out "$RUNS/video-nextstep"

"$OR_AUDIT" run \
  -d seldingermed/angiostress@1 \
  -a seldingermed/cath-seg@0 \
  --registry "$REGISTRY" \
  --out "$RUNS/angiostress"

"$OR_AUDIT" leaderboard "$RUNS" --out "$ROOT/site"
