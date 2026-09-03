#!/usr/bin/env python3
"""Build one box-prompted item per visible EndoVis instrument instance."""

from __future__ import annotations

import base64
import json
from collections import deque
from io import BytesIO
from math import ceil
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "datasets/seldingermed/endovis-style/1/tasks/anatomy-retention"
ROOT = REPO / "datasets/seldingermed/endovis-prompted-seg/2/tasks/cross-dataset-instruments"
MIN_COMPONENT_FRACTION = 0.01


def instrument_components(encoded_mask: str) -> list[tuple[int, Image.Image]]:
    image = Image.open(BytesIO(base64.b64decode(encoded_mask))).convert("L")
    width, height = image.size
    foreground = {index for index, value in enumerate(image.getdata()) if value}
    minimum_pixels = ceil(width * height * MIN_COMPONENT_FRACTION)
    components: list[tuple[int, Image.Image]] = []
    while foreground:
        start = foreground.pop()
        component = {start}
        queue = deque([start])
        while queue:
            index = queue.popleft()
            x, y = index % width, index // width
            for nx in range(max(0, x - 1), min(width, x + 2)):
                for ny in range(max(0, y - 1), min(height, y + 2)):
                    neighbor = ny * width + nx
                    if neighbor in foreground:
                        foreground.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
        if len(component) >= minimum_pixels:
            mask = Image.new("L", image.size)
            pixels = mask.load()
            for index in component:
                pixels[index % width, index // width] = 255
            components.append((len(component), mask))
    return sorted(components, key=lambda item: item[0], reverse=True)


def encode_png(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode()


def main() -> None:
    source_inputs = json.loads((SOURCE / "inputs.json").read_text())
    source_labels = json.loads((SOURCE / "labels.json").read_text())
    labels = {item["id"]: item for item in source_labels["items"]}
    inputs, outputs = [], []
    for frame_index, item in enumerate(source_inputs["items"]):
        label = labels[item["id"]]
        components = instrument_components(label["instrument_mask"])
        if not components:
            raise ValueError(f"no instrument instance in {item['id']}")
        for component_index, (pixels, mask) in enumerate(components):
            item_id = f"endovis_prompted_seg_{frame_index:03d}_{component_index:02d}"
            box = mask.getbbox()
            assert box is not None
            inputs.append(
                {
                    "id": item_id,
                    "image": item["content_image"],
                    "box_prompt": list(box),
                    "image_id": item["content_image_id"],
                    "sequence_id": item["content_sequence_id"],
                    "component_rank": component_index,
                    "component_pixels": pixels,
                }
            )
            outputs.append({"id": item_id, "instrument_mask": encode_png(mask)})
    provenance = {
        **source_inputs["provenance"],
        "derived_from": "seldingermed/endovis-style@1",
        "prompt": "tight bounding box derived from one held-out instrument component",
        "instance_derivation": (
            "8-connected nonzero mask components at least 1% of the 224x224 frame; "
            "smaller annotation specks are excluded"
        ),
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "inputs.json").write_text(
        json.dumps({"provenance": provenance, "items": inputs}, separators=(",", ":"))
    )
    (ROOT / "labels.json").write_text(
        json.dumps({"provenance": provenance, "items": outputs}, separators=(",", ":"))
    )
    assert len(inputs) == len(outputs) == 24
    assert len({item["sequence_id"] for item in inputs}) == 9
    assert all(item["component_pixels"] >= 502 for item in inputs)


if __name__ == "__main__":
    main()
