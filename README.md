# seldinger-tasks

Public, versioned OR-Audit task, dataset, and baseline-agent registry.

Each registry row is an exact `org/name@version` identity backed by:

- an immutable Git commit;
- a SHA-256 package tree digest;
- a relative package path;
- a port-compatible `dataset.toml`, `task.toml`, or `agent.toml` contract.

The registry preserves vector results. It does not define procedure enums, collapse safety into an overall score, contain private clinical media, or make clinical-validation claims.

## Use

```bash
or-audit datasets list
or-audit agents list
or-audit datasets pull seldingermed/lumen-nav@0 --out ./registry
or-audit run -d seldingermed/lumen-nav@0 \
  -a seldingermed/lumen-linear@0 \
  --out ./runs/lumen-linear
```

## Regenerate public baselines

With OR-Audit installed from its P4 release:

```bash
./scripts/regenerate.sh
```

This runs the public baseline packages and refreshes the committed static, vector-preserving leaderboard under `site/`. Full run bundles stay out of Git; every published row remains reproducible from its pinned packages and artifact head.

## License

Apache-2.0. Package metadata and derived public benchmark artifacts may retain narrower upstream claim and data boundaries recorded in their contracts.
