"""Verify a checkpoint package's structural integrity report."""

from __future__ import annotations

from typing import Any


class CheckpointVerifier:
    def score(self, context: dict[str, Any]) -> dict[str, Any]:
        prediction = context["prediction"]
        readable = bool(prediction.get("archive_readable"))
        return {
            "gates": {
                "archive_readable": {
                    "status": "pass" if readable else "fail",
                    "reason": "checkpoint archive is readable" if readable else "checkpoint archive is not readable",
                }
            },
            "metrics": {
                "archive_readable": readable,
                "archive_members": float(prediction.get("archive_members", 0)),
                "size_bytes": float(prediction.get("size_bytes", 0)),
            },
        }


def load_verifier(*, root: Any) -> CheckpointVerifier:
    del root
    return CheckpointVerifier()
