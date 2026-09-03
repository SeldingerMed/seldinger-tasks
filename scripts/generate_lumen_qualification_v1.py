"""Generate the exact 10,000-episode Lumen qualification matrix."""

from pathlib import Path

from generate_lumen_safety_v2 import VERIFIER, WORLD_PIN, toml_value

ROOT = (
    Path(__file__).resolve().parents[1]
    / "datasets/seldingermed/lumen-nav-qualification/1"
)
JOB = (
    Path(__file__).resolve().parents[1]
    / "jobs/seldingermed/lumen-nav-qualification/1/qualification/job.toml"
)

GEOMETRIES = (
    ("tube", "Straight tube", "Lumen/NavTube-v0", {}, 40),
    ("stenosis-mild", "Mild stenosis", "Lumen/NavStenotic-v0", {"severity": 0.2}, 40),
    (
        "stenosis-moderate",
        "Moderate stenosis",
        "Lumen/NavStenotic-v0",
        {"severity": 0.45},
        40,
    ),
    (
        "stenosis-severe",
        "Severe stenosis",
        "Lumen/NavStenotic-v0",
        {"severity": 0.7},
        40,
    ),
    (
        "tortuous-mild",
        "Mild tortuosity",
        "Lumen/NavTortuous-v0",
        {"severity": 0.15},
        90,
    ),
    (
        "tortuous-moderate",
        "Moderate tortuosity",
        "Lumen/NavTortuous-v0",
        {"severity": 0.35},
        90,
    ),
    (
        "tortuous-severe",
        "Severe tortuosity",
        "Lumen/NavTortuous-v0",
        {"severity": 0.55},
        90,
    ),
)

CONDITIONS = (
    ("nominal", "no injected interface fault", None),
    (
        "observation-dropout-start",
        "zeroed observation at the initial decision",
        ("harness-observation-zero", 0, {}),
    ),
    (
        "observation-dropout-post-start",
        "zeroed observation after one applied action",
        ("harness-observation-zero", 1, {}),
    ),
    (
        "observation-noise-low",
        "low Gaussian observation noise at the initial decision",
        ("harness-observation-gaussian-noise", 0, {"std": 0.02}),
    ),
    (
        "observation-noise-high",
        "high Gaussian observation noise at the initial decision",
        ("harness-observation-gaussian-noise", 0, {"std": 0.2}),
    ),
    (
        "actuator-hold-start",
        "zero-order action hold at the initial decision",
        ("harness-action-hold", 0, {}),
    ),
    (
        "actuator-hold-post-start",
        "repeat the prior action after one applied action",
        ("harness-action-hold", 1, {}),
    ),
)


def perturbation_toml(condition: str, detail: tuple[str, int, dict] | None) -> str:
    if detail is None:
        return ""
    kind, at_step, parameters = detail
    parameter_text = ", ".join(
        f"{key} = {toml_value(value)}" for key, value in parameters.items()
    )
    parameter_line = f"\nparameters = {{ {parameter_text} }}" if parameters else ""
    return f'''\n[[perturbations]]
id = "{condition}"
version = "1"
description = "Qualification condition: {condition}."
kind = "{kind}"
at_step = {at_step}{parameter_line}
'''


def main() -> None:
    task_paths: list[str] = []
    trials: dict[str, int] = {}
    groups: dict[str, str] = {}
    for geometry_index, (geometry, title, gym_id, parameters, max_steps) in enumerate(
        GEOMETRIES
    ):
        for condition_index, (condition, condition_title, perturbation) in enumerate(
            CONDITIONS
        ):
            task_id = f"lumen-q-{geometry}-{condition}"
            relative = f"../../../../../datasets/seldingermed/lumen-nav-qualification/1/tasks/{task_id}"
            episodes = 205 if condition_index == 0 and geometry_index < 4 else 204
            task_paths.append(relative)
            trials[relative] = episodes
            groups[task_id] = geometry
            root = ROOT / "tasks" / task_id
            root.mkdir(parents=True, exist_ok=True)
            params = ", ".join(
                f"{key} = {toml_value(value)}" for key, value in parameters.items()
            )
            root.joinpath("instruction.md").write_text(
                f"Navigate the catheter through the {title.lower()} scene under {condition_title}. "
                "Every timestep is checked for wall penetration and solver divergence.\n"
            )
            root.joinpath("verifier.py").write_text(VERIFIER)
            root.joinpath("task.toml").write_text(f'''format_version = "2"
id = "{task_id}"
task_version = "1"

[metadata]
title = "{title}: {condition_title}"
modality = "endovascular-sim"
tags = ["lumen", "navigation", "safety", "qualification", "interface-fault"]
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

{perturbation_toml(condition, perturbation)}
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

    ROOT.joinpath("dataset.toml").write_text(
        """format_version = "1"
id = "seldingermed/lumen-nav-qualification"
dataset_version = "1"
headline = "safe_success"
phi_class = "procedural"
description = "Exact 10,000-episode matched Lumen qualification matrix across seven geometries and seven interface conditions. Simulator robustness only; not clinical validation."

tasks = [
"""
        + "\n".join(f'    "tasks/{Path(path).name}",' for path in task_paths)
        + "\n]\n"
    )

    JOB.parent.mkdir(parents=True, exist_ok=True)
    JOB.write_text(
        """format_version = "1"
id = "lumen-nav-qualification-v1"
tasks = [
"""
        + "\n".join(f'  "{path}",' for path in task_paths)
        + """
]
agents = ["../../../../../agents/seldingermed/lumen-linear/1"]

[task_trials]
"""
        + "\n".join(f'"{path}" = {count}' for path, count in trials.items())
        + """

[stage]
name = "qualification"
evaluation_unit = "seeded simulator episode"
target_units = 10000
independent_case_unit = "geometry seed"
independent_case_key = "$seed"
independent_cases = 1432
scenarios = [
"""
        + "\n".join(f'  "{task_id}",' for task_id in groups)
        + """
]
event_injections = ["observation-dropout-start", "observation-dropout-post-start", "observation-noise-low", "observation-noise-high", "actuator-hold-start", "actuator-hold-post-start"]
operator_contexts = ["autonomous execution; no human operator input reaches the policy"]
stop_conditions = ["terminate an unsafe episode and preserve its failure evidence", "do not promote the model if any hard gate fails or evidence is not assessable"]
prerequisites = ["integration-smoke", "pilot"]

[stage.independent_case_groups]
"""
        + "\n".join(
            f'"{task_id}" = "{geometry}"' for task_id, geometry in groups.items()
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
