# SOAR-AI

**An LLM-powered security triage tool with a web interface.** Enter a package and version (pip or npm) and it scans the dependency with [Trivy](https://github.com/aquasecurity/trivy), normalises the findings into a common format, and uses an LLM (Anthropic Claude) to classify each one as **critical**, **review** or **likely noise**, with a reason and a suggested action.

The goal is the same as a SOAR (Security Orchestration, Automation and Response): automate the manual, repetitive work of triaging security findings so a team only spends time on what actually needs human judgement.

> Personal project built to explore security automation with LLMs. Working prototype, runs locally.

---

## What it does

```
  ┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────────┐
  │   Trivy      │ ──▶ │  Normalise    │ ──▶ │  Classify    │ ──▶ │  Prioritise  │
  │  (scanner)   │     │  to Finding   │     │  with an LLM │     │  & report    │
  └──────────────┘     └───────────────┘     └──────────────┘     └──────────────┘
   pip / npm            common format          critical /            critical first,
   (live scan)          (any source)           review / noise        shown in the UI
```

- **Two ecosystems:** scans both Python (pip) and JavaScript (npm) packages.
- **Live scanning:** runs Trivy on-demand against the exact package and version you enter.
- **LLM triage:** each finding gets a verdict (critical / review / likely noise), a reason and a suggested fix, returned as structured JSON and parsed robustly. The classifier fails safe to "review" if a response can't be parsed.
- **Web UI:** a sidebar app with a scan view and a history of past scans (stored in SQLite).
- **Tested:** API tests (pytest) and end-to-end browser tests (Playwright).

---

## Tech stack

- **Backend:** Python, FastAPI
- **Scanner:** Trivy (pip + npm)
- **LLM:** Anthropic Claude
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Storage:** SQLite (scan history)
- **Tests:** pytest (API), Playwright (end-to-end)

---

## Project structure

```
soar-ai/
├── api.py                 # FastAPI app: endpoints and serving the UI
├── soar/
│   ├── models.py          # the Finding model (common format)
│   ├── scanner.py         # run Trivy on-demand (pip / npm)
│   ├── sources/trivy.py   # parse Trivy reports into Findings
│   ├── classifier.py      # LLM classification (Claude)
│   ├── pipeline.py        # classify a batch and prioritise
│   └── storage.py         # SQLite scan history
├── static/
│   ├── index.html         # UI structure
│   ├── style.css          # styles
│   └── app.js             # frontend logic
├── tests/
│   ├── test_api.py        # API tests (pytest)
│   └── test_e2e.py        # end-to-end tests (Playwright)
└── requirements.txt
```

---

## Running it locally

**1. Install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Install Trivy** (the scanner). On macOS:

```bash
brew install trivy
```

See the [Trivy install docs](https://trivy.dev/latest/getting-started/installation/) for other systems.

**3. Set your API key** — create a `.env` file (never commit it):

```
ANTHROPIC_API_KEY=sk-ant-...
```

**4. Run the server**

```bash
uvicorn api:app --reload
```

Open **http://127.0.0.1:8000** and scan a package, e.g. `requests` `2.19.0` on pip, or `lodash` `4.17.4` on npm.

---

## Command line (optional)

`main.py` classifies an existing Trivy report from the terminal. Generate one first (the repo includes a deliberately vulnerable `vulnscan/` folder):

```bash
trivy fs --format json -o data/trivy_report.json vulnscan/
python main.py --limit 10    # or --all
```

---

## Running the tests

```bash
# Fast tests only (no live scan, no paid API calls)
pytest -m "not slow" -v

# All tests, including end-to-end (needs the server running + Playwright browsers)
playwright install chromium
pytest -v
```

---

## Notes & next steps

- Classification quality depends on the prompt and model; a human stays in the loop for anything critical.
- Not deployed publicly on purpose: live scanning calls a paid LLM API, so it runs locally with your own key.
- Possible next steps: scan a full `requirements.txt` / `package.json`, more scanner sources, and anchoring the LLM verdict against the scanner's own severity.