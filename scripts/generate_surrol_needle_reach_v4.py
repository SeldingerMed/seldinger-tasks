"""Generate the reproducibly seeded SurRoL NeedleReach pilot."""

import importlib.util
from pathlib import Path


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    source = Path(__file__).with_name("generate_surrol_needle_reach_v3.py")
    spec = importlib.util.spec_from_file_location("surrol_generator", source)
    assert spec and spec.loader
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    generator.VERSION = "4"
    generator.ROOT = repo / "datasets/seldingermed/surrol-needle-reach/4"
    generator.JOB_ROOT = repo / "jobs/seldingermed/surrol-needle-reach/4"
    generator.WORLD_PIN = "1a9f4b9ccefb214b8981871c5f562841e29f4337"
    generator.main()


if __name__ == "__main__":
    main()
