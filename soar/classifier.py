"""LLM-based classification of security findings."""

import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

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
    """Send a finding to the LLM and return its triage decision."""
    user_message = (
        f"Source: {finding.source}\n"
        f"Title: {finding.title}\n"
        f"Severity (as reported): {finding.severity.value}\n"
        f"Asset: {finding.asset}\n"
        f"Identifier: {finding.identifier}\n"
        f"Description: {finding.description}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()
    return _extract_json(text)