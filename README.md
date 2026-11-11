# SOAR-AI

**An LLM-powered security triage tool.** It ingests findings from a vulnerability scanner, normalises them into a common format, and uses an LLM to classify each one as **critical**, **review**, or **likely noise**, with a short reason and a suggested action, then prioritises them so the important ones surface first.

The goal is the same as a SOAR (Security Orchestration, Automation and Response): take the manual, repetitive work of triaging security findings and automate it, so a security team only spends time on what actually needs human judgement.

> This is a personal project built to explore security automation with LLMs. It's a working prototype, not a production system.

---

## What it does

```
  ┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────────┐
  │   Trivy      │ ──▶ │  Normalise    │ ──▶ │  Classify    │ ──▶ │  Prioritise  │
  │  (scanner)   │     │  to Finding   │     │  with an LLM │     │  & report    │
  └──────────────┘     └───────────────┘     └──────────────┘     └──────────────┘
   real CVEs            common format          critical /            critical first,
   (JSON)               (any source)           review / noise        noise last
                                               + reason + action
```

1. **Ingest** real vulnerability findings from a [Trivy](https://github.com/aquasecurity/trivy) JSON report.
2. **Normalise** every finding into a common `Finding` format, so any source (Trivy today, others tomorrow) plugs into the same pipeline.
3. **Classify** each finding with an LLM (Anthropic Claude): `critical`, `review`, or `likely_noise`, plus a one-line reason and a concrete suggested action. The model is asked for **structured JSON output**, parsed robustly.
4. **Prioritise** the results so critical findings appear first and likely noise last, and print a summary.

---

## Example output

Run against a deliberately vulnerable `requirements.txt`:

```
Ingested 73 findings from Trivy.
Processing the first 10 ...

============================================================
  TRIAGE RESULTS (most important first)
============================================================

[CRITICAL] Django: crafted email address allows account takeover
   Asset:  django 2.2.0 (requirements.txt)
   Reason: CVE-2019-19844 is a confirmed account takeover via password reset.
   Action: Upgrade Django to 2.2.9+ and review recent password reset activity.

[REVIEW] django: potential SQL injection via StringAgg(delimiter)
   Asset:  django 2.2.0 (requirements.txt)
   Reason: Exploitation requires user-controlled input to the delimiter parameter.
   Action: Audit code using StringAgg with user-controlled delimiters, then upgrade.

============================================================
  Summary: 6 critical | 4 to review | 0 likely noise
============================================================
```

Notice the model reasons about **context**: it rates clear SQL injections as critical, but flags a context-dependent one as *review* rather than assuming the worst.

---

## Tech stack

- **Python**
- **Anthropic Claude** (LLM classification, structured outputs)
- **Trivy** (open-source vulnerability scanner, as the findings source)
- Designed to be **source-agnostic**: adding a new scanner means writing one small parser to the common `Finding` format.

---

## Project structure

```
soar-ai/
├── soar/
│   ├── models.py          # the Finding model (common format)
│   ├── classifier.py      # LLM classification (Claude)
│   ├── pipeline.py        # process a batch, classify + prioritise
│   └── sources/
│       └── trivy.py       # ingest & normalise Trivy reports
├── main.py                # entry point: ingest → classify → prioritise → report
├── data/                  # scan reports (gitignored)
└── requirements.txt
```

---

## Running it

**1. Install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Set your API key**

Create a `.env` file (never commit it):

```
ANTHROPIC_API_KEY=sk-ant-...
```

**3. Generate a scan with Trivy** (example: a vulnerable requirements file)

```bash
trivy fs --format json --output data/trivy_report.json path/to/project/
```

**4. Run the triage**

```bash
python main.py            # first 10 findings
python main.py --limit 20 # first 20
python main.py --all      # everything
```

---

## Notes & next steps

- The classification quality depends on the prompt and the model; a human stays in the loop for anything critical.
- Possible next steps: more sources (e.g. OWASP ZAP), evaluation of classification accuracy, notification of critical findings, and orchestration with a tool like n8n.