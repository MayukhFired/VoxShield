/* VoxShield AI — Clean, Minimal Frontend Logic */

const API = "";

/* =========================
   FILE UPLOAD
========================= */

(function() {
    const fileInput = document.getElementById("audioFile");
    const uploadArea = document.getElementById("uploadArea");
    const audioPlayer = document.getElementById("audioPlayer");
    const analyzeBtn = document.getElementById("analyzeBtn");

    if (!fileInput) return;

    fileInput.addEventListener("change", function() {
        const file = this.files[0];
        if (!file) return;
        audioPlayer.src = URL.createObjectURL(file);
        audioPlayer.style.display = "block";
        analyzeBtn.style.display = "inline-flex";
        uploadArea.querySelector(".upload-text").textContent = file.name;
    });

    // Drag and drop
    if (uploadArea) {
        uploadArea.addEventListener("dragover", function(e) {
            e.preventDefault();
            this.classList.add("dragging");
        });
        uploadArea.addEventListener("dragleave", function() {
            this.classList.remove("dragging");
        });
        uploadArea.addEventListener("drop", function(e) {
            e.preventDefault();
            this.classList.remove("dragging");
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                fileInput.dispatchEvent(new Event("change"));
            }
        });
    }
})();


/* =========================
   ANALYZE UPLOADED AUDIO
========================= */

async function analyzeAudio() {
    const fileInput = document.getElementById("audioFile");
    const resultDiv = document.getElementById("detectResult");
    const specWrap = document.getElementById("spectrogramWrap");
    const checksDiv = document.getElementById("signalChecks");
    const btn = document.getElementById("analyzeBtn");

    if (!fileInput || !fileInput.files.length) return;

    btn.textContent = "Analyzing...";
    btn.disabled = true;
    resultDiv.style.display = "none";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const res = await fetch(API + "/api/detect", { method: "POST", body: formData });
        if (!res.ok) throw new Error((await res.json()).detail || "Failed");
        const data = await res.json();
        showResult(data, resultDiv, specWrap, checksDiv);
    } catch (err) {
        resultDiv.style.display = "block";
        resultDiv.innerHTML = '<div class="card" style="border-color:rgba(239,68,68,0.3);"><p style="color:#ef4444;">Error: ' + err.message + '</p></div>';
    } finally {
        btn.textContent = "Analyze this voice";
        btn.disabled = false;
    }
}
window.analyzeAudio = analyzeAudio;


/* =========================
   DEMO SAMPLES
========================= */

async function runDemoSample(sampleId) {
    const resultDiv = document.getElementById("detectResult");
    const specWrap = document.getElementById("spectrogramWrap");
    const checksDiv = document.getElementById("signalChecks");
    const audioPlayer = document.getElementById("audioPlayer");

    // Show loading
    resultDiv.style.display = "block";
    resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><div class="loading-text">Analyzing...</div></div>';

    if (audioPlayer) {
        audioPlayer.src = API + "/api/demo/audio/" + sampleId;
        audioPlayer.style.display = "block";
    }

    try {
        const res = await fetch(API + "/api/demo/analyze/" + sampleId);
        if (!res.ok) throw new Error("Analysis failed");
        const data = await res.json();
        showResult(data, resultDiv, specWrap, checksDiv);
    } catch (err) {
        resultDiv.innerHTML = '<div class="card"><p style="color:#ef4444;">Error: ' + err.message + '. Make sure backend is running.</p></div>';
    }
}
window.runDemoSample = runDemoSample;


/* =========================
   SHOW DETECTION RESULT
========================= */

function showResult(data, resultDiv, specWrap, checksDiv) {
    const isFake = data.verdict === "fake";

    // Big verdict
    resultDiv.style.display = "block";
    resultDiv.innerHTML =
        '<div class="verdict ' + (isFake ? 'verdict-danger' : 'verdict-safe') + '">' +
            '<div class="verdict-icon">' + (isFake ? '⚠️' : '✓') + '</div>' +
            '<div class="verdict-label">' + (isFake ? 'Fake Voice Detected' : 'Real Voice') + '</div>' +
            '<div class="verdict-sub">' + (isFake ? 'This voice shows signs of AI generation.' : 'Voice patterns are consistent with natural speech.') + '</div>' +
            '<div class="verdict-confidence" style="color:' + (isFake ? '#ef4444' : '#22c55e') + ';">' + Math.round(data.confidence * 100) + '% confidence</div>' +
        '</div>';

    // Spectrogram
    if (specWrap && data.spectrogram && data.spectrogram.data.length > 0) {
        specWrap.style.display = "block";
        renderSpectrogram(document.getElementById("spectrogramCanvas"), data.spectrogram);
    }

    // Signal checks
    if (checksDiv && data.signal_checks) {
        checksDiv.innerHTML = '<div class="checks">' +
            data.signal_checks.map(function(c) {
                return '<div class="check"><div class="check-dot ' + (c.passed ? 'pass' : 'fail') + '"></div><div class="check-label">' + c.check_name.replace(/_/g, ' ') + '</div></div>';
            }).join('') +
        '</div>';
    }
}


/* =========================
   SPECTROGRAM RENDERER
========================= */

function renderSpectrogram(canvas, spec) {
    if (!canvas || !spec.data.length) return;
    const ctx = canvas.getContext("2d");
    const nMels = spec.n_mels;
    const nFrames = spec.n_frames;
    canvas.width = Math.min(720, nFrames * 4);
    canvas.height = nMels * 2.5;
    const cw = canvas.width / nFrames;
    const ch = canvas.height / nMels;

    for (let m = 0; m < nMels; m++) {
        for (let f = 0; f < nFrames; f++) {
            const v = Math.max(0, Math.min(1, spec.data[m][f]));
            const r = Math.round(v * 220 + 10);
            const g = Math.round(v * 80 + 20);
            const b = Math.round((1 - v) * 180 + 40);
            ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
            ctx.fillRect(f * cw, (nMels - 1 - m) * ch, cw + 1, ch + 1);
        }
    }
}


/* =========================
   PWA INSTALL
========================= */

let deferredPrompt = null;
window.addEventListener("beforeinstallprompt", function(e) {
    e.preventDefault();
    deferredPrompt = e;
});



/* =========================
   BLACKLIST — Search & Report
========================= */

(function() {
    const searchForm = document.getElementById("blacklistSearchForm");
    const searchInput = document.getElementById("search");
    const searchResult = document.getElementById("searchResult");
    const reportForm = document.getElementById("reportForm");
    const blacklistTable = document.getElementById("blacklistTable");

    // Search
    if (searchForm) {
        searchForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            const q = searchInput ? searchInput.value.trim() : "";
            if (!q) { showResult("Please enter a phone number.", "warning"); return; }

            try {
                const res = await fetch(API + "/api/blacklist/check/" + encodeURIComponent(q));
                const data = await res.json();
                if (data.is_blacklisted) {
                    showResult("⚠️ Number found — " + data.status.toUpperCase() + " (reported " + data.reports_count + " times)", "danger");
                } else {
                    showResult("✓ Number is clean. Not found in database.", "safe");
                }
            } catch(err) {
                showResult("Could not check. Is the backend running?", "warning");
            }
        });
    }

    function showResult(text, type) {
        if (!searchResult) return;
        searchResult.style.display = "block";
        const colors = { danger: "#dc2626", safe: "#16a34a", warning: "#d97706" };
        searchResult.style.color = colors[type] || "#374151";
        searchResult.style.padding = "12px";
        searchResult.style.marginTop = "12px";
        searchResult.style.borderRadius = "8px";
        searchResult.style.background = type === "danger" ? "#fef2f2" : type === "safe" ? "#f0fdf4" : "#fffbeb";
        searchResult.style.fontSize = "0.85rem";
        searchResult.style.fontWeight = "600";
        searchResult.textContent = text;
    }

    // Report
    if (reportForm) {
        reportForm.addEventListener("submit", async function(e) {
            e.preventDefault();
            const phone = document.getElementById("phone");
            const reason = document.getElementById("reason");
            if (!phone || !phone.value.trim()) { alert("Enter a phone number."); return; }

            try {
                await fetch(API + "/api/blacklist/report", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ phone_number: phone.value.trim(), confidence_score: 0.85, notes: reason ? reason.value : "" })
                });
                alert("Report submitted successfully!");
                reportForm.reset();
                loadTable();
            } catch(err) {
                alert("Failed to submit report.");
            }
        });
    }

    // Load table
    async function loadTable() {
        if (!blacklistTable) return;
        const tbody = blacklistTable.querySelector("tbody");
        if (!tbody) return;
        try {
            const res = await fetch(API + "/api/blacklist/list?page=1&page_size=20");
            const data = await res.json();
            if (data.entries && data.entries.length > 0) {
                tbody.innerHTML = "";
                data.entries.forEach(function(entry) {
                    const tr = document.createElement("tr");
                    const riskClass = entry.status === "confirmed" ? "badge-danger" : entry.reports_count >= 2 ? "badge-warning" : "badge-safe";
                    const riskLabel = entry.status === "confirmed" ? "HIGH" : entry.reports_count >= 2 ? "MEDIUM" : "LOW";
                    const date = new Date(entry.last_reported).toLocaleDateString("en-GB", {day:"numeric",month:"short",year:"numeric"});
                    tr.innerHTML = "<td>" + entry.phone_number + "</td><td><span class='badge " + riskClass + "'>" + riskLabel + "</span></td><td>" + entry.status.toUpperCase() + "</td><td>" + date + "</td>";
                    tbody.appendChild(tr);
                });
            }
        } catch(err) {}
    }

    if (blacklistTable) loadTable();
})();
