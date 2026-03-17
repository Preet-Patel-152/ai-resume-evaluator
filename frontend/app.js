// Circle circumference for the SVG score gauge (radius = 54px)
// Used to calculate how much of the arc to draw based on the score (0–100)
const CIRCUMFERENCE = 2 * Math.PI * 54; // → 339.3px
const API_URL = "/grade_resume_pdf/";

const form        = document.getElementById("analyze-form");
const resumeInput = document.getElementById("resume");
const fileNameEl  = document.getElementById("file-name");
const btn         = document.getElementById("submit-btn");
const statusEl    = document.getElementById("status");
const copyBtn     = document.getElementById("copy-btn");

let lastData = null;

// Update the visible filename label when the user picks a file
resumeInput.addEventListener("change", () => {
    fileNameEl.textContent = resumeInput.files?.[0]?.name || "No file selected.";
});

// Returns a color hex based on score: green (≥70), yellow (≥40), red (<40)
function scoreColor(score) {
    if (score >= 70) return "#10b981";
    if (score >= 40) return "#f59e0b";
    return "#ef4444";
}

// Returns a human-readable label for the score range
function scoreVerdict(score) {
    if (score >= 80) return "Strong Match";
    if (score >= 60) return "Good Match";
    if (score >= 40) return "Moderate Match";
    return "Weak Match";
}

// Animates the circular score gauge from 0 up to the target score.
// strokeDashoffset controls how much of the SVG arc is visible:
//   offset = 0        → full circle drawn
//   offset = CIRCUMFERENCE → nothing drawn
// We decrease it incrementally on a 16ms interval (~60fps) for a smooth fill effect.
function animateGauge(score) {
    const arc   = document.getElementById("gauge-arc");
    const pctEl = document.getElementById("gauge-pct");
    const color = scoreColor(score);

    arc.style.stroke = color;
    document.getElementById("score-verdict").style.color = color;

    let current = 0;
    const step  = score / 45; // number of steps to reach full score in ~45 frames
    const timer = setInterval(() => {
        current = Math.min(current + step, score);
        arc.style.strokeDashoffset = CIRCUMFERENCE * (1 - current / 100);
        pctEl.textContent = Math.round(current) + "%";
        pctEl.style.color = color;
        if (current >= score) clearInterval(timer); // stop the loop once done
    }, 16);
}

// ---- Render helpers ----
function renderList(id, items) {
    document.getElementById(id).innerHTML =
        items.map(item => `<li>${item}</li>`).join("");
}

function renderChips(id, items, cls) {
    const el = document.getElementById(id);
    if (!items || items.length === 0) {
        el.innerHTML = `<span class="chip-empty">None detected</span>`;
        return;
    }
    el.innerHTML = items.map(s => `<span class="chip ${cls}">${s}</span>`).join("");
}

// ---- Copy to clipboard ----
copyBtn.addEventListener("click", () => {
    if (!lastData) return;
    const e = lastData.evaluation;
    const k = lastData.keyword_score;
    const lines = [
        "AI Resume Match Analysis",
        "=".repeat(26),
        "",
        `Match Score: ${e.match_score}% — ${scoreVerdict(e.match_score)}`,
        `Summary: ${e.summary}`,
        "",
        `Matched Skills: ${k.matched_skills.join(", ") || "none"}`,
        `Missing Skills: ${k.missing_skills.join(", ") || "none"}`,
        "",
        "Strengths:",
        ...e.strengths.map(s => `  • ${s}`),
        "",
        "Gaps:",
        ...e.gaps.map(g => `  • ${g}`),
        "",
        "Improvements:",
        ...e.improvements.map(i => `  • ${i}`),
    ];
    navigator.clipboard.writeText(lines.join("\n")).then(() => {
        copyBtn.textContent = "Copied!";
        setTimeout(() => copyBtn.textContent = "Copy Results", 2000);
    });
});

// ---- UI state helpers ----
function setLoading(loading) {
    btn.disabled    = loading;
    btn.textContent = loading ? "Analyzing…" : "Analyze Resume";
    statusEl.textContent = loading ? "Working…" : "";
    statusEl.className   = "status";

    document.getElementById("results-section").style.display = "block";
    document.getElementById("skeleton").style.display        = loading ? "block" : "none";
    document.getElementById("actual-results").style.display  = loading ? "none"  : "block";
}

function renderResults(data) {
    lastData = data;
    const ev = data.evaluation;
    const ks = data.keyword_score;

    animateGauge(ev.match_score);
    document.getElementById("score-verdict").textContent = scoreVerdict(ev.match_score);
    document.getElementById("score-summary").textContent = ev.summary;

    renderChips("matched-chips", ks.matched_skills, "chip-green");
    renderChips("missing-chips", ks.missing_skills, "chip-red");

    renderList("strengths-list",    ev.strengths);
    renderList("gaps-list",         ev.gaps);
    renderList("improvements-list", ev.improvements);
}

// ---- Form submit ----
form.addEventListener("submit", async (e) => {
    e.preventDefault(); // stop the browser from refreshing the page on submit

    // Validate inputs before making any API call
    if (!resumeInput.files?.[0]) {
        statusEl.textContent = "Please upload a PDF resume.";
        statusEl.className = "status error";
        return;
    }
    const jobText = document.getElementById("job-text").value.trim();
    if (!jobText) {
        statusEl.textContent = "Please paste a job description.";
        statusEl.className = "status error";
        return;
    }

    setLoading(true);

    // FormData bundles the file + text into a multipart/form-data request
    // that FastAPI's UploadFile + Form parameters can receive
    const formData = new FormData();
    formData.append("resume_pdf", resumeInput.files[0]);
    formData.append("job_description", jobText);

    try {
        const response = await fetch(API_URL, { method: "POST", body: formData });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail?.error || err.detail || "API error");
        }

        renderResults(await response.json());
        setLoading(false);
        statusEl.textContent = "Done.";
        statusEl.className = "status success";

    } catch (err) {
        document.getElementById("skeleton").style.display = "none";
        statusEl.textContent = "Error: " + err.message;
        statusEl.className = "status error";
        btn.disabled    = false;
        btn.textContent = "Analyze Resume";
    }
});
