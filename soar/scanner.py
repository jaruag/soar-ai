"""Run Trivy on-demand for a given package, version and ecosystem."""

import json
import subprocess
import tempfile
from pathlib import Path


def _write_manifest(tmpdir: str, package: str, version: str, ecosystem: str) -> None:
    """Write the dependency file Trivy will scan, in the right format
    for the chosen ecosystem."""
    folder = Path(tmpdir)

    if ecosystem == "npm":
        # Trivy needs a lockfile (package-lock.json) with resolved versions,
        # not a plain package.json. We write a minimal lockfile v3.
        lockfile = {
            "name": "soar-scan",
            "version": "1.0.0",
            "lockfileVersion": 3,
            "requires": True,
            "packages": {
                "": {
                    "name": "soar-scan",
                    "version": "1.0.0",
                    "dependencies": {
                        package: version,
                    },
                },
                f"node_modules/{package}": {
                    "version": version,
                },
            },
        }
        (folder / "package-lock.json").write_text(json.dumps(lockfile, indent=2))

    else:  # default: pip
        (folder / "requirements.txt").write_text(f"{package}=={version}\n")


def scan_package(package: str, version: str, ecosystem: str = "pip") -> dict:
    """Create a temporary dependency file for the package, run Trivy on it,
    and return the parsed JSON report as a dict."""

    with tempfile.TemporaryDirectory() as tmpdir:
        _write_manifest(tmpdir, package, version, ecosystem)

        report_path = Path(tmpdir) / "report.json"

        result = subprocess.run(
            [
                "trivy", "fs",
                "--format", "json",
                "--output", str(report_path),
                "--quiet",
                str(tmpdir),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Trivy failed: {result.stderr}")

        with open(report_path) as f:
            return json.load(f)