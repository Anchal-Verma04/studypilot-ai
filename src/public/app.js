// StudyPilot AI - Frontend Application Orchestrator

document.addEventListener("DOMContentLoaded", () => {
    // State management
    let appState = {
        currentNoteId: null,
        currentQuizId: null,
        currentQuizQuestions: [],
        currentQuizAnswers: {}, // question_id -> chosen option index
        currentQuestionIndex: 0,
        chartInstance: null
    };

    // DOM Elements
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabs = document.querySelectorAll(".tab-content");
    const tabTitle = document.getElementById("tab-title");
    const tabSubtitle = document.getElementById("tab-subtitle");
    const systemModeBadge = document.getElementById("system-mode");
    const backendStatus = document.getElementById("backend-status");

    // Initialize API connection
    checkBackendHealth();
    loadDashboardAnalytics();

    // Tab Navigation Logic
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-target");
            switchTab(targetTab);
        });
    });

    function switchTab(tabId) {
        // Update Nav Active State
        navButtons.forEach(b => {
            if (b.getAttribute("data-target") === tabId) {
                b.classList.add("active");
            } else {
                b.classList.remove("active");
            }
        });

        // Update Tab Visibilities
        tabs.forEach(t => {
            if (t.id === tabId) {
                t.classList.add("active");
            } else {
                t.classList.remove("active");
            }
        });

        // Update Header Titles
        if (tabId === "dashboard-tab") {
            tabTitle.innerText = "Student Dashboard";
            tabSubtitle.innerText = "Track your multi-agent educational progress and score statistics.";
            loadDashboardAnalytics();
        } else if (tabId === "studylab-tab") {
            tabTitle.innerText = "Study Lab";
            tabSubtitle.innerText = "Upload notes, scan security criteria, and extract key terms.";
        } else if (tabId === "quiz-tab") {
            tabTitle.innerText = "Quiz Session";
            tabSubtitle.innerText = "Validate your knowledge of the study materials.";
        } else if (tabId === "feedback-tab") {
            tabTitle.innerText = "Feedback Hub";
            tabSubtitle.innerText = "View comprehensive agent grading results and tutor analysis.";
        }
    }

    // API Health Check Function
    async function checkBackendHealth() {
        try {
            const res = await fetch("/api/health");
            const data = await res.json();
            if (data.status === "healthy") {
                backendStatus.innerText = "Connected";
                backendStatus.className = "status-val text-success";
                
                // Update system mode badge
                systemModeBadge.querySelector("span").innerText = data.llm_mode;
                if (data.llm_mode.includes("Gemini")) {
                    systemModeBadge.style.color = "#06b6d4";
                } else {
                    systemModeBadge.style.color = "#a855f7";
                }
            } else {
                backendStatus.innerText = "Error";
                backendStatus.className = "status-val text-danger";
            }
        } catch (err) {
            backendStatus.innerText = "Offline";
            backendStatus.className = "status-val text-danger";
            console.error("Backend health check failed:", err);
        }
    }

    // --- Study Lab Section ---
    const btnExtract = document.getElementById("btn-extract-notes");
    const notesTitleInput = document.getElementById("notes-title");
    const notesContentInput = document.getElementById("notes-content");

    // Security Badges
    const secSize = document.getElementById("sec-size-check");
    const secInjection = document.getElementById("sec-injection-check");
    const secXss = document.getElementById("sec-xss-check");
    const secLogDesc = document.getElementById("security-log-desc");

    // Output Cards
    const extractionResultCard = document.getElementById("extraction-result-card");
    const extractedSummary = document.getElementById("extracted-summary");
    const extractedTopics = document.getElementById("extracted-topics-tags");
    const extractedTerms = document.getElementById("extracted-terms-list");
    const btnGotoQuiz = document.getElementById("btn-goto-quiz");

    btnExtract.addEventListener("click", async () => {
        const title = notesTitleInput.value.trim();
        const content = notesContentInput.value.trim();

        if (!content) {
            alert("Please paste study notes before processing.");
            return;
        }

        // Reset UI indicators to "Scanning" state
        setSecurityState(secSize, "scanning", "Verifying...");
        setSecurityState(secInjection, "scanning", "Verifying...");
        setSecurityState(secXss, "scanning", "Verifying...");
        secLogDesc.innerText = "Safety Filter Agent: Initializing sanitization hooks and scanning buffer size...";
        
        extractionResultCard.classList.add("hide");
        btnExtract.disabled = true;
        btnExtract.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing Notes...';

        try {
            const res = await fetch("/api/notes/extract", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, content })
            });
            const data = await res.json();

            btnExtract.disabled = false;
            btnExtract.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Process Notes with Extractor';

            if (data.security_flag === true) {
                // Safety hazard detected
                secLogDesc.innerText = `[ALERT] Notes Extractor Agent blocked execution.\nReason: ${data.error}`;
                secLogDesc.style.color = "var(--danger)";
                
                if (data.error.includes("exceeds the safe limit")) {
                    setSecurityState(secSize, "flagged", "Flagged");
                    setSecurityState(secInjection, "inactive", "Passed");
                    setSecurityState(secXss, "inactive", "Neutralized");
                } else {
                    setSecurityState(secSize, "passed", "Passed");
                    setSecurityState(secInjection, "flagged", "Threat Detected");
                    setSecurityState(secXss, "inactive", "Neutralized");
                }
                return;
            }

            if (!data.success) {
                secLogDesc.innerText = `Error: ${data.error}`;
                secLogDesc.style.color = "var(--danger)";
                return;
            }

            // Safe & Successful extraction!
            setSecurityState(secSize, "passed", "Passed");
            setSecurityState(secInjection, "passed", "Passed (No Injection)");
            setSecurityState(secXss, "passed", "Sanitized & Clean");
            
            secLogDesc.innerText = "Safety Filter Agent: Validation complete. Inputs cleaned. Prompt sanitization check resolved. Extraction Agent parsing initiated.";
            secLogDesc.style.color = "var(--success)";

            // Render structures
            appState.currentNoteId = data.note_id;
            extractedSummary.innerText = data.summary;
            
            // Render topics
            extractedTopics.innerHTML = "";
            data.topics.forEach(topic => {
                const badge = document.createElement("span");
                badge.className = "tag";
                badge.innerText = topic;
                extractedTopics.appendChild(badge);
            });

            // Render key terms
            extractedTerms.innerHTML = "";
            data.terms.forEach(t => {
                const termCard = document.createElement("div");
                termCard.className = "term-detail-item";
                termCard.innerHTML = `<h5>${escapeHtml(t.term)}</h5><p>${escapeHtml(t.definition)}</p>`;
                extractedTerms.appendChild(termCard);
            });

            // Show panel
            extractionResultCard.classList.remove("hide");
            
        } catch (err) {
            btnExtract.disabled = false;
            btnExtract.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Process Notes with Extractor';
            console.error("Notes processing error:", err);
            secLogDesc.innerText = `Error contacting backend: ${err.message}`;
            secLogDesc.style.color = "var(--danger)";
        }
    });

    function setSecurityState(element, state, text) {
        element.innerText = text;
        if (state === "scanning") {
            element.className = "sec-badge inactive";
            element.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Checking';
        } else if (state === "passed") {
            element.className = "sec-badge passed";
        } else if (state === "flagged") {
            element.className = "sec-badge flagged";
        } else {
            element.className = "sec-badge inactive";
        }
    }

    // Generate Quiz button action
    btnGotoQuiz.addEventListener("click", async () => {
        if (!appState.currentNoteId) return;

        btnGotoQuiz.disabled = true;
        btnGotoQuiz.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating Exam...';

        try {
            const res = await fetch("/api/quiz/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ note_id: appState.currentNoteId })
            });
            const data = await res.json();
            btnGotoQuiz.disabled = false;
            btnGotoQuiz.innerHTML = '<i class="fa-solid fa-circle-question"></i> Generate Quiz from these Notes';

            if (!data.success) {
                alert(`Quiz Generation failed: ${data.error}`);
                return;
            }

            // Set up state
            appState.currentQuizId = data.quiz_id;
            appState.currentQuizQuestions = data.questions;
            appState.currentQuizAnswers = {};
            appState.currentQuestionIndex = 0;

            // Enable navigation tab
            const navQuizBtn = document.getElementById("nav-quiz");
            navQuizBtn.disabled = false;

            // Render quiz
            renderQuestion();
            switchTab("quiz-tab");

        } catch (err) {
            btnGotoQuiz.disabled = false;
            btnGotoQuiz.innerHTML = '<i class="fa-solid fa-circle-question"></i> Generate Quiz from these Notes';
            console.error("Quiz creation error:", err);
            alert("Error generating quiz. Please verify backend connection.");
        }
    });

    // --- Quiz Session Section ---
    const quizContainer = document.getElementById("quiz-container");
    const quizProgressText = document.getElementById("quiz-progress-text");
    const quizProgressBar = document.getElementById("quiz-progress-bar");
    const btnQuizPrev = document.getElementById("btn-quiz-prev");
    const btnQuizNext = document.getElementById("btn-quiz-next");
    const btnQuizSubmit = document.getElementById("btn-quiz-submit");

    function renderQuestion() {
        const question = appState.currentQuizQuestions[appState.currentQuestionIndex];
        if (!question) return;

        // Update progress UI
        const total = appState.currentQuizQuestions.length;
        quizProgressText.innerText = `Question ${appState.currentQuestionIndex + 1} of ${total}`;
        quizProgressBar.style.width = `${((appState.currentQuestionIndex + 1) / total) * 100}%`;

        // Render card
        quizContainer.innerHTML = "";
        
        const qCard = document.createElement("div");
        qCard.className = "quiz-question-card";
        
        const qTitle = document.createElement("h4");
        qTitle.innerText = `${appState.currentQuestionIndex + 1}. ${question.question}`;
        qCard.appendChild(qTitle);

        const optionsList = document.createElement("div");
        optionsList.className = "quiz-options-list";

        const savedAnswerIndex = appState.currentQuizAnswers[question.id];

        question.options.forEach((opt, idx) => {
            const label = document.createElement("label");
            label.className = `quiz-option-label ${savedAnswerIndex === idx ? 'selected' : ''}`;
            
            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = `question_${question.id}`;
            radio.value = idx;
            if (savedAnswerIndex === idx) radio.checked = true;

            radio.addEventListener("change", () => {
                appState.currentQuizAnswers[question.id] = idx;
                
                // Visually update selection
                optionsList.querySelectorAll("label").forEach(l => l.classList.remove("selected"));
                label.classList.add("selected");
            });

            label.appendChild(radio);
            
            const txt = document.createTextNode(` ${opt}`);
            label.appendChild(txt);
            
            optionsList.appendChild(label);
        });

        qCard.appendChild(optionsList);
        quizContainer.appendChild(qCard);

        // Adjust navigation buttons
        btnQuizPrev.disabled = (appState.currentQuestionIndex === 0);
        
        if (appState.currentQuestionIndex === total - 1) {
            btnQuizNext.classList.add("hide");
            btnQuizSubmit.classList.remove("hide");
        } else {
            btnQuizNext.classList.remove("hide");
            btnQuizSubmit.classList.add("hide");
        }
    }

    btnQuizPrev.addEventListener("click", () => {
        if (appState.currentQuestionIndex > 0) {
            appState.currentQuestionIndex--;
            renderQuestion();
        }
    });

    btnQuizNext.addEventListener("click", () => {
        const question = appState.currentQuizQuestions[appState.currentQuestionIndex];
        if (appState.currentQuizAnswers[question.id] === undefined) {
            alert("Please pick an option before proceeding.");
            return;
        }
        if (appState.currentQuestionIndex < appState.currentQuizQuestions.length - 1) {
            appState.currentQuestionIndex++;
            renderQuestion();
        }
    });

    btnQuizSubmit.addEventListener("click", async () => {
        const question = appState.currentQuizQuestions[appState.currentQuestionIndex];
        if (appState.currentQuizAnswers[question.id] === undefined) {
            alert("Please answer the final question before submitting.");
            return;
        }

        btnQuizSubmit.disabled = true;
        btnQuizSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Grading Answers...';

        try {
            const res = await fetch("/api/quiz/grade", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    quiz_id: appState.currentQuizId,
                    answers: appState.currentQuizAnswers
                })
            });
            const data = await res.json();
            btnQuizSubmit.disabled = false;
            btnQuizSubmit.innerHTML = '<i class="fa-solid fa-check-double"></i> Submit Exam Answers';

            if (!data.success) {
                alert(`Grading failed: ${data.error}`);
                return;
            }

            // Enable feedback tab
            const navFeedbackBtn = document.getElementById("nav-feedback");
            navFeedbackBtn.disabled = false;

            // Render feedback elements
            renderFeedback(data.grading);
            switchTab("feedback-tab");

        } catch (err) {
            btnQuizSubmit.disabled = false;
            btnQuizSubmit.innerHTML = '<i class="fa-solid fa-check-double"></i> Submit Exam Answers';
            console.error("Quiz submission error:", err);
            alert("Error submitting answers. Please check server.");
        }
    });

    // --- Feedback Section ---
    const feedbackPercentage = document.getElementById("feedback-percentage");
    const feedbackScoreText = document.getElementById("feedback-score-text");
    const feedbackGeneralMsg = document.getElementById("feedback-general-msg");
    const feedbackRecommendations = document.getElementById("feedback-recommendations");
    const feedbackExplanations = document.getElementById("feedback-explanations-container");
    const btnRestartStudy = document.getElementById("btn-restart-study");

    function renderFeedback(grading) {
        feedbackPercentage.innerText = `${grading.percentage}%`;
        feedbackScoreText.innerText = `Score: ${grading.score} / ${grading.total_questions}`;
        feedbackGeneralMsg.innerText = grading.overall_feedback;

        // Render color of grade badge based on score
        if (grading.percentage >= 75) {
            feedbackPercentage.style.background = "linear-gradient(135deg, var(--success), #34d399)";
        } else if (grading.percentage >= 50) {
            feedbackPercentage.style.background = "linear-gradient(135deg, var(--warning), #fbbf24)";
        } else {
            feedbackPercentage.style.background = "linear-gradient(135deg, var(--danger), #f87171)";
        }

        // Render Recommendations
        feedbackRecommendations.innerHTML = "";
        grading.recommendations.forEach(rec => {
            const li = document.createElement("li");
            li.innerHTML = `<i class="fa-solid fa-angles-right"></i> <span>${escapeHtml(rec)}</span>`;
            feedbackRecommendations.appendChild(li);
        });

        // Render Explanations list
        feedbackExplanations.innerHTML = "";
        grading.graded_questions.forEach(q => {
            const expl = grading.question_explanations[q.id] || "No explanation provided by grader.";
            
            const item = document.createElement("div");
            item.className = "feedback-explain-item";
            
            const qHeader = document.createElement("div");
            qHeader.className = "explain-q-header";
            qHeader.innerHTML = `
                <h4>Q: ${escapeHtml(q.question)}</h4>
                <span class="explain-badge ${q.is_correct ? 'correct' : 'incorrect'}">
                    ${q.is_correct ? '<i class="fa-solid fa-circle-check"></i> Correct' : '<i class="fa-solid fa-circle-xmark"></i> Incorrect'}
                </span>
            `;
            item.appendChild(qHeader);

            const optionsView = document.createElement("div");
            optionsView.className = "explain-options-view";
            
            q.options.forEach((opt, idx) => {
                let optClass = "explain-opt other-option";
                let optPrefix = "";

                if (idx === q.correct_answer) {
                    optClass = "explain-opt target-correct";
                    optPrefix = '<i class="fa-solid fa-check"></i> ';
                } else if (idx === q.user_answer && !q.is_correct) {
                    optClass = "explain-opt chosen-wrong";
                    optPrefix = '<i class="fa-solid fa-xmark"></i> ';
                }

                const optDiv = document.createElement("div");
                optDiv.className = optClass;
                optDiv.innerHTML = `${optPrefix}${escapeHtml(opt)}`;
                optionsView.appendChild(optDiv);
            });
            item.appendChild(optionsView);

            const descDiv = document.createElement("div");
            descDiv.className = "explain-desc";
            descDiv.innerHTML = `<strong>Grader Explains:</strong> ${escapeHtml(expl)}`;
            item.appendChild(descDiv);

            feedbackExplanations.appendChild(item);
        });
    }

    btnRestartStudy.addEventListener("click", () => {
        notesTitleInput.value = "";
        notesContentInput.value = "";
        extractionResultCard.classList.add("hide");
        
        // Reset safety badges
        secSize.className = "sec-badge inactive";
        secSize.innerText = "Unverified";
        secInjection.className = "sec-badge inactive";
        secInjection.innerText = "Unverified";
        secXss.className = "sec-badge inactive";
        secXss.innerText = "Unverified";
        secLogDesc.innerText = "Ready. Safety Agent is listening for note uploads.";
        secLogDesc.style.color = "var(--text-secondary)";

        // Disable temporary tabs
        document.getElementById("nav-quiz").disabled = true;
        document.getElementById("nav-feedback").disabled = true;

        switchTab("studylab-tab");
    });

    // --- Dashboard / History Loader ---
    const statAttempts = document.getElementById("stat-attempts");
    const statAvgScore = document.getElementById("stat-avg-score");
    const statTrend = document.getElementById("stat-trend");
    const listStrengths = document.getElementById("list-strengths");
    const listFocusAreas = document.getElementById("list-focus-areas");
    const historyTableBody = document.getElementById("history-table-body");

    async function loadDashboardAnalytics() {
        try {
            const res = await fetch("/api/analytics");
            const data = await res.json();

            if (!data.success) return;

            const analytics = data.analytics;
            
            // Set basic values
            statAttempts.innerText = analytics.total_attempts;
            statAvgScore.innerText = `${analytics.average_score}%`;
            statTrend.innerText = analytics.learning_trend;

            // Render Strengths
            listStrengths.innerHTML = "";
            if (analytics.strengths.length === 0) {
                listStrengths.innerHTML = '<li class="empty-list-msg">No mastered topics yet.</li>';
            } else {
                analytics.strengths.forEach(t => {
                    const li = document.createElement("li");
                    li.innerText = t;
                    listStrengths.appendChild(li);
                });
            }

            // Render Focus Areas
            listFocusAreas.innerHTML = "";
            if (analytics.focus_areas.length === 0) {
                listFocusAreas.innerHTML = '<li class="empty-list-msg">No review subjects yet.</li>';
            } else {
                analytics.focus_areas.forEach(t => {
                    const li = document.createElement("li");
                    li.innerText = t;
                    listFocusAreas.appendChild(li);
                });
            }

            // Render History logs table rows
            historyTableBody.innerHTML = "";
            if (data.history.length === 0) {
                historyTableBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="empty-table-msg">No previous quiz history found.</td>
                    </tr>
                `;
            } else {
                data.history.forEach(row => {
                    const tr = document.createElement("tr");
                    tr.className = "clickable-row";
                    tr.title = "Click to review this attempt";

                    const dateCell = document.createElement("td");
                    dateCell.innerText = new Date(row.created_at).toLocaleString();
                    tr.appendChild(dateCell);

                    const titleCell = document.createElement("td");
                    titleCell.innerText = row.note_title;
                    tr.appendChild(titleCell);

                    const topicsCell = document.createElement("td");
                    topicsCell.innerText = row.topics.join(", ") || "General";
                    tr.appendChild(topicsCell);

                    const scoreCell = document.createElement("td");
                    scoreCell.innerText = `${row.score} / ${row.total_questions}`;
                    tr.appendChild(scoreCell);

                    // Percentage + "View →" hover hint
                    const percentCell = document.createElement("td");
                    percentCell.innerHTML = `<strong>${row.percentage}%</strong><span class="row-hint"><i class="fa-solid fa-arrow-up-right-from-square"></i> View</span>`;
                    tr.appendChild(percentCell);

                    // Open detail modal on click
                    tr.addEventListener("click", () => openAttemptModal(row));

                    historyTableBody.appendChild(tr);
                });
            }

            // Draw progress trend line plot
            drawAnalyticsChart(analytics.chart_data);

        } catch (err) {
            console.error("Error loading dashboard metrics:", err);
        }
    }

    function drawAnalyticsChart(chartData) {
        const ctx = document.getElementById("progressChart").getContext("2d");
        
        if (appState.chartInstance) {
            appState.chartInstance.destroy();
        }

        if (!chartData || chartData.length === 0) {
            // Draw an empty placeholder
            appState.chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ["No attempts"],
                    datasets: [{
                        label: 'Performance',
                        data: [0],
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, max: 100 }
                    }
                }
            });
            return;
        }

        const labels = chartData.map(d => `Quiz ${d.attempt_num}`);
        const percentages = chartData.map(d => d.percentage);

        appState.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Score Percentage (%)',
                    data: percentages,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2.5,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: '#06b6d4',
                    pointBorderColor: '#fff',
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterBody: function(items) {
                                const index = items[0].dataIndex;
                                return `Notes: ${chartData[index].note_title}\nDate: ${chartData[index].date}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Helper: Escape text to avoid simple script injections when displaying
    function escapeHtml(text) {
        if (!text) return "";
        return text
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // ── Attempt Detail Modal ────────────────────────────────────────────────
    const attemptModal   = document.getElementById("attempt-detail-modal");
    const btnCloseModal  = document.getElementById("btn-close-modal");

    function openAttemptModal(row) {
        // ── Meta bar ──
        document.getElementById("modal-note-title").textContent = row.note_title || "Unknown Notes";
        document.getElementById("modal-date").textContent =
            new Date(row.created_at).toLocaleString();
        document.getElementById("modal-score").textContent =
            `${row.score} / ${row.total_questions}`;

        const pctEl = document.getElementById("modal-grade-pct");
        pctEl.textContent = `${row.percentage}%`;
        if (row.percentage >= 75) {
            pctEl.style.background = "linear-gradient(135deg,var(--success),#34d399)";
        } else if (row.percentage >= 50) {
            pctEl.style.background = "linear-gradient(135deg,var(--warning),#fbbf24)";
        } else {
            pctEl.style.background = "linear-gradient(135deg,var(--danger),#f87171)";
        }

        // ── Original notes ──
        document.getElementById("modal-notes-content").textContent =
            row.note_content || "Notes content not available.";

        // ── Overall feedback ──
        const grading = row.detailed_grading || {};
        document.getElementById("modal-overall-feedback").textContent =
            grading.overall_feedback || row.feedback || "No feedback recorded.";

        // ── Recommendations ──
        const recsList = document.getElementById("modal-recommendations");
        recsList.innerHTML = "";
        const recs = grading.recommendations || [];
        if (recs.length === 0) {
            recsList.innerHTML = "<li style='color:var(--text-muted);font-style:italic'>No recommendations recorded.</li>";
        } else {
            recs.forEach(r => {
                const li = document.createElement("li");
                li.innerHTML = `<i class="fa-solid fa-angles-right"></i><span>${escapeHtml(r)}</span>`;
                recsList.appendChild(li);
            });
        }

        // ── Question breakdown ──
        const breakdown = document.getElementById("modal-questions-breakdown");
        breakdown.innerHTML = "";

        const questions        = row.questions        || [];
        const userAnswers      = row.answers          || {};
        const explanations     = grading.question_explanations || {};
        const gradedQuestions  = grading.graded_questions      || [];

        if (questions.length === 0) {
            breakdown.innerHTML = "<p style='color:var(--text-muted);font-style:italic'>Question details not available for this attempt.</p>";
        } else {
            questions.forEach((q, qi) => {
                // Resolve user answer index — may come from graded_questions or raw answers map
                const gradedQ = gradedQuestions.find(gq => gq.id === q.id) || {};
                const userIdx = gradedQ.user_answer !== undefined
                    ? gradedQ.user_answer
                    : (userAnswers[q.id] !== undefined ? parseInt(userAnswers[q.id]) : -1);
                const correctIdx  = q.answer;
                const isCorrect   = (userIdx === correctIdx);
                const explanation = explanations[q.id] || "";

                const item = document.createElement("div");
                item.className = "feedback-explain-item";

                // Question header + badge
                const qHeader = document.createElement("div");
                qHeader.className = "explain-q-header";
                qHeader.innerHTML = `
                    <h4>${qi + 1}. ${escapeHtml(q.question)}</h4>
                    <span class="explain-badge ${isCorrect ? 'correct' : 'incorrect'}">
                        ${isCorrect
                            ? '<i class="fa-solid fa-circle-check"></i> Correct'
                            : '<i class="fa-solid fa-circle-xmark"></i> Incorrect'}
                    </span>`;
                item.appendChild(qHeader);

                // Options
                const optView = document.createElement("div");
                optView.className = "explain-options-view";
                (q.options || []).forEach((opt, idx) => {
                    let cls    = "explain-opt other-option";
                    let prefix = "";
                    if (idx === correctIdx) {
                        cls    = "explain-opt target-correct";
                        prefix = "<i class='fa-solid fa-check'></i> ";
                    } else if (idx === userIdx && !isCorrect) {
                        cls    = "explain-opt chosen-wrong";
                        prefix = "<i class='fa-solid fa-xmark'></i> ";
                    }
                    const d = document.createElement("div");
                    d.className = cls;
                    d.innerHTML = `${prefix}${escapeHtml(opt)}`;
                    optView.appendChild(d);
                });
                item.appendChild(optView);

                // Explanation
                if (explanation) {
                    const desc = document.createElement("div");
                    desc.className = "explain-desc";
                    desc.innerHTML = `<strong>Grader Explains:</strong> ${escapeHtml(explanation)}`;
                    item.appendChild(desc);
                }

                breakdown.appendChild(item);
            });
        }

        // ── Show modal ──
        attemptModal.classList.remove("hide");
        document.body.style.overflow = "hidden";
    }

    function closeAttemptModal() {
        attemptModal.classList.add("hide");
        document.body.style.overflow = "";
    }

    btnCloseModal.addEventListener("click", closeAttemptModal);

    // Close on backdrop click
    attemptModal.addEventListener("click", e => {
        if (e.target === attemptModal) closeAttemptModal();
    });

    // Close on Escape key
    document.addEventListener("keydown", e => {
        if (e.key === "Escape" && !attemptModal.classList.contains("hide")) {
            closeAttemptModal();
        }
    });
    // ── End Modal ───────────────────────────────────────────────────────────
});
