"""Metrics-only verifier for SurRoL NeedleReach."""

from typing import Any


class Verifier:
    def score(self, context: dict[str, Any]) -> dict[str, Any]:
        raw = context.get("info")
        info = raw if isinstance(raw, dict) else {}
        success = bool(info["is_success"]) if "is_success" in info else None
        return {"gates": {}, "metrics": {"raw_success": success}}


def load_verifier(*, root: Any = None) -> Verifier:
    del root
    return Verifier()
