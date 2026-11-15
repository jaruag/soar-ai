// ============================================================
//  SOAR-AI frontend logic
//  - tab navigation
//  - calling the scan API
//  - rendering progress and results
//  - scan history (view saved scans)
//  - toast messages
// ============================================================

const API_URL = "/scan";
const SCAN_LIMIT = 5;

// ---- DOM references ----------------------------------------
const form = document.getElementById("scanForm");
const results = document.getElementById("results");
const scanBtn = document.getElementById("scanBtn");


// ============================================================
//  Tab navigation
// ============================================================
function setupTabs() {
    document.querySelectorAll(".nav-item").forEach((link) => {
        link.addEventListener("click", () => switchTab(link.dataset.tab));
    });
}

function switchTab(targetId) {
    document.querySelectorAll(".nav-item").forEach((link) => {
        link.classList.toggle("active", link.dataset.tab === targetId);
    });

    document.querySelectorAll(".tab").forEach((tab) => {
        tab.classList.toggle("active", tab.id === targetId);
    });

    if (targetId === "history") {
        loadHistory();
    }
}


// ============================================================
//  Progress bar
// ============================================================
function renderProgress(percent, label) {
    results.innerHTML = `
        <div class="progress">
            <div class="progress-bar" style="width:${percent}%"></div>
        </div>
        <div class="progress-label">${label} <span class="pct">${percent}%</span></div>
    `;
}


// ============================================================
//  Calling the API
// ============================================================
async function requestScan(pkg, version, ecosystem) {
    const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            package: pkg,
            version: version,
            ecosystem: ecosystem,
            limit: SCAN_LIMIT,
        }),
    });

    return response.json();
}


// ============================================================
//  Rendering results
// ============================================================
function countVerdicts(findings) {
    const counts = { critical: 0, review: 0, likely_noise: 0 };

    findings.forEach((finding) => {
        counts[finding.verdict] = (counts[finding.verdict] || 0) + 1;
    });

    return counts;
}

function renderSummary(counts) {
    return `
        <div class="summary-bar">
            <span class="pill c"><b>${counts.critical || 0}</b> critical</span>
            <span class="pill r"><b>${counts.review || 0}</b> review</span>
            <span class="pill n"><b>${counts.likely_noise || 0}</b> noise</span>
        </div>
    `;
}

function renderFinding(finding) {
    return `
        <div class="finding ${finding.verdict}">
            <span class="verdict ${finding.verdict}">${finding.verdict.replace("_", " ")}</span>
            <h3>${finding.title}</h3>
            <p><span class="label">Asset:</span> ${finding.asset}</p>
            <p><span class="label">Why:</span> ${finding.reason}</p>
            <p><span class="label">Action:</span> ${finding.action}</p>
        </div>
    `;
}

function renderResults(data) {
    if (!data.findings || data.findings.length === 0) {
        results.innerHTML = `<div class="status">${data.message || "No findings."}</div>`;
        return;
    }

    const summary = renderSummary(countVerdicts(data.findings));
    const cards = data.findings.map(renderFinding).join("");

    results.innerHTML = summary + cards;
}

function renderError() {
    results.innerHTML = `<div class="status">Error: could not reach the API.</div>`;
}


// ============================================================
//  Main scan flow
// ============================================================

// Handles the form submit: reads the fields and runs a scan
function handleScan(event) {
    event.preventDefault();

    const pkg = document.getElementById("package").value;
    const version = document.getElementById("version").value;
    const ecosystem = document.getElementById("ecosystem").value;

    // Sanity check: warn if the package looks like the wrong ecosystem
    const looksNpm = pkg.includes("/") || ["lodash", "express", "react", "axios", "moment", "chalk", "minimist"].includes(pkg.toLowerCase());
    const looksPip = ["django", "flask", "requests", "numpy", "pandas", "pyyaml", "jinja2", "urllib3"].includes(pkg.toLowerCase());

    if (ecosystem === "pip" && looksNpm) {
        showToast(`"${pkg}" looks like an npm package. Switch the selector to npm?`);
        return;
    }
    if (ecosystem === "npm" && looksPip) {
        showToast(`"${pkg}" looks like a Python package. Switch the selector to pip?`);
        return;
    }

    runScan(pkg, version, ecosystem);
}

// Runs a scan with explicit values
async function runScan(pkg, version, ecosystem) {
    scanBtn.disabled = true;
    renderProgress(15, `Scanning ${pkg}@${version} with Trivy`);

    const triageTick = setTimeout(() => {
        renderProgress(55, "Triaging findings with the LLM");
    }, 1200);

    try {
        const data = await requestScan(pkg, version, ecosystem);
        clearTimeout(triageTick);

        renderProgress(100, "Done");
        await delay(300);

        renderResults(data);
    } catch (error) {
        clearTimeout(triageTick);
        renderError();
    } finally {
        scanBtn.disabled = false;
    }
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}


// ============================================================
//  History
// ============================================================
async function loadHistory() {
    const list = document.getElementById("historyList");
    list.innerHTML = '<div class="status">Loading…</div>';

    try {
        const res = await fetch("/history");
        const data = await res.json();

        if (!data.history || data.history.length === 0) {
            list.innerHTML = '<div class="status">No scans yet.</div>';
            return;
        }

        // Render the list plus an empty slot for the selected scan's detail
        list.innerHTML = data.history.map(renderHistoryRow).join("")
                       + '<div id="historyDetail"></div>';

        document.querySelectorAll(".history-row").forEach((row) => {
            row.addEventListener("click", () => showHistoryDetail(row.dataset.id));
        });
    } catch (err) {
        list.innerHTML = '<div class="status">Could not load history.</div>';
    }
}

function renderHistoryRow(item) {
    const date = new Date(item.scanned_at).toLocaleString();
    return `
        <div class="finding history-row" data-id="${item.id}" style="cursor:pointer">
            <h3>${item.package}@${item.version} <span class="label">(${item.ecosystem})</span></h3>
            <div class="summary-bar">
                <span class="pill c"><b>${item.counts.critical || 0}</b> critical</span>
                <span class="pill r"><b>${item.counts.review || 0}</b> review</span>
                <span class="pill n"><b>${item.counts.likely_noise || 0}</b> noise</span>
            </div>
            <p class="label" style="font-size:12px">${date}</p>
        </div>
    `;
}

// Loads one saved scan and shows its full findings in the History tab
async function showHistoryDetail(scanId) {
    const detail = document.getElementById("historyDetail");
    detail.innerHTML = '<div class="status">Loading…</div>';

    try {
        const res = await fetch(`/history/${scanId}`);
        const data = await res.json();

        if (!data.findings || data.findings.length === 0) {
            detail.innerHTML = '<div class="status">No findings.</div>';
            return;
        }

        const title = `<h2 style="margin-top:24px">${data.package}@${data.version} (${data.ecosystem})</h2>`;
        detail.innerHTML = title + data.findings.map(renderFinding).join("");
        detail.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
        detail.innerHTML = '<div class="status">Could not load scan.</div>';
    }
}


// ============================================================
//  Toast (floating message)
// ============================================================
let toastTimer = null;

function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 3500);
}


// ============================================================
//  Init  (runs last, when everything above is defined)
// ============================================================
setupTabs();
form.addEventListener("submit", handleScan);