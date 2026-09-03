"""Generate the licensed, reproducibly seeded SurRoL NeedleReach pilot."""

import runpy
from pathlib import Path


def main() -> None:
    generator = runpy.run_path(str(Path(__file__).with_name("generate_surrol_needle_reach_v4.py")))
    root = generator["generate"]("5", "1a9f4b9ccefb214b8981871c5f562841e29f4337")
    for task in root.joinpath("tasks").iterdir():
        task.joinpath("license.toml").write_text('spdx = "MIT"\n')


if __name__ == "__main__":
    main()
