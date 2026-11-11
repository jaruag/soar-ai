"""Data models for the SOAR pipeline."""

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Raw severity as reported by the source tool."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class Finding:
    """A normalised security finding, from any source.

    This is the common format every source is mapped to, so the
    rest of the pipeline (triage, classification, output) never has
    to care where the finding originally came from.
    """
    source: str                             # e.g. "trivy", "zap"
    title: str                              # Short Description
    severity: Severity                      # Normalised Severity
    description: str = ""                   # Longer Detail
    asset: str = ""                         # Affected Asset (package, host, URL...)
    identifier: str = ""                    # CVE id, rule id ...
    raw: dict = field(default_factory=dict) # original source payload

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.title} ({self.source})"