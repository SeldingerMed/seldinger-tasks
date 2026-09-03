#!/usr/bin/env python3
"""Pin a small, cross-sequence EndoVis validation pilot into the task package."""

from __future__ import annotations

import base64
import json
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


DATASET = "tyluan/Endovis2017"
DATASET_SHA = "ee7f41a60803126aee9725fb905874a316e82efc"
OFFSETS = (0, 75, 150, 225, 300, 375, 450, 525, 600, 675, 750, 825)
ROOT = Path(__file__).resolve().parents[1] / "datasets/seldingermed/endovis-style/1/tasks/anatomy-retention"


def row(offset: int) -> dict:
    query = urllib.parse.urlencode(
        {"dataset": DATASET, "config": "default", "split": "val", "offset": offset, "length": 1}
    )
    with urllib.request.urlopen(f"https://datasets-server.huggingface.co/rows?{query}") as response:
        return json.load(response)["rows"][0]["row"]


def image_data(url: str, *, mask: bool = False) -> str:
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "source.jpg"
        output = Path(directory) / "output.png"
        urllib.request.urlretrieve(url, source)
        subprocess.run(
            ["sips", "-z", "224", "224", "-s", "format", "png", str(source), "--out", str(output)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return base64.b64encode(output.read_bytes()).decode()


def main() -> None:
    rows = [row(offset) for offset in OFFSETS]
    inputs, labels = [], []
    for index, content in enumerate(rows):
        identity = index % 4 == 0
        style = content if identity else rows[(index + 5) % len(rows)]
        item_id = f"endovis_style_{index:03d}"
        inputs.append(
            {
                "id": item_id,
                "content_image": image_data(content["image"]["src"]),
                "style_image": image_data(style["image"]["src"]),
                "identity_pair": identity,
                "content_image_id": content["image_id"],
                "style_image_id": style["image_id"],
                "content_sequence_id": content["sequence_id"],
                "style_sequence_id": style["sequence_id"],
            }
        )
        labels.append(
            {
                "id": item_id,
                "instrument_mask": image_data(content["label"]["src"], mask=True),
            }
        )
    provenance = {
        "dataset": DATASET,
        "revision": DATASET_SHA,
        "split": "val",
        "row_offsets": list(OFFSETS),
        "license": "cc-by-4.0",
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "inputs.json").write_text(json.dumps({"provenance": provenance, "items": inputs}, separators=(",", ":")))
    (ROOT / "labels.json").write_text(json.dumps({"provenance": provenance, "items": labels}, separators=(",", ":")))


if __name__ == "__main__":
    main()
