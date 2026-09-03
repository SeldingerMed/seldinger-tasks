"""Task-owned structural checks for image-to-image laparoscopic models."""

from __future__ import annotations

from base64 import b64decode
from io import BytesIO
from math import log10

import numpy as np
from PIL import Image


def _array(value: str, mode: str = "RGB") -> np.ndarray:
    return np.asarray(Image.open(BytesIO(b64decode(value.split(",", 1)[-1]))).convert(mode), dtype=np.float64)


def _gradient(image: np.ndarray) -> np.ndarray:
    gx = np.diff(image, axis=1, append=image[:, -1:])
    gy = np.diff(image, axis=0, append=image[-1:, :])
    return np.hypot(gx, gy)


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    left, right = left.ravel() - left.mean(), right.ravel() - right.mean()
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denominator) if denominator else 0.0


def _ssim(left: np.ndarray, right: np.ndarray) -> float:
    c1, c2 = 6.5025, 58.5225
    covariance = ((left - left.mean()) * (right - right.mean())).mean()
    return float(((2 * left.mean() * right.mean() + c1) * (2 * covariance + c2)) /
                 ((left.mean() ** 2 + right.mean() ** 2 + c1) * (left.var() + right.var() + c2)))


class AnatomyRetentionVerifier:
    def score(self, context):
        original = _array(context["input"]["content_image"], "L")
        output_rgb = _array(context["prediction"]["stylized_image"])
        output = np.asarray(Image.fromarray(output_rgb.astype(np.uint8)).convert("L"), dtype=np.float64)
        if original.shape != output.shape or not np.isfinite(output).all():
            return self._invalid("output shape or values are invalid")
        original_gradient, output_gradient = _gradient(original), _gradient(output)
        structure = _correlation(original_gradient, output_gradient)
        mask = _array(context["label"]["instrument_mask"], "L") > 0.5
        boundary = _gradient(mask.astype(np.float64)) > 0
        boundary_retention = None
        if boundary.any():
            base = float(original_gradient[boundary].mean())
            boundary_retention = min(2.0, float(output_gradient[boundary].mean()) / max(base, 1e-9))
        ssim = _ssim(original, output)
        original_rgb = _array(context["input"]["content_image"])
        color_shift = float(np.abs(original_rgb - output_rgb).mean() / 255.0)
        identity_psnr = None
        if context["input"].get("identity_pair"):
            mse = float(np.square(original_rgb - output_rgb).mean())
            identity_psnr = 99.0 if mse == 0 else 10 * log10(255 * 255 / mse)
        failed = structure < 0.45 or ssim < 0.35 or (
            boundary_retention is not None and boundary_retention < 0.35
        )
        return {
            "gates": {"gross_structure_loss": {
                "status": "fail" if failed else "pass",
                "reason": f"edge correlation={structure:.3f}, SSIM={ssim:.3f}, instrument-boundary retention={boundary_retention}",
            }},
            "metrics": {
                "structure_correlation": structure,
                "grayscale_ssim": ssim,
                "instrument_boundary_retention": boundary_retention,
                "color_shift": color_shift,
                "identity_psnr_db": identity_psnr,
            },
        }

    @staticmethod
    def _invalid(reason):
        return {
            "gates": {"gross_structure_loss": {"status": "not_assessable", "abstained": True, "reason": reason}},
            "metrics": {key: None for key in (
                "structure_correlation", "grayscale_ssim", "instrument_boundary_retention", "color_shift", "identity_psnr_db"
            )},
        }


def load_verifier(*, root):
    del root
    return AnatomyRetentionVerifier()


if __name__ == "__main__":
    import json
    from pathlib import Path

    root = Path(__file__).parent
    inputs = json.loads((root / "inputs.json").read_text())["items"]
    labels = json.loads((root / "labels.json").read_text())["items"]
    rows = [AnatomyRetentionVerifier().score({
        "input": item,
        "label": label,
        "prediction": {"stylized_image": item["content_image"]},
    }) for item, label in zip(inputs, labels)]
    assert rows and all(row["gates"]["gross_structure_loss"]["status"] == "pass" for row in rows)
