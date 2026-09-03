"""Generate the reproducibly seeded SurRoL NeedleReach pilot."""

import importlib.util
from pathlib import Path


def generate(version: str, world_pin: str) -> Path:
    repo = Path(__file__).resolve().parents[1]
    source = Path(__file__).with_name("generate_surrol_needle_reach_v3.py")
    spec = importlib.util.spec_from_file_location("surrol_generator", source)
    assert spec and spec.loader
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    generator.VERSION = version
    generator.ROOT = repo / f"datasets/seldingermed/surrol-needle-reach/{version}"
    generator.JOB_ROOT = repo / f"jobs/seldingermed/surrol-needle-reach/{version}"
    generator.WORLD_PIN = world_pin
    generator.main()
    return generator.ROOT


def main() -> None:
    generate("4", "1a9f4b9ccefb214b8981871c5f562841e29f4337")


if __name__ == "__main__":
    main()
