"""Generate the matched 120-episode SurRoL NeedleReach pilot."""

from pathlib import Path

ROOT = (
    Path(__file__).resolve().parents[1] / "datasets/seldingermed/surrol-needle-reach/1"
)
JOB_ROOT = (
    Path(__file__).resolve().parents[1] / "jobs/seldingermed/surrol-needle-reach/1"
)
WORLD_PIN = "68a60bd1e399c819c0241d0fbd1f201b129ec4b1"
ADAPTER_DIGEST = "62ac03c711b3d4b6123d4dc72a2984428ddaa10e52d33dc5075b3ca782724e74"

CONDITIONS = (
    ("nominal", "no injected interface fault", None),
    (
        "observation-dropout-start",
        "zeroed goal observation at the initial decision",
        ("harness-observation-zero", {}),
    ),
    (
        "observation-noise-high",
        "Gaussian noise with standard deviation 0.2 at the initial decision",
        ("harness-observation-gaussian-noise", {"std": 0.2}),
    ),
    (
        "actuator-hold-start",
        "zero-order action hold at the initial decision",
        ("harness-action-hold", {}),
    ),
)

VERIFIER = '''"""Metrics-only verifier for SurRoL NeedleReach."""

from typing import Any


class Verifier:
    def score(self, context: dict[str, Any]) -> dict[str, Any]:
        raw = context.get("info")
        info = raw if isinstance(raw, dict) else {}
        success = bool(info["is_success"]) if "is_success" in info else None
        return {"gates": {}, "metrics": {"raw_success": success}}


def load_verifier(*, root: Any = None) -> Verifier:
    del root
    return Verifier()
'''


def perturbation_toml(condition: str, detail: tuple[str, dict] | None) -> str:
    if detail is None:
        return ""
    kind, parameters = detail
    params = ", ".join(f"{key} = {value}" for key, value in parameters.items())
    parameter_line = f"\nparameters = {{ {params} }}" if parameters else ""
    return f'''\n[[perturbations]]
id = "{condition}"
version = "1"
description = "Matched pilot condition: {condition}."
kind = "{kind}"
at_step = 0{parameter_line}
'''


def task_toml(
    task_id: str, title: str, condition: str, detail: tuple[str, dict] | None
) -> str:
    return f'''format_version = "2"
id = "{task_id}"
task_version = "1"

[metadata]
title = "SurRoL NeedleReach: {title}"
modality = "robotic-kinematics"
tags = ["surrol", "needle-reach", "pybullet", "metrics-only", "interface-fault"]
safety_critical = false

[subject]
kind = "policy"

[phi]
class = "procedural"

[environment]
kind = "pybullet"
gym_id = "legacy:surrol.gym:NeedleReach-v0"
world_pin = "{WORLD_PIN}"
adapter = "or_audit.eval.sim.gym_bridge:make_gym_bridge"
adapter_digest = "{ADAPTER_DIGEST}"
parameters = {{ }}
n_eval_episodes = 30
seed_policy = "matched-seeds-0-through-29"
metrics_only = true

[environment.capabilities]
physics = true
closed_loop = true
counterfactual = false
requires_gym_id = true
requires_world_pin = true
requires_contract = false
determinism_class = "unmeasured"
{perturbation_toml(condition, detail)}
[interface]
id = "gym-policy"
interaction_mode = "closed-loop"
protocol_version = "1"
observations = ["surrol-goal-observation"]
actions = ["surrol-psm-delta5"]

[harness]
interaction_mode = "closed-loop"
protocol_version = "1"
max_steps = 50

[agent]
kinds = ["policy", "random"]
action_space = "surrol-psm-delta5"
timeout_sec = 120.0

[oracle]
kind = "physics"

[verifier]
abstain_ok = true
headline = "raw_success"
entrypoint = "verifier.py:load_verifier"

[[verifier.metrics]]
id = "raw_success"
kind = "boolean"
direction = "maximize"
source = "surrol.info.is_success"

[attestation]
level = "none"

[decision]
emit_human_determination = false
'''


def main() -> None:
    task_ids: list[str] = []
    for condition, title, detail in CONDITIONS:
        task_id = f"surrol-needle-reach-{condition}"
        task_ids.append(task_id)
        root = ROOT / "tasks" / task_id
        root.mkdir(parents=True, exist_ok=True)
        root.joinpath("instruction.md").write_text(
            f"Run the NeedleReach policy under {title}. Report task success only; "
            "SurRoL exposes no force or tissue-safety signal.\n"
        )
        root.joinpath("task.toml").write_text(
            task_toml(task_id, title, condition, detail)
        )
        root.joinpath("verifier.py").write_text(VERIFIER)

    ROOT.joinpath("dataset.toml").write_text(
        """format_version = "1"
id = "seldingermed/surrol-needle-reach"
dataset_version = "1"
headline = "raw_success"
phi_class = "procedural"
description = "Matched SurRoL NeedleReach task-performance pilot. Metrics-only simulator evidence; not physical or clinical safety evidence."

tasks = [
"""
        + "\n".join(f'    "tasks/{task_id}",' for task_id in task_ids)
        + "\n]\n"
    )

    relative = "../../../../../datasets/seldingermed/surrol-needle-reach/1/tasks"
    smoke = JOB_ROOT / "integration-smoke/job.toml"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text(f'''format_version = "1"
id = "surrol-needle-reach-v1-integration-smoke"
tasks = ["{relative}/surrol-needle-reach-nominal"]
agents = ["../../../../../agents/seldingermed/surrol-needle-reach-oracle/1"]

[task_trials]
"{relative}/surrol-needle-reach-nominal" = 1

[stage]
name = "integration-smoke"
evaluation_unit = "seeded simulator episode"
target_units = 1
independent_case_unit = "simulator seed"
independent_case_key = "$seed"
independent_cases = 1
scenarios = ["surrol-needle-reach-nominal"]
operator_contexts = ["autonomous execution"]
stop_conditions = ["stop on interface, provenance, non-finite output, or unassessable success"]
prerequisites = []
''')

    pilot = JOB_ROOT / "pilot/job.toml"
    pilot.parent.mkdir(parents=True, exist_ok=True)
    pilot.write_text(
        """format_version = "1"
id = "surrol-needle-reach-v1-pilot"
tasks = [
"""
        + "\n".join(f'  "{relative}/{task_id}",' for task_id in task_ids)
        + """
]
agents = ["../../../../../agents/seldingermed/surrol-needle-reach-oracle/1"]

[task_trials]
"""
        + "\n".join(f'"{relative}/{task_id}" = 30' for task_id in task_ids)
        + """

[stage]
name = "pilot"
evaluation_unit = "seeded simulator episode"
target_units = 120
independent_case_unit = "matched simulator seed"
independent_case_key = "$seed"
independent_cases = 30
scenarios = ["surrol-needle-reach-nominal", "surrol-needle-reach-observation-dropout-start", "surrol-needle-reach-observation-noise-high", "surrol-needle-reach-actuator-hold-start"]
event_injections = ["observation-dropout-start", "observation-noise-high", "actuator-hold-start"]
operator_contexts = ["autonomous execution"]
stop_conditions = ["stop if success is unassessable", "do not make force, tissue-safety, hardware, or clinical claims"]
prerequisites = ["integration-smoke"]

[stage.independent_case_groups]
"""
        + "\n".join(f'"{task_id}" = "needle-reach"' for task_id in task_ids)
        + "\n"
    )


if __name__ == "__main__":
    main()
