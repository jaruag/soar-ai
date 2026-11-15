"""LLM-based classification of security findings."""

import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

from soar.models import Finding

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are a security triage assistant inside a SOAR pipeline.
Given a security finding, decide how it should be triaged.

Reply ONLY with a valid JSON object, no extra text, with these keys:
- "verdict": one of "critical", "review", "likely_noise"
- "reason": one short sentence explaining the verdict
- "suggested_action": one short, concrete next step

Be conservative: if something could be serious, lean towards "review"
rather than "likely_noise"."""


def _extract_json(text: str) -> dict:
    """Extract a JSON object from the model's reply, even if it's
    wrapped in markdown fences or surrounded by extra text."""
    # Remove markdown code fences if present
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[len("json"):]

    # Keep only from the first { to the last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]

    return json.loads(text.strip())


def classify(finding: Finding) -> dict:
    """Send a finding to the LLM and return its triage decision.
    Fails safe to 'review', but logs the real cause so an API/key
    problem isn't silently hidden as a parsing issue."""
    user_message = (
        f"Source: {finding.source}\n"
        f"Title: {finding.title}\n"
        f"Severity (as reported): {finding.severity.value}\n"
        f"Asset: {finding.asset}\n"
        f"Identifier: {finding.identifier}\n"
        f"Description: {finding.description}"
    )

    # 1. Call the API. A failure here (bad/missing key, network, rate limit)
    #    is a real problem we want to surface, not hide as a parsing issue.
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text.strip()
    except Exception as e:
        logger.error("LLM API call failed (check API key / network): %s", e)
        return {
            "verdict": "review",
            "reason": "The security model could not be reached; flagged for manual review.",
            "suggested_action": "Check the service configuration, then re-run.",
        }

    # 2. Parse the response. A failure here is a malformed-JSON issue.
    try:
        decision = _extract_json(text)

        # Make sure the verdict is one we expect; otherwise treat as review
        if decision.get("verdict") not in ("critical", "review", "likely_noise"):
            decision["verdict"] = "review"

        return {
            "verdict": decision["verdict"],
            "reason": decision.get("reason", "No reason provided."),
            "suggested_action": decision.get("suggested_action", "Review this finding manually."),
        }
    except Exception as e:
        logger.warning("Could not parse model response: %s", e)
        return {
            "verdict": "review",
            "reason": "The model's response could not be parsed; flagged for manual review.",
            "suggested_action": "Review this finding manually.",
        }