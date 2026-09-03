"""Pinned scripted NeedleReach reference policy derived from SurRoL's public oracle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


class NeedleReachOracle:
    def __init__(self, weights_path: Path) -> None:
        config = json.loads(weights_path.read_text(encoding="utf-8"))
        self.deadband = float(config["deadband"])
        self.gain = float(config["gain"])
        self.position_scale = float(config["position_scale"])

    def reset(self, *, seed: int) -> None:
        del seed

    def act(self, observation: Any, *, step: int) -> np.ndarray:
        del step
        delta = (
            np.asarray(observation["desired_goal"], dtype=float)
            - np.asarray(observation["achieved_goal"], dtype=float)
        ) / self.position_scale
        if np.linalg.norm(delta) < self.deadband:
            delta.fill(0.0)
        peak = np.abs(delta).max()
        if peak > 1.0:
            delta /= peak
        return np.array([*(delta * self.gain), 0.0, 0.0])


def load_policy(*, root: Path, weights_path: Path) -> NeedleReachOracle:
    del root
    return NeedleReachOracle(weights_path)
