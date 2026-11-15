from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from soar.scanner import scan_package
from soar.sources.trivy import parse_report
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from soar import storage

from soar.pipeline import process

app = FastAPI(title="SOAR-AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
storage.init_db()
REPORT_PATH = "data/trivy_report.json"


class ScanRequest(BaseModel):
    package: str
    version: str
    ecosystem: str = "pip"   # "pip" or "npm"
    limit: int = 5


@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok", "service": "SOAR-AI"}

@app.post("/scan")
def scan(req: ScanRequest):
    # Run Trivy live on the requested package
    try:
        report = scan_package(req.package, req.version, req.ecosystem)
    except Exception as e:
        return {"package": req.package, "version": req.version, "findings": [], "message": f"Scan failed: {e}"}

    findings = parse_report(report)
    if not findings:
        return {"package": req.package, "version": req.version, "findings": [], "message": "No vulnerabilities found for this package and version."}

    findings = findings[: req.limit]
    results = process(findings)

    output = [{
        "verdict": r["verdict"],
        "title": r["finding"].title,
        "asset": r["finding"].asset,
        "reason": r["reason"],
        "action": r["suggested_action"],
    } for r in results]

    # Save to history
    storage.save_scan(req.ecosystem, req.package, req.version, output)

    return {
        "package": req.package,
        "version": req.version,
        "count": len(output),
        "findings": output,
    }

@app.get("/history")
def history():
    return {"history": storage.get_history()}

@app.get("/history/{scan_id}")
def history_detail(scan_id: int):
    scan = storage.get_scan_by_id(scan_id)
    if scan is None:
        return {"findings": [], "message": "Scan not found."}
    return scan