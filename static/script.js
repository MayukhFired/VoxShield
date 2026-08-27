/* =========================================================
   VOXSHIELD AI — Frontend JavaScript
   Connected to FastAPI backend at /api/*
========================================================= */

const API_BASE = "";  // Same origin — served by FastAPI


/* =========================================================
   AUDIO DETECTION (index.html #detect)
========================================================= */

(function initDetection() {

    const detectSection = document.querySelector("#detect");
    if (!detectSection) return;

    const audioForm = detectSection.querySelector("form");
    const audioFile = document.querySelector("#audioFile");
    const audioPlayer = detectSection.querySelector("audio");
    const spectrogramCanvas = document.querySelector("#spectrogramCanvas");
    const resultBox = document.querySelector("#detectResult");
    const checksContainer = document.querySelector("#signalChecks");
    const submitBtn = audioForm ? audioForm.querySelector("button[type='submit']") : null;

    // Preview selected audio
    if (audioFile && audioPlayer) {
        audioFile.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;
            audioPlayer.src = URL.createObjectURL(file);
            // Reset previous results
            if (resultBox) resultBox.style.display = "none";
            if (checksContainer) checksContainer.innerHTML = "";
        });
    }

    // Submit for analysis
    if (audioForm) {
        audioForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            if (!audioFile || !audioFile.files.length) {
                alert("Please select an audio file first.");
                return;
            }

            const file = audioFile.files[0];

            // Max 10MB check
            if (file.size > 10 * 1024 * 1024) {
                alert("File too large. Maximum size is 10MB.");
                return;
            }

            // Show loading state
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "Analyzing...";
            }

            const formData = new FormData();
            formData.append("file", file);

            try {
                const response = await fetch(API_BASE + "/api/detect", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || "Analysis failed");
                }

                const result = await response.json();
                displayDetectionResult(result);

            } catch (error) {
                alert("Error: " + error.message);
                console.error(error);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Analyze Audio";
                }
            }
        });
    }

    function displayDetectionResult(result) {
        if (!resultBox) return;

        resultBox.style.display = "block";

        // Use big verdict display
        const isFake = result.verdict === "fake";
        resultBox.className = "verdict-huge " + (isFake ? "verdict-danger" : "verdict-safe");
        
        const icon = isFake ? "⚠️" : "✅";
        const label = isFake ? "FAKE VOICE DETECTED" : "REAL - SAFE";
        const sublabel = isFake 
            ? "This voice shows signs of AI generation. Do NOT trust this caller." 
            : "Voice patterns are consistent with natural human speech.";
        
        resultBox.innerHTML = 
            '<div class="verdict-icon">' + icon + '</div>' +
            '<div class="verdict-label">' + label + '</div>' +
            '<div class="verdict-sublabel">' + sublabel + '</div>' +
            '<div class="verdict-confidence" style="color:' + (isFake ? '#ef4444' : '#22c55e') + ';">Confidence: ' + Math.round(result.confidence * 100) + '%</div>' +
            '<p style="color:#64748b;font-size:0.75rem;margin-top:8px;">Duration: ' + result.duration_seconds + 's</p>';

        // Render spectrogram
        if (spectrogramCanvas && result.spectrogram && result.spectrogram.data.length > 0) {
            renderSpectrogram(spectrogramCanvas, result.spectrogram);
        }

        // Render signal checks with new grid format
        if (checksContainer && result.signal_checks) {
            renderSignalChecks(checksContainer, result.signal_checks);
        }
    }

})();


/* =========================================================
   SPECTROGRAM RENDERER
========================================================= */

function renderSpectrogram(canvas, specData) {
    const ctx = canvas.getContext("2d");
    const nMels = specData.n_mels;
    const nFrames = specData.n_frames;

    canvas.width = Math.min(800, nFrames * 4);
    canvas.height = nMels * 3;

    const cellWidth = canvas.width / nFrames;
    const cellHeight = canvas.height / nMels;

    for (let mel = 0; mel < nMels; mel++) {
        for (let frame = 0; frame < nFrames; frame++) {
            const value = specData.data[mel][frame];
            ctx.fillStyle = spectrogramColor(value);
            ctx.fillRect(
                frame * cellWidth,
                (nMels - 1 - mel) * cellHeight,
                cellWidth + 1,
                cellHeight + 1
            );
        }
    }
}

function spectrogramColor(v) {
    v = Math.max(0, Math.min(1, v));
    if (v < 0.25) {
        const t = v / 0.25;
        return "rgb(" + Math.round(t * 30) + "," + Math.round(t * 50) + "," + Math.round(50 + t * 150) + ")";
    } else if (v < 0.5) {
        const t = (v - 0.25) / 0.25;
        return "rgb(" + Math.round(30 + t * 20) + "," + Math.round(50 + t * 150) + "," + Math.round(200 - t * 50) + ")";
    } else if (v < 0.75) {
        const t = (v - 0.5) / 0.25;
        return "rgb(" + Math.round(50 + t * 200) + "," + Math.round(200 - t * 50) + "," + Math.round(150 - t * 120) + ")";
    } else {
        const t = (v - 0.75) / 0.25;
        return "rgb(250," + Math.round(150 - t * 120) + "," + Math.round(30 - t * 20) + ")";
    }
}


/* =========================================================
   SIGNAL CHECKS RENDERER
========================================================= */

function renderSignalChecks(container, checks) {
    container.innerHTML = "";
    
    const grid = document.createElement("div");
    grid.className = "check-grid";

    checks.forEach(function (check) {
        const passed = check.passed;
        const icon = passed ? "✓" : "✗";
        const name = check.check_name.replace(/_/g, " ");
        const score = Math.round(check.score * 100);

        const div = document.createElement("div");
        div.className = "check-item";
        div.innerHTML =
            '<div class="check-icon ' + (passed ? "pass" : "fail") + '">' + icon + '</div>' +
            '<div class="check-info">' +
            '<div class="check-name">' + name + '</div>' +
            '<div class="check-score">' + score + '% — ' + (passed ? 'Normal' : 'Suspicious') + '</div>' +
            '</div>';

        grid.appendChild(div);
    });

    container.appendChild(grid);
}


/* =========================================================
   LIVE MICROPHONE (index.html #live)
========================================================= */

(function initLiveMic() {

    const liveSection = document.querySelector("#live");
    if (!liveSection) return;

    const startBtn = document.querySelector("#startMic");
    const stopBtn = document.querySelector("#stopMic");
    const waveformEl = document.querySelector("#waveformDisplay");
    const liveResultEl = document.querySelector("#liveResult");
    const confidenceBar = document.querySelector("#liveConfidence");
    const confidenceText = document.querySelector("#liveConfidenceText");

    let mediaRecorder = null;
    let audioStream = null;
    let ws = null;
    let audioContext = null;
    let analyser = null;
    let animationId = null;

    if (startBtn) {
        startBtn.addEventListener("click", startListening);
    }

    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.addEventListener("click", stopListening);
    }

    async function startListening() {
        try {
            audioStream = await navigator.mediaDevices.getUserMedia({
                audio: { sampleRate: 16000, channelCount: 1 }
            });

            startBtn.disabled = true;
            stopBtn.disabled = false;

            if (liveResultEl) {
                liveResultEl.textContent = "LISTENING...";
                liveResultEl.style.color = "#3b82f6";
            }

            // Audio visualizer
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(audioStream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            source.connect(analyser);
            animateWaveform();

            // WebSocket connection
            const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            ws = new WebSocket(wsProtocol + "//" + window.location.host + "/ws/stream");

            ws.onopen = function () {
                console.log("WebSocket connected");
                // Record in 3-second chunks
                mediaRecorder = new MediaRecorder(audioStream, { mimeType: "audio/webm" });
                mediaRecorder.ondataavailable = function (event) {
                    if (event.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {
                        event.data.arrayBuffer().then(function (buffer) {
                            ws.send(buffer);
                        });
                    }
                };
                mediaRecorder.start(3000);
            };

            ws.onmessage = function (event) {
                const data = JSON.parse(event.data);
                if (data.error) {
                    console.error("Detection error:", data.error);
                    return;
                }
                displayLiveResult(data);
            };

            ws.onerror = function () {
                if (liveResultEl) {
                    liveResultEl.textContent = "CONNECTION ERROR";
                    liveResultEl.style.color = "#ef4444";
                }
            };

        } catch (error) {
            if (error.name === "NotAllowedError") {
                alert("Microphone permission denied. Please allow access.");
            } else {
                alert("Error: " + error.message);
            }
        }
    }

    function stopListening() {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        if (ws) {
            ws.close();
            ws = null;
        }
        if (audioStream) {
            audioStream.getTracks().forEach(function (track) { track.stop(); });
            audioStream = null;
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }

        startBtn.disabled = false;
        stopBtn.disabled = true;

        if (waveformEl) waveformEl.textContent = "Microphone stopped";
        if (liveResultEl) {
            liveResultEl.textContent = "STOPPED";
            liveResultEl.style.color = "#94a3b8";
        }
    }

    function animateWaveform() {
        if (!analyser || !waveformEl) return;
        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function draw() {
            analyser.getByteFrequencyData(dataArray);
            let bars = "";
            const chars = "▁▂▃▄▅▆▇█";
            for (let i = 0; i < 40; i++) {
                const val = dataArray[i * 3] || 0;
                const idx = Math.floor((val / 255) * (chars.length - 1));
                bars += chars[idx];
            }
            waveformEl.textContent = bars;
            animationId = requestAnimationFrame(draw);
        }
        draw();
    }

    function displayLiveResult(result) {
        if (liveResultEl) {
            const verdict = result.verdict.toUpperCase();
            liveResultEl.textContent = verdict;
            liveResultEl.style.color = result.verdict === "fake" ? "#ef4444" : "#22c55e";
        }
        if (confidenceBar) {
            confidenceBar.value = Math.round(result.confidence * 100);
        }
        if (confidenceText) {
            confidenceText.textContent = Math.round(result.confidence * 100) + "%";
        }
    }

})();


/* =========================================================
   BLACKLIST — SEARCH & REPORT (blacklist.html)
========================================================= */

(function initBlacklist() {

    const blacklistTable = document.querySelector("#blacklistTable");

    // === SEARCH ===
    const searchForm = document.getElementById("blacklistSearchForm");
    const searchInput = document.getElementById("search");
    const searchResult = document.getElementById("searchResult");

    if (searchForm) {
        searchForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const query = searchInput ? searchInput.value.trim() : "";
            if (!query) {
                showSearchResult("warning", "Please enter a phone number.");
                return;
            }

            try {
                const response = await fetch(API_BASE + "/api/blacklist/check/" + encodeURIComponent(query));
                const data = await response.json();

                if (data.is_blacklisted) {
                    showSearchResult("danger",
                        "⚠️ Number found in database — " + data.status.toUpperCase() +
                        "<br><span style='color:#94a3b8;font-size:0.75rem;'>Reported " + data.reports_count + " time(s) | Risk: " + data.risk_level.toUpperCase() + "</span>"
                    );
                } else {
                    showSearchResult("safe",
                        "✓ Number is clean<br><span style='color:#94a3b8;font-size:0.75rem;'>Not found in our database.</span>"
                    );
                }
            } catch (error) {
                showSearchResult("warning", "Failed to check. Is the backend running?");
                console.error(error);
            }
        });
    }

    function showSearchResult(type, html) {
        if (!searchResult) return;
        searchResult.style.display = "block";

        const colors = {
            danger: { color: "#fca5a5", border: "rgba(239,68,68,0.3)", bg: "rgba(239,68,68,0.05)" },
            safe: { color: "#86efac", border: "rgba(34,197,94,0.3)", bg: "rgba(34,197,94,0.05)" },
            warning: { color: "#fcd34d", border: "rgba(245,158,11,0.3)", bg: "rgba(245,158,11,0.05)" }
        };
        const c = colors[type] || colors.warning;
        searchResult.style.borderColor = c.border;
        searchResult.style.background = c.bg;
        searchResult.innerHTML = '<strong style="color:' + c.color + ';">' + html + '</strong>';
    }

    // === REPORT ===
    const reportForm = document.getElementById("reportForm");

    if (reportForm) {
        reportForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const phone = document.getElementById("phone");
            const reason = document.getElementById("reason");
            const description = document.getElementById("description");

            if (!phone || !phone.value.trim()) {
                alert("Please enter a phone number.");
                return;
            }
            if (!reason || !reason.value) {
                alert("Please select a reason.");
                return;
            }

            const btn = reportForm.querySelector("button[type='submit']");
            if (btn) { btn.disabled = true; btn.textContent = "Submitting..."; }

            try {
                const response = await fetch(API_BASE + "/api/blacklist/report", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        phone_number: phone.value.trim(),
                        confidence_score: 0.85,
                        notes: (reason.value || "") + ": " + (description ? description.value : "")
                    })
                });

                if (!response.ok) throw new Error("Report failed");

                alert("✅ Report submitted successfully! Number added to database.");
                reportForm.reset();
                loadBlacklistTable(); // Refresh table

            } catch (error) {
                alert("Failed to submit report. Is the backend running?");
                console.error(error);
            } finally {
                if (btn) { btn.disabled = false; btn.textContent = "Submit Report"; }
            }
        });
    }

    // === LOAD TABLE FROM API ===
    async function loadBlacklistTable() {
        if (!blacklistTable) return;

        const tbody = blacklistTable.querySelector("tbody");
        if (!tbody) return;

        try {
            const response = await fetch(API_BASE + "/api/blacklist/list?page=1&page_size=20");
            const data = await response.json();

            if (data.entries && data.entries.length > 0) {
                tbody.innerHTML = "";
                data.entries.forEach(function (entry) {
                    const tr = document.createElement("tr");

                    const riskClass = entry.status === "confirmed" ? "risk-high" :
                        entry.reports_count >= 2 ? "risk-medium" : "risk-low";
                    const riskLabel = entry.status === "confirmed" ? "HIGH" :
                        entry.reports_count >= 2 ? "MEDIUM" : "LOW";

                    const date = new Date(entry.last_reported);
                    const dateStr = date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

                    tr.innerHTML =
                        "<td>" + entry.phone_number + "</td>" +
                        '<td><b class="' + riskClass + '">' + riskLabel + "</b></td>" +
                        "<td>" + entry.status.toUpperCase() + "</td>" +
                        "<td>" + dateStr + "</td>";

                    tbody.appendChild(tr);
                });
            }
            // If no entries, keep the demo data as fallback

        } catch (error) {
            console.log("Could not load blacklist from API, using demo data.");
        }
    }

    // Load on page ready
    if (blacklistTable) {
        loadBlacklistTable();
    }

    // === TABLE SORTING ===
    if (blacklistTable) {
        const headers = blacklistTable.querySelectorAll("thead th");
        let sortDirection = {};

        headers.forEach(function (header, columnIndex) {
            header.addEventListener("click", function () {
                const tbody = blacklistTable.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));

                sortDirection[columnIndex] = !sortDirection[columnIndex];
                const direction = sortDirection[columnIndex] ? 1 : -1;

                rows.sort(function (a, b) {
                    const valA = a.children[columnIndex].textContent.trim().toLowerCase();
                    const valB = b.children[columnIndex].textContent.trim().toLowerCase();
                    return valA.localeCompare(valB) * direction;
                });

                rows.forEach(function (row) { tbody.appendChild(row); });
            });
        });
    }

    // === PAGINATION ===
    const prevBtn = document.getElementById("previousPage");
    const nextBtn = document.getElementById("nextPage");
    const pageButtons = document.querySelectorAll(".page-number");
    let currentPage = 1;
    const rowsPerPage = 5;

    function showPage(page) {
        if (!blacklistTable) return;
        const rows = Array.from(blacklistTable.querySelectorAll("tbody tr"));
        const totalPages = Math.max(1, Math.ceil(rows.length / rowsPerPage));

        if (page < 1) page = 1;
        if (page > totalPages) page = totalPages;
        currentPage = page;

        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;

        rows.forEach(function (row, i) {
            row.style.display = (i >= start && i < end) ? "" : "none";
        });

        pageButtons.forEach(function (btn) {
            const p = Number(btn.dataset.page);
            btn.classList.toggle("active-page", p === currentPage);
            btn.style.display = p <= totalPages ? "" : "none";
        });

        if (prevBtn) prevBtn.disabled = currentPage === 1;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    }

    pageButtons.forEach(function (btn, i) {
        btn.dataset.page = i + 1;
        btn.addEventListener("click", function () {
            showPage(Number(btn.dataset.page));
        });
    });

    if (prevBtn) prevBtn.addEventListener("click", function () { showPage(currentPage - 1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { showPage(currentPage + 1); });

    if (blacklistTable) showPage(1);

})();


/* =========================================================
   SIMULATED CALL (index.html #call)
========================================================= */

(function initCallSimulation() {

    const callSection = document.querySelector("#call");
    if (!callSection) return;

    const alertBox = document.querySelector("#callAlertBox");
    const alertStrong = alertBox ? alertBox.querySelector("strong") : null;
    const alertConfidence = document.querySelector("#callAlertConfidence");
    const alertDescription = document.querySelector("#callAlertDescription");
    const callerNumber = document.querySelector("#callerNumber");

    const fakeBtn = document.querySelector("#scenarioFake");
    const realBtn = document.querySelector("#scenarioReal");
    const suspiciousBtn = document.querySelector("#scenarioSuspicious");
    const declineBtn = document.querySelector("#callDecline");
    const acceptBtn = document.querySelector("#callAccept");

    const scenarios = {
        fake: {
            number: "+91 87654 32100",
            label: "⚠️ FAKE VOICE DETECTED",
            confidence: "AI Confidence: 94%",
            description: "This caller is using a synthetic or cloned voice.",
            color: "#ef4444",
            bg: "rgba(239, 68, 68, 0.08)",
            border: "rgba(239, 68, 68, 0.35)"
        },
        real: {
            number: "+91 98765 43210",
            label: "✓ REAL VOICE VERIFIED",
            confidence: "AI Confidence: 96%",
            description: "Voice patterns match natural human speech.",
            color: "#22c55e",
            bg: "rgba(34, 197, 94, 0.08)",
            border: "rgba(34, 197, 94, 0.35)"
        },
        suspicious: {
            number: "+91 11111 22222",
            label: "⚠️ SUSPICIOUS CALLER",
            confidence: "AI Confidence: 72%",
            description: "Unable to confirm authenticity. Exercise caution.",
            color: "#f59e0b",
            bg: "rgba(245, 158, 11, 0.08)",
            border: "rgba(245, 158, 11, 0.35)"
        }
    };

    function loadScenario(type) {
        const s = scenarios[type];
        if (!s) return;

        if (callerNumber) callerNumber.textContent = s.number;
        if (alertStrong) { alertStrong.textContent = s.label; alertStrong.style.color = s.color; }
        if (alertConfidence) alertConfidence.textContent = s.confidence;
        if (alertDescription) alertDescription.textContent = s.description;
        if (alertBox) { alertBox.style.background = s.bg; alertBox.style.borderColor = s.border; }
    }

    if (fakeBtn) fakeBtn.addEventListener("click", function () { loadScenario("fake"); });
    if (realBtn) realBtn.addEventListener("click", function () { loadScenario("real"); });
    if (suspiciousBtn) suspiciousBtn.addEventListener("click", function () { loadScenario("suspicious"); });

    if (declineBtn) {
        declineBtn.addEventListener("click", function () {
            alert("Call declined. You are safe.");
        });
    }

    if (acceptBtn) {
        acceptBtn.addEventListener("click", async function () {
            // Check blacklist before accepting
            const number = callerNumber ? callerNumber.textContent.trim() : "";
            if (number) {
                try {
                    const resp = await fetch(API_BASE + "/api/blacklist/check/" + encodeURIComponent(number));
                    const data = await resp.json();
                    if (data.is_blacklisted) {
                        const proceed = confirm(
                            "⚠️ WARNING: This number is in our blacklist!\n" +
                            "Reported " + data.reports_count + " time(s).\n" +
                            "Status: " + data.status.toUpperCase() + "\n\n" +
                            "Do you still want to accept?"
                        );
                        if (!proceed) return;
                    }
                } catch (e) {
                    // Backend not available, continue
                }
            }
            alert("Call accepted. AI monitoring active.");
        });
    }

    // Load default scenario
    loadScenario("fake");

})();


/* =========================================================
   CONTACT FORM
========================================================= */

(function initContact() {
    const contactForm = document.querySelector("#contact form");
    if (!contactForm) return;

    contactForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const name = document.querySelector("#name");
        if (name && name.value) {
            alert("Thank you, " + name.value + "! Your message has been received.");
            contactForm.reset();
        } else {
            alert("Please fill all fields.");
        }
    });
})();


/* =========================================================
   SMOOTH NAVIGATION
========================================================= */

document.querySelectorAll("nav a, footer a").forEach(function (link) {
    link.addEventListener("click", function (event) {
        const href = link.getAttribute("href");
        if (href && href.startsWith("#")) {
            const target = document.querySelector(href);
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: "smooth" });
            }
        }
    });
});


/* =========================================================
   DEMO SAMPLES — Instant pre-loaded analysis
========================================================= */

async function runDemoSample(sampleId) {
    const resultBox = document.querySelector("#detectResult");
    const spectrogramCanvas = document.querySelector("#spectrogramCanvas");
    const checksContainer = document.querySelector("#signalChecks");
    const audioPlayer = document.querySelector("#detect audio");

    // Show loading
    if (resultBox) {
        resultBox.style.display = "block";
        const verdictEl = resultBox.querySelector(".verdict-text");
        if (verdictEl) { verdictEl.textContent = "ANALYZING..."; verdictEl.style.color = "#3b82f6"; }
    }

    try {
        // Load audio for playback
        if (audioPlayer) {
            audioPlayer.src = API_BASE + "/api/demo/audio/" + sampleId;
        }

        // Get analysis results (cached, instant)
        const response = await fetch(API_BASE + "/api/demo/analyze/" + sampleId);
        if (!response.ok) throw new Error("Demo analysis failed");

        const result = await response.json();

        // Display verdict
        if (resultBox) {
            const isFake = result.verdict === "fake";
            resultBox.style.display = "block";
            resultBox.className = "verdict-huge " + (isFake ? "verdict-danger" : "verdict-safe");
            
            const icon = isFake ? "⚠️" : "✅";
            const label = isFake ? "FAKE VOICE DETECTED" : "REAL - SAFE";
            const sublabel = isFake 
                ? "This voice shows signs of AI generation." 
                : "Voice patterns are consistent with natural human speech.";
            
            resultBox.innerHTML = 
                '<div class="verdict-icon">' + icon + '</div>' +
                '<div class="verdict-label">' + label + '</div>' +
                '<div class="verdict-sublabel">' + sublabel + '</div>' +
                '<div class="verdict-confidence" style="color:' + (isFake ? '#ef4444' : '#22c55e') + ';">Confidence: ' + Math.round(result.confidence * 100) + '%</div>' +
                '<p style="color:#64748b;font-size:0.75rem;margin-top:8px;">Sample: ' + (result.demo_info ? result.demo_info.label : sampleId) + '</p>';
        }

        // Render spectrogram
        if (spectrogramCanvas && result.spectrogram && result.spectrogram.data.length > 0) {
            renderSpectrogram(spectrogramCanvas, result.spectrogram);
        }

        // Render signal checks
        if (checksContainer && result.signal_checks) {
            renderSignalChecks(checksContainer, result.signal_checks);
        }

    } catch (error) {
        alert("Demo failed: " + error.message + "\nMake sure the backend is running.");
        console.error(error);
    }
}

// Make it global so onclick in HTML works
window.runDemoSample = runDemoSample;


/* =========================================================
   PWA INSTALL PROMPT
========================================================= */

let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    // Show install banner
    const banner = document.createElement('div');
    banner.id = 'installBanner';
    banner.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#3b82f6,#2563eb);color:white;padding:14px 24px;border-radius:12px;box-shadow:0 10px 30px rgba(37,99,235,0.4);z-index:9999;display:flex;align-items:center;gap:12px;font-size:0.85rem;font-weight:600;';
    banner.innerHTML = '<span>📱 Install VoxShield on your device</span><button onclick="installApp()" style="background:white;color:#2563eb;border:none;padding:8px 16px;border-radius:8px;font-weight:700;cursor:pointer;">Install</button><button onclick="this.parentElement.remove()" style="background:none;border:none;color:rgba(255,255,255,0.7);cursor:pointer;font-size:1.2rem;">✕</button>';
    document.body.appendChild(banner);
});

async function installApp() {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    console.log('Install:', result.outcome);
    deferredPrompt = null;
    const banner = document.getElementById('installBanner');
    if (banner) banner.remove();
}
window.installApp = installApp;


/* =========================================================
   INIT
========================================================= */

console.log("VoxShield AI frontend loaded — connected to backend API.");
