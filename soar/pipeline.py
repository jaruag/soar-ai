"""The SOAR pipeline: classify a batch of findings and sort them."""

from soar.models import Finding
from soar.classifier import classify

# Order of importance for sorting the results.
VERDICT_ORDER = {"critical": 0, "review": 1, "likely_noise": 2}


def process(findings: list[Finding]) -> list[dict]:
    """Classify every finding and return the results, most important first."""
    results = []

    for finding in findings:
        print(f"Classifying: {finding}")
        decision = classify(finding)
        results.append({
            "finding": finding,
            "verdict": decision.get("verdict", "review"),
            "reason": decision.get("reason", ""),
            "suggested_action": decision.get("suggested_action", ""),
        })

    # Sort so critical findings come first, noise last.
    results.sort(key=lambda r: VERDICT_ORDER.get(r["verdict"], 1))
    return results