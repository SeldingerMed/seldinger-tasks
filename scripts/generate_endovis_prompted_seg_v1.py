#!/usr/bin/env python3
"""Build the prompted-segmentation pilot from the pinned EndoVis task data."""

from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "datasets/seldingermed/endovis-style/1/tasks/anatomy-retention"
ROOT = REPO / "datasets/seldingermed/endovis-prompted-seg/1/tasks/cross-dataset-instruments"


def bounding_box(mask: str) -> list[int]:
    image = Image.open(BytesIO(base64.b64decode(mask))).convert("L")
    box = image.point(lambda value: 255 if value else 0).getbbox()
    if box is None:
        raise ValueError("instrument mask is empty")
    return list(box)


def main() -> None:
    source_inputs = json.loads((SOURCE / "inputs.json").read_text())
    source_labels = json.loads((SOURCE / "labels.json").read_text())
    labels = {item["id"]: item for item in source_labels["items"]}
    inputs, outputs = [], []
    for index, item in enumerate(source_inputs["items"]):
        label = labels[item["id"]]
        item_id = f"endovis_prompted_seg_{index:03d}"
        inputs.append(
            {
                "id": item_id,
                "image": item["content_image"],
                "box_prompt": bounding_box(label["instrument_mask"]),
                "image_id": item["content_image_id"],
                "sequence_id": item["content_sequence_id"],
            }
        )
        outputs.append({"id": item_id, "instrument_mask": label["instrument_mask"]})
    provenance = {
        **source_inputs["provenance"],
        "derived_from": "seldingermed/endovis-style@1",
        "prompt": "tight bounding box derived from the held-out ground-truth instrument mask",
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "inputs.json").write_text(
        json.dumps({"provenance": provenance, "items": inputs}, separators=(",", ":"))
    )
    (ROOT / "labels.json").write_text(
        json.dumps({"provenance": provenance, "items": outputs}, separators=(",", ":"))
    )
    assert len(inputs) == 12
    assert len({item["sequence_id"] for item in inputs}) == 9


if __name__ == "__main__":
    main()
