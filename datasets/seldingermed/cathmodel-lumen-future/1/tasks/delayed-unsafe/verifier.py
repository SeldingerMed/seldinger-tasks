"""Task-owned scoring for action-conditioned future-state predictions."""

from __future__ import annotations

THRESHOLD_MM = 0.35


class DelayedUnsafeVerifier:
    def score(self, context):
        expected = {(row["anchor"], row["horizon"]): row for row in context["label"]["rows"]}
        predicted = {(row["anchor"], row["horizon"]): row for row in context["prediction"].get("rows", [])}
        if set(predicted) != set(expected):
            return self._missing(len(expected), len(predicted))

        unsafe = hits = contacts = contact_hits = negatives = negative_hits = 0
        penetration_error = coverage = values = 0
        for key, label in expected.items():
            prediction = predicted[key]
            mean = prediction["state_mean"]
            std = prediction["state_std"]
            target = label["future_state"]
            if len(mean) != 10 or len(std) != 10 or len(target) != 10:
                return self._missing(len(expected), len(predicted))
            true_pen = target[8] * 2.5
            predicted_pen = mean[8] * 2.5
            if true_pen > THRESHOLD_MM:
                unsafe += 1
                hits += predicted_pen > THRESHOLD_MM
            contact = bool(label["contact"])
            classified = float(prediction["contact_probability"]) >= 0.5
            contacts += contact
            contact_hits += contact and classified
            negatives += not contact
            negative_hits += (not contact) and (not classified)
            penetration_error += abs(predicted_pen - true_pen)
            for actual, estimate, sigma in zip(target, mean, std):
                coverage += estimate - 1.645 * sigma <= actual <= estimate + 1.645 * sigma
                values += 1

        recall = hits / unsafe if unsafe else None
        gate_failed = recall is None or hits != unsafe
        return {
            "gates": {"missed_unsafe_future": {
                "status": "fail" if gate_failed else "pass",
                "reason": f"forecast {hits} of {unsafe} unsafe future windows above {THRESHOLD_MM} mm",
            }},
            "metrics": {
                "unsafe_penetration_recall": recall,
                "unsafe_window_count": unsafe,
                "contact_recall": contact_hits / contacts if contacts else None,
                "contact_specificity": negative_hits / negatives if negatives else None,
                "penetration_mae_mm": penetration_error / len(expected),
                "state_90pct_interval_coverage": coverage / values,
                "sample_count": len(expected),
            },
        }

    @staticmethod
    def _missing(expected, actual):
        return {
            "gates": {"missed_unsafe_future": {
                "status": "not_assessable",
                "abstained": True,
                "reason": f"prediction covered {actual} of {expected} required windows",
            }},
            "metrics": {
                "unsafe_penetration_recall": None,
                "unsafe_window_count": None,
                "contact_recall": None,
                "contact_specificity": None,
                "penetration_mae_mm": None,
                "state_90pct_interval_coverage": None,
                "sample_count": actual,
            },
        }


def load_verifier(*, root):
    del root
    return DelayedUnsafeVerifier()
