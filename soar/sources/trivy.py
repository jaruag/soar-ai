"""Ingest Trivy JSON reports and normalise them into Findings."""

import json

from soar.models import Finding, Severity

# Map Trivy severity strings to our Severity enum.
_SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
    "UNKNOWN": Severity.UNKNOWN,
}


def load_findings(report_path: str) -> list[Finding]:
    """Read a Trivy JSON report and return a list of normalised Findings."""
    with open(report_path) as f:
        report = json.load(f)

    findings = []
    for result in report.get("Results", []):
        target = result.get("Target", "")
        for vuln in result.get("Vulnerabilities", []):
            pkg = vuln.get("PkgName", "")
            version = vuln.get("InstalledVersion", "")
            fixed = vuln.get("FixedVersion", "")

            findings.append(Finding(
                source="trivy",
                title=vuln.get("Title") or f"{vuln.get('VulnerabilityID')} in {pkg}",
                severity=_SEVERITY_MAP.get(vuln.get("Severity", "UNKNOWN"), Severity.UNKNOWN),
                description=(vuln.get("Description") or "")[:500],  # keep it short
                asset=f"{pkg} {version} ({target})",
                identifier=vuln.get("VulnerabilityID", ""),
                raw={"fixed_version": fixed},
            ))

    return findings