"""SOAR-AI: ingest security findings, classify them with an LLM, prioritise.

Usage:
    python main.py                # process first 10 findings
    python main.py --limit 20     # process first 20
    python main.py --all          # process everything (slower, costs more)
"""

import argparse

from soar.sources.trivy import load_findings
from soar.pipeline import process

REPORT_PATH = "data/trivy_report.json"


def main():
    parser = argparse.ArgumentParser(description="SOAR-AI triage pipeline")
    parser.add_argument("--limit", type=int, default=10,
                        help="How many findings to process (default: 10)")
    parser.add_argument("--all", action="store_true",
                        help="Process all findings (overrides --limit)")
    args = parser.parse_args()

    findings = load_findings(REPORT_PATH)
    print(f"Ingested {len(findings)} findings from Trivy.\n")

    if not args.all:
        findings = findings[:args.limit]
        print(f"Processing the first {len(findings)} (use --all for everything).\n")

    results = process(findings)

    print("\n" + "=" * 60)
    print("  TRIAGE RESULTS (most important first)")
    print("=" * 60 + "\n")

    counts = {"critical": 0, "review": 0, "likely_noise": 0}
    for r in results:
        verdict = r["verdict"]
        counts[verdict] = counts.get(verdict, 0) + 1
        print(f"[{verdict.upper()}] {r['finding'].title}")
        print(f"   Asset:  {r['finding'].asset}")
        print(f"   Reason: {r['reason']}")
        print(f"   Action: {r['suggested_action']}\n")

    print("=" * 60)
    print(f"  Summary: {counts.get('critical',0)} critical | "
          f"{counts.get('review',0)} to review | "
          f"{counts.get('likely_noise',0)} likely noise")
    print("=" * 60)


if __name__ == "__main__":
    main()