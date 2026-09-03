"""Score every timestep; terminal-only safety is not safety evidence."""

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
