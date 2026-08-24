/* =========================================================
   VOXSHIELD AI
   Frontend JavaScript
========================================================= */


/* =========================================================
   AUDIO DETECTION
========================================================= */

const detectSection = document.querySelector("#detect");

if (detectSection) {

    const audioForm =
        detectSection.querySelector("form");

    const audioFile =
        document.querySelector("#audioFile");

    const audioPlayer =
        detectSection.querySelector("audio");

    const resultBox =
        detectSection.querySelector(
            "div:nth-of-type(3)"
        );

    const resultText =
        resultBox
            ? resultBox.querySelector("strong")
            : null;

    const confidenceText =
        resultBox
            ? resultBox.querySelector("p:last-child")
            : null;


    /* Select audio file */

    if (audioFile && audioPlayer) {

        audioFile.addEventListener(
            "change",
            function () {

                const file =
                    this.files[0];

                if (!file) {
                    return;
                }

                const audioURL =
                    URL.createObjectURL(file);

                audioPlayer.src =
                    audioURL;

                console.log(
                    "Selected file:",
                    file.name
                );

            }
        );

    }


    /* Analyze audio */

    if (audioForm) {

        audioForm.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();


                if (
                    !audioFile ||
                    !audioFile.files.length
                ) {

                    alert(
                        "Please select an audio file first."
                    );

                    return;
                }


                /* Demo result */

                const isFake =
                    Math.random() > 0.5;


                const confidence =
                    Math.floor(
                        Math.random() * 10 + 90
                    );


                if (
                    resultText &&
                    resultBox &&
                    confidenceText
                ) {

                    if (isFake) {

                        resultText.textContent =
                            "FAKE";

                        resultText.style.color =
                            "#ef4444";

                        resultBox.style.borderColor =
                            "rgba(239, 68, 68, 0.4)";

                    } else {

                        resultText.textContent =
                            "REAL";

                        resultText.style.color =
                            "#22c55e";

                        resultBox.style.borderColor =
                            "rgba(34, 197, 94, 0.4)";
                    }


                    confidenceText.textContent =
                        "Confidence: " +
                        confidence +
                        "%";
                }

            }
        );

    }

}



/* =========================================================
   LIVE MICROPHONE
========================================================= */

const liveSection =
    document.querySelector("#live");


if (liveSection) {

    const liveButtons =
        liveSection.querySelectorAll(
            "button"
        );


    const startMicButton =
        liveButtons[0];


    const stopMicButton =
        liveButtons[1];


    const waveform =
        liveSection.querySelector(
            "div:nth-of-type(2) > div"
        );


    const liveResult =
        liveSection.querySelector(
            "div:nth-of-type(4) strong"
        );


    const confidenceGauge =
        liveSection.querySelector(
            "progress"
        );


    const confidenceValue =
        liveSection.querySelector(
            "div:nth-of-type(3) p"
        );


    let microphoneStream =
        null;


    let waveformInterval =
        null;


    let confidenceInterval =
        null;


    /* =========================
       START MICROPHONE
    ========================== */

    if (startMicButton) {

        startMicButton.addEventListener(
            "click",
            async function () {

                try {

                    microphoneStream =
                        await navigator.mediaDevices
                            .getUserMedia({
                                audio: true
                            });


                    startMicButton.disabled =
                        true;


                    if (stopMicButton) {

                        stopMicButton.disabled =
                            false;
                    }


                    if (liveResult) {

                        liveResult.textContent =
                            "LISTENING...";

                        liveResult.style.color =
                            "#3b82f6";
                    }


                    /* Waveform animation */

                    if (waveform) {

                        waveformInterval =
                            setInterval(
                                function () {

                                    let bars = "";

                                    for (
                                        let i = 0;
                                        i < 35;
                                        i++
                                    ) {

                                        const height =
                                            Math.floor(
                                                Math.random() * 30
                                            );


                                        bars +=
                                            "▂▃▄▅▆▇"
                                            [height % 7];

                                    }


                                    waveform.textContent =
                                        bars;

                                },
                                100
                            );
                    }


                    /* Confidence */

                    confidenceInterval =
                        setInterval(
                            function () {

                                if (
                                    !microphoneStream
                                ) {

                                    clearInterval(
                                        confidenceInterval
                                    );

                                    return;
                                }


                                const confidence =
                                    Math.floor(
                                        Math.random() *
                                        45 +
                                        50
                                    );


                                if (
                                    confidenceGauge
                                ) {

                                    confidenceGauge.value =
                                        confidence;
                                }


                                if (
                                    confidenceValue
                                ) {

                                    confidenceValue.textContent =
                                        confidence +
                                        "%";
                                }

                            },
                            800
                        );


                } catch (error) {

                    alert(
                        "Microphone permission was denied."
                    );

                    console.error(error);

                }

            }
        );

    }


    /* =========================
       STOP MICROPHONE
    ========================== */

    if (stopMicButton) {

        stopMicButton.disabled =
            true;


        stopMicButton.addEventListener(
            "click",
            function () {

                if (microphoneStream) {

                    microphoneStream
                        .getTracks()
                        .forEach(
                            function (track) {

                                track.stop();

                            }
                        );

                    microphoneStream =
                        null;
                }


                clearInterval(
                    waveformInterval
                );


                clearInterval(
                    confidenceInterval
                );


                if (waveform) {

                    waveform.textContent =
                        "Microphone stopped";
                }


                startMicButton.disabled =
                    false;


                stopMicButton.disabled =
                    true;


                if (liveResult) {

                    liveResult.textContent =
                        "STOPPED";

                    liveResult.style.color =
                        "#94a3b8";
                }

            }
        );

    }

}



/* =========================================================
   CALLER BLACKLIST
   This section works ONLY on blacklist.html
========================================================= */

const blacklistTable =
    document.querySelector(
        "#blacklistTable"
    );


if (blacklistTable) {


    /* =========================
       SEARCH
    ========================== */

    const searchForm =
        document.getElementById(
            "blacklistSearchForm"
        );


    const searchInput =
        document.getElementById(
            "search"
        );


    const searchResult =
        document.getElementById(
            "searchResult"
        );


    if (searchForm) {

        searchForm.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();


                const searchValue =
                    searchInput
                        ? searchInput.value
                            .trim()
                            .toLowerCase()
                        : "";


                const rows =
                    Array.from(
                        blacklistTable
                            .querySelectorAll(
                                "tbody tr"
                            )
                    );


                if (!searchValue) {

                    if (searchResult) {

                        searchResult.style.display =
                            "block";

                        searchResult.innerHTML =
                            `
                            <strong style="color:#fcd34d;">
                                ⚠️ Please enter a phone number.
                            </strong>
                            `;
                    }

                    return;
                }


                let found = false;


                rows.forEach(
                    function (row) {

                        const rowText =
                            row.textContent
                                .toLowerCase();


                        if (
                            rowText.includes(
                                searchValue
                            )
                        ) {

                            row.style.display =
                                "";

                            found = true;

                        } else {

                            row.style.display =
                                "none";
                        }

                    }
                );


                if (searchResult) {

                    searchResult.style.display =
                        "block";


                    if (found) {

                        searchResult.innerHTML =
                            `
                            <strong style="color:#fca5a5;">
                                ⚠️ Number found in database
                            </strong>
                            <br>
                            <span style="color:#94a3b8;">
                                This number has been reported as suspicious.
                            </span>
                            `;

                    } else {

                        searchResult.innerHTML =
                            `
                            <strong style="color:#86efac;">
                                ✓ No report found
                            </strong>
                            <br>
                            <span style="color:#94a3b8;">
                                This number was not found in the demo database.
                            </span>
                            `;
                    }

                }

            }
        );

    }



    /* =========================
       REPORT FORM
    ========================== */

    const reportForm =
        document.getElementById(
            "reportForm"
        );


    if (reportForm) {

        reportForm.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();


                const phone =
                    document.getElementById(
                        "phone"
                    );


                const reason =
                    document.getElementById(
                        "reason"
                    );


                const description =
                    document.getElementById(
                        "description"
                    );


                if (
                    !phone ||
                    !reason ||
                    !description
                ) {

                    return;
                }


                if (
                    !phone.value.trim() ||
                    !reason.value ||
                    !description.value.trim()
                ) {

                    alert(
                        "Please fill all the fields."
                    );

                    return;
                }


                alert(
                    "✅ Report submitted successfully!"
                );


                reportForm.reset();

            }
        );

    }



    /* =========================
       TABLE SORTING
    ========================== */

    const headers =
        blacklistTable.querySelectorAll(
            "thead th"
        );


    let sortDirection = {};


    headers.forEach(
        function (
            header,
            columnIndex
        ) {

            header.addEventListener(
                "click",
                function () {

                    const tbody =
                        blacklistTable
                            .querySelector(
                                "tbody"
                            );


                    const rows =
                        Array.from(
                            tbody.querySelectorAll(
                                "tr"
                            )
                        );


                    sortDirection[columnIndex] =
                        !sortDirection[columnIndex];


                    const direction =
                        sortDirection[columnIndex]
                            ? 1
                            : -1;


                    rows.sort(
                        function (
                            rowA,
                            rowB
                        ) {

                            const valueA =
                                rowA
                                    .children[
                                        columnIndex
                                    ]
                                    .textContent
                                    .trim()
                                    .toLowerCase();


                            const valueB =
                                rowB
                                    .children[
                                        columnIndex
                                    ]
                                    .textContent
                                    .trim()
                                    .toLowerCase();


                            return (
                                valueA.localeCompare(
                                    valueB
                                ) * direction
                            );

                        }
                    );


                    rows.forEach(
                        function (row) {

                            tbody.appendChild(
                                row
                            );

                        }
                    );


                    /* Reset pagination */

                    showBlacklistPage(
                        1
                    );

                }
            );

        }
    );



    /* =========================
       PAGINATION
    ========================== */

    const previousButton =
        document.getElementById(
            "previousPage"
        );


    const nextButton =
        document.getElementById(
            "nextPage"
        );


    const pageButtons =
        document.querySelectorAll(
            ".page-number"
        );


    let currentPage = 1;


    const rowsPerPage = 3;


    function getBlacklistRows() {

        return Array.from(
            blacklistTable.querySelectorAll(
                "tbody tr"
            )
        );

    }


    function showBlacklistPage(
        page
    ) {

        const rows =
            getBlacklistRows();


        const totalPages =
            Math.max(
                1,
                Math.ceil(
                    rows.length /
                    rowsPerPage
                )
            );


        if (page < 1) {
            page = 1;
        }


        if (page > totalPages) {
            page = totalPages;
        }


        currentPage =
            page;


        const start =
            (page - 1) *
            rowsPerPage;


        const end =
            start +
            rowsPerPage;


        rows.forEach(
            function (
                row,
                index
            ) {

                if (
                    index >= start &&
                    index < end
                ) {

                    row.style.display =
                        "";

                } else {

                    row.style.display =
                        "none";
                }

            }
        );


        /* Active page */

        pageButtons.forEach(
            function (
                button
            ) {

                const buttonPage =
                    Number(
                        button.dataset.page
                    );


                button.classList.toggle(
                    "active-page",
                    buttonPage ===
                    currentPage
                );

            }
        );


        /* Previous */

        if (previousButton) {

            previousButton.disabled =
                currentPage === 1;
        }


        /* Next */

        if (nextButton) {

            nextButton.disabled =
                currentPage >=
                totalPages;
        }


        /* Hide unnecessary page buttons */

        pageButtons.forEach(
            function (
                button
            ) {

                const pageNumber =
                    Number(
                        button.dataset.page
                    );


                button.style.display =
                    pageNumber <= totalPages
                        ? ""
                        : "none";

            }
        );

    }



    /* Add page numbers */

    pageButtons.forEach(
        function (
            button,
            index
        ) {

            /*
             * Your HTML has:
             *
             * 1
             * 2
             * 3
             *
             * We assign the page number
             * automatically.
             */

            button.dataset.page =
                index + 1;


            button.addEventListener(
                "click",
                function () {

                    showBlacklistPage(
                        Number(
                            button.dataset.page
                        )
                    );

                }
            );

        }
    );


    /* Previous */

    if (previousButton) {

        previousButton.addEventListener(
            "click",
            function () {

                showBlacklistPage(
                    currentPage - 1
                );

            }
        );

    }


    /* Next */

    if (nextButton) {

        nextButton.addEventListener(
            "click",
            function () {

                showBlacklistPage(
                    currentPage + 1
                );

            }
        );

    }


    /* Start page */

    showBlacklistPage(1);

}



/* =========================================================
   SIMULATED CALL
========================================================= */

const callSection =
    document.querySelector("#call");


if (callSection) {

    const scenarioButtons =
        callSection.querySelectorAll(
            "button"
        );


    const callAlert =
        callSection.querySelector(
            "div:first-of-type > div"
        );


    const callStrong =
        callAlert
            ? callAlert.querySelector(
                "strong"
            )
            : null;


    const callConfidence =
        callAlert
            ? callAlert.querySelector(
                "p"
            )
            : null;


    /* Fake Call */

    if (scenarioButtons[2]) {

        scenarioButtons[2].addEventListener(
            "click",
            function () {

                if (callStrong) {

                    callStrong.textContent =
                        "⚠️ FAKE CALL DETECTED";

                    callStrong.style.color =
                        "#ef4444";
                }


                if (callConfidence) {

                    callConfidence.textContent =
                        "AI Confidence: 94%";
                }


                if (callAlert) {

                    callAlert.style.background =
                        "rgba(239, 68, 68, 0.1)";

                    callAlert.style.borderColor =
                        "rgba(239, 68, 68, 0.35)";
                }

            }
        );

    }


    /* Real Call */

    if (scenarioButtons[3]) {

        scenarioButtons[3].addEventListener(
            "click",
            function () {

                if (callStrong) {

                    callStrong.textContent =
                        "✓ REAL CALL";

                    callStrong.style.color =
                        "#22c55e";
                }


                if (callConfidence) {

                    callConfidence.textContent =
                        "AI Confidence: 96%";
                }


                if (callAlert) {

                    callAlert.style.background =
                        "rgba(34, 197, 94, 0.1)";

                    callAlert.style.borderColor =
                        "rgba(34, 197, 94, 0.35)";
                }

            }
        );

    }


    /* Suspicious Call */

    if (scenarioButtons[4]) {

        scenarioButtons[4].addEventListener(
            "click",
            function () {

                if (callStrong) {

                    callStrong.textContent =
                        "⚠️ SUSPICIOUS CALL";

                    callStrong.style.color =
                        "#f59e0b";
                }


                if (callConfidence) {

                    callConfidence.textContent =
                        "AI Confidence: 72%";
                }


                if (callAlert) {

                    callAlert.style.background =
                        "rgba(245, 158, 11, 0.1)";

                    callAlert.style.borderColor =
                        "rgba(245, 158, 11, 0.35)";
                }

            }
        );

    }


    /* Call controls */

    const declineButton =
        scenarioButtons[0];


    const acceptButton =
        scenarioButtons[1];


    if (declineButton) {

        declineButton.addEventListener(
            "click",
            function () {

                alert(
                    "Call declined."
                );

            }
        );

    }


    if (acceptButton) {

        acceptButton.addEventListener(
            "click",
            function () {

                alert(
                    "Call accepted."
                );

            }
        );

    }

}



/* =========================================================
   CONTACT FORM
========================================================= */

const contactForm =
    document.querySelector(
        "#contact form"
    );


if (contactForm) {

    contactForm.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();


            const name =
                document.querySelector(
                    "#name"
                );


            const email =
                document.querySelector(
                    "#email"
                );


            const message =
                document.querySelector(
                    "#message"
                );


            if (
                !name ||
                !email ||
                !message
            ) {

                return;
            }


            if (
                !name.value ||
                !email.value ||
                !message.value
            ) {

                alert(
                    "Please fill all fields."
                );

                return;
            }


            alert(
                "Thank you, " +
                name.value +
                "! Your message has been submitted."
            );


            contactForm.reset();

        }
    );

}



/* =========================================================
   SMOOTH NAVIGATION
========================================================= */

document
    .querySelectorAll(
        "nav a, footer a"
    )
    .forEach(
        function (link) {

            link.addEventListener(
                "click",
                function (event) {

                    const targetID =
                        link.getAttribute(
                            "href"
                        );


                    /*
                     * Only handle links that
                     * are actual same-page anchors.
                     *
                     * blacklist.html and index.html
                     * will work normally.
                     */

                    if (
                        targetID &&
                        targetID.startsWith("#")
                    ) {

                        const target =
                            document.querySelector(
                                targetID
                            );


                        if (target) {

                            event.preventDefault();


                            target.scrollIntoView({
                                behavior: "smooth"
                            });

                        }

                    }

                }
            );

        }
    );



/* =========================================================
   INITIAL MESSAGE
========================================================= */

console.log(
    "VoxShield AI frontend loaded successfully."
);