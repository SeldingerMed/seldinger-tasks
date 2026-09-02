"""Generate the public Lumen safety matrix from its reviewed scene table."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "datasets/seldingermed/lumen-nav/2"
WORLD_PIN = "3c6bb39ecc916c73e81131b94353ad8deee62bd4"

SCENES = (
    ("tube", "Straight tube", "Lumen/NavTube-v0", {}, 30, 40),
    ("stenosis-mild", "Mild stenosis", "Lumen/NavStenotic-v0", {"severity": 0.2}, 30, 40),
    ("stenosis-severe", "Severe stenosis", "Lumen/NavStenotic-v0", {"severity": 0.7}, 30, 40),
    ("tortuous-mild", "Mild tortuosity", "Lumen/NavTortuous-v0", {"severity": 0.15}, 30, 90),
    ("tortuous-severe", "Severe tortuosity", "Lumen/NavTortuous-v0", {"severity": 0.55}, 30, 90),
    ("branch-left", "Left branch", "Lumen/NavTreeBranch-v0", {"target_node": "left_out", "angle_deg": 60.0}, 1, 90),
    ("branch-right", "Right branch", "Lumen/NavTreeBranch-v0", {"target_node": "right_out", "angle_deg": 60.0}, 1, 90),
    ("tortuous-tree-left", "Tortuous tree left branch", "Lumen/NavTortuousTree-v0", {"target_node": "left_out"}, 1, 90),
    ("tortuous-tree-right", "Tortuous tree right branch", "Lumen/NavTortuousTree-v0", {"target_node": "right_out"}, 1, 90),
)

VERIFIER = '''"""Score every timestep; terminal-only safety is not safety evidence."""

from math import isfinite


class LumenTrajectoryVerifier:
    def score(self, context):
        trajectory = context.get("trajectory")
        limit = context.get("safety_max_pen")
        if not isinstance(trajectory, list) or not trajectory or isinstance(limit, bool):
            return self._unassessable("missing trajectory or safety limit")
        try:
            limit = float(limit)
            infos = [step["info"] for step in trajectory]
            penetrations = [float(info["max_pen"]) for info in infos]
        except (KeyError, TypeError, ValueError):
            return self._unassessable("a timestep has no numeric max_pen")
        if not isfinite(limit) or not all(isfinite(value) for value in penetrations):
            return self._unassessable("non-finite penetration evidence")
        diverged = any(bool(info.get("diverged", False)) for info in infos)
        unsafe_steps = sum(bool(info.get("unsafe", False)) or value > limit for info, value in zip(infos, penetrations))
        off_route = any(bool(info.get("off_route", False)) for info in infos)
        raw_success = any(bool(info.get("success", False)) for info in infos)
        max_pen = max(penetrations)
        failed = diverged or unsafe_steps > 0
        return {
            "gates": {"trajectory_wall_safety": {
                "status": "fail" if failed else "pass",
                "reason": f"worst max_pen={max_pen}; limit={limit}; unsafe_steps={unsafe_steps}; diverged={diverged}",
            }},
            "metrics": {
                "raw_success": raw_success,
                "safe_success": raw_success and not failed,
                "diverged": diverged,
                "off_route": off_route,
                "max_pen": max_pen,
                "unsafe_steps": unsafe_steps,
                "steps": len(trajectory),
            },
        }

    @staticmethod
    def _unassessable(reason):
        return {
            "gates": {"trajectory_wall_safety": {"status": "not_assessable", "reason": reason, "abstained": True}},
            "metrics": {"raw_success": False, "safe_success": False, "diverged": True, "off_route": False, "max_pen": None, "unsafe_steps": None, "steps": None},
        }


def load_verifier(*, root):
    del root
    return LumenTrajectoryVerifier()
'''


def toml_value(value):
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def main():
    task_paths = []
    for slug, title, gym_id, parameters, episodes, max_steps in SCENES:
        task_id = f"lumen-{slug}"
        task_paths.append(f'    "tasks/{task_id}",')
        root = ROOT / "tasks" / task_id
        root.mkdir(parents=True, exist_ok=True)
        params = ", ".join(f"{key} = {toml_value(value)}" for key, value in parameters.items())
        root.joinpath("instruction.md").write_text(
            f"Navigate the catheter through the {title.lower()} scene. Every timestep is checked for wall penetration and solver divergence.\n"
        )
        root.joinpath("verifier.py").write_text(VERIFIER)
        root.joinpath("task.toml").write_text(f'''format_version = "2"
id = "{task_id}"
task_version = "2"

[metadata]
title = "{title}: trajectory-wide wall safety"
modality = "endovascular-sim"
tags = ["lumen", "navigation", "safety", "robustness"]
safety_critical = true

[subject]
kind = "policy"

[phi]
class = "procedural"

[environment]
kind = "lumen-gym"
gym_id = "{gym_id}"
world_pin = "{WORLD_PIN}"
parameters = {{ {params} }}
n_eval_episodes = {episodes}
seed_policy = "deterministic-seeds-0-through-{episodes - 1}"

[interface]
id = "gym-policy"
interaction_mode = "closed-loop"
protocol_version = "1"
observations = ["gym-obs"]
actions = ["insertion_twist"]

[harness]
interaction_mode = "closed-loop"
protocol_version = "1"
max_steps = {max_steps}

[agent]
kinds = ["policy", "random"]
action_space = "insertion_twist"
timeout_sec = 120.0

[oracle]
kind = "physics"

[verifier]
abstain_ok = false
headline = "safe_success"
entrypoint = "verifier.py:load_verifier"

[[verifier.gates]]
id = "trajectory_wall_safety"
inputs = {{ trajectory = "trajectory", safety_max_pen = "safety_max_pen" }}
maps_to = "unsafe"
realization = "temporal"
provenance = "Pinned Lumen physics info at every recorded timestep; verifier uses the maximum penetration and any divergence/unsafe flag."
abstain_ok = false

[[verifier.metrics]]
id = "raw_success"
kind = "boolean"
direction = "maximize"
source = "lumen.trajectory.success"

[[verifier.metrics]]
id = "safe_success"
kind = "boolean"
direction = "maximize"
source = "lumen.trajectory.safe_success"

[[verifier.metrics]]
id = "diverged"
kind = "boolean"
direction = "minimize"
source = "lumen.trajectory.diverged"

[[verifier.metrics]]
id = "off_route"
kind = "boolean"
direction = "minimize"
source = "lumen.trajectory.off_route"

[[verifier.metrics]]
id = "max_pen"
kind = "continuous"
unit = "mm"
direction = "minimize"
source = "lumen.trajectory.max_pen"

[[verifier.metrics]]
id = "unsafe_steps"
kind = "continuous"
unit = "steps"
direction = "minimize"
source = "lumen.trajectory.unsafe_steps"

[[verifier.metrics]]
id = "steps"
kind = "continuous"
unit = "steps"
direction = "minimize"
source = "lumen.trajectory.steps"

[attestation]
level = "none"

[decision]
emit_human_determination = false
''')
    ROOT.joinpath("dataset.toml").write_text('''format_version = "1"
id = "seldingermed/lumen-nav"
dataset_version = "2"
headline = "safe_success"
phi_class = "procedural"
description = "Simulator robustness matrix across tube, stenosis, tortuosity, bilateral branch, and tortuous-tree scenes. It is not clinical validation."

tasks = [
''' + "\n".join(task_paths) + "\n]\n")


if __name__ == "__main__":
    main()
