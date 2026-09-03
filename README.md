# seldinger-tasks

Public, versioned OR-Audit task, dataset, and baseline-agent registry.

Each registry row is an exact `org/name@version` identity backed by:

- an immutable Git commit;
- a SHA-256 package tree digest;
- a relative package path;
- a port-compatible `dataset.toml`, `task.toml`, or `agent.toml` contract.

The registry preserves vector results. It does not define procedure enums, collapse safety into an overall score, contain private clinical media, or make clinical-validation claims.

Current reproducible rows: [`site/leaderboard.json`](site/leaderboard.json) and
the dependency-free [`site/index.html`](site/index.html).

## Use

```bash
or-audit datasets list
or-audit agents list
or-audit datasets pull seldingermed/lumen-nav@0 --out ./registry
or-audit run -d seldingermed/lumen-nav@0 \
  -a seldingermed/lumen-linear@0 \
  --out ./runs/lumen-linear

# Exact staged Lumen v2 runs (requires surgeval >= 0.3.0a6 and Lumen)
or-audit run -c jobs/seldingermed/lumen-nav/2/integration-smoke \
  --out ./runs/lumen-v2-smoke
or-audit run -c jobs/seldingermed/lumen-nav/2/pilot \
  --out ./runs/lumen-v2-pilot
```

The pilot schedules 154 independent simulator episodes across nine anatomies.
Its branch scenes intentionally have one available seed each; configured maximum
timesteps are ceilings, not extra episodes or evidence.

## Regenerate public baselines

With OR-Audit installed from its P4 release:

```bash
./scripts/regenerate.sh
```

This runs all three public baseline packages and refreshes the committed static,
vector-preserving leaderboard under `site/`. The first AngioStress run restores
about 7 GB of content-addressed public benchmark artifacts into the OR-Audit
cache. Full run bundles stay out of Git; every published row remains reproducible
from its pinned packages and artifact head.

## License

Apache-2.0. Package metadata and derived public benchmark artifacts may retain narrower upstream claim and data boundaries recorded in their contracts.
