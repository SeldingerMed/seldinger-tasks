#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUNS=${OR_AUDIT_RUNS:-"$ROOT/.runs"}
REGISTRY=${OR_AUDIT_REGISTRY:-"$ROOT/registry.json"}

rm -rf "$RUNS" "$ROOT/site"
mkdir -p "$RUNS"

or-audit run \
  -d seldingermed/lumen-nav@0 \
  -a seldingermed/lumen-linear@0 \
  -n 30 \
  --registry "$REGISTRY" \
  --out "$RUNS/lumen-linear"

or-audit run \
  -d seldingermed/video-nextstep@0 \
  -a example/video-predictor@0 \
  --registry "$REGISTRY" \
  --out "$RUNS/video-nextstep"

or-audit leaderboard "$RUNS" --out "$ROOT/site"
