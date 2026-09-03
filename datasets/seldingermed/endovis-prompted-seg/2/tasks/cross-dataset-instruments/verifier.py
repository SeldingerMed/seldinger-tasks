"""Task-owned geometry and calibration checks for prompted segmentation."""

from __future__ import annotations

from base64 import b64decode
from io import BytesIO

import numpy as np
from PIL import Image


def _mask(value: str) -> np.ndarray:
    return np.asarray(Image.open(BytesIO(b64decode(value.split(",", 1)[-1]))).convert("L")) > 0


def _boundary(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1, constant_values=False)
    eroded = padded[1:-1, 1:-1].copy()
    for y, x in ((0, 1), (2, 1), (1, 0), (1, 2)):
        eroded &= padded[y : y + mask.shape[0], x : x + mask.shape[1]]
    return mask & ~eroded


def _dilate(mask: np.ndarray, radius: int = 2) -> np.ndarray:
    padded = np.pad(mask, radius, constant_values=False)
    return np.logical_or.reduce(
        [
            padded[y : y + mask.shape[0], x : x + mask.shape[1]]
            for y in range(2 * radius + 1)
            for x in range(2 * radius + 1)
        ]
    )


def _boundary_f1(truth: np.ndarray, prediction: np.ndarray) -> float:
    truth_boundary, prediction_boundary = _boundary(truth), _boundary(prediction)
    if not truth_boundary.any() or not prediction_boundary.any():
        return float(truth_boundary.any() == prediction_boundary.any())
    precision = float(
        prediction_boundary[_dilate(truth_boundary)].sum() / prediction_boundary.sum()
    )
    recall = float(truth_boundary[_dilate(prediction_boundary)].sum() / truth_boundary.sum())
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


class PromptedSegmentationVerifier:
    def score(self, context: dict) -> dict:
        truth = _mask(context["label"]["instrument_mask"])
        prediction = _mask(context["prediction"]["instrument_mask"])
        if truth.shape != prediction.shape:
            return self._invalid("predicted mask shape does not match the label")
        intersection = int(np.logical_and(truth, prediction).sum())
        union = int(np.logical_or(truth, prediction).sum())
        iou = intersection / union if union else 1.0
        dice = (
            2 * intersection / (int(truth.sum()) + int(prediction.sum()))
            if truth.any() or prediction.any()
            else 1.0
        )
        boundary_f1 = _boundary_f1(truth, prediction)
        predicted_iou = float(context["prediction"]["predicted_iou"])
        calibration_error = abs(predicted_iou - iou)
        x0, y0, x1, y1 = context["input"]["box_prompt"]
        inside = np.zeros_like(truth)
        inside[y0:y1, x0:x1] = True
        prompt_coverage = float(truth[inside].sum() / max(1, truth.sum()))
        quality_failed = iou < 0.50 or boundary_f1 < 0.50
        calibration_failed = calibration_error > 0.25
        return {
            "gates": {
                "segmentation_quality_screen": {
                    "status": "fail" if quality_failed else "pass",
                    "reason": f"IoU={iou:.3f}, Dice={dice:.3f}, boundary-F1@2px={boundary_f1:.3f}",
                },
                "predicted_iou_calibration_screen": {
                    "status": "fail" if calibration_failed else "pass",
                    "reason": (
                        f"predicted IoU={predicted_iou:.3f}, measured IoU={iou:.3f}, "
                        f"absolute error={calibration_error:.3f}"
                    ),
                },
            },
            "metrics": {
                "measured_iou": iou,
                "dice": dice,
                "boundary_f1_2px": boundary_f1,
                "predicted_iou": predicted_iou,
                "predicted_iou_absolute_error": calibration_error,
                "prompt_coverage": prompt_coverage,
            },
        }

    @staticmethod
    def _invalid(reason: str) -> dict:
        return {
            "gates": {
                gate: {"status": "not_assessable", "abstained": True, "reason": reason}
                for gate in ("segmentation_quality_screen", "predicted_iou_calibration_screen")
            },
            "metrics": dict.fromkeys(
                (
                    "measured_iou",
                    "dice",
                    "boundary_f1_2px",
                    "predicted_iou",
                    "predicted_iou_absolute_error",
                    "prompt_coverage",
                )
            ),
        }


def load_verifier(*, root: object) -> PromptedSegmentationVerifier:
    del root
    return PromptedSegmentationVerifier()


if __name__ == "__main__":
    import json
    from pathlib import Path

    root = Path(__file__).parent
    item = json.loads((root / "inputs.json").read_text())["items"][0]
    label = json.loads((root / "labels.json").read_text())["items"][0]
    result = PromptedSegmentationVerifier().score(
        {
            "input": item,
            "label": label,
            "prediction": {"instrument_mask": label["instrument_mask"], "predicted_iou": 1.0},
        }
    )
    assert all(gate["status"] == "pass" for gate in result["gates"].values())
    assert result["metrics"]["measured_iou"] == result["metrics"]["prompt_coverage"] == 1.0
