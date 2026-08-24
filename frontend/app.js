// Base URL for all backend API calls
const serverBase = "http://localhost:8000/api";


/**
 * Convert backend sentiment labels into display text for the UI.
 */
function toneLabel(raw) {
  const toneMap = {
    POSITIVE: "Positive tone",
    NEUTRAL:  "Neutral tone",
    NEGATIVE: "Negative tone",
  };
  return toneMap[raw] || raw;
}

// Interview session state
let questionBank = [];
let questionIndex = 0;
let sessionResults = [];
let recorder = null;
let audioBuffer = [];
let recordingActive = false;
let hasRecording = false;

// Eye contact tracking state
let gazeOk = 0;
let gazeTotal = 0;
let gazeRunning = false;
let gazeScore = null;
let camStream = null;
let mpCamLoop = null;
let mpFace = null;

// Cache commonly used DOM elements for performance
const pageScreens = {
  jd:        document.getElementById("screen-jd"),
  interview: document.getElementById("screen-interview"),
  report:    document.getElementById("screen-report"),
};
const loadOverlay = document.getElementById("loading");
const loadText    = document.getElementById("loading-msg");
const camFeed     = document.getElementById("cam-feed");
const camWrap     = document.getElementById("cam-wrap");
const gazeBadge   = document.getElementById("gaze-badge");

/**
 * Show one screen and hide the others.
 */
function switchScreen(name) {
  Object.values(pageScreens).forEach(s => s.classList.add("hidden"));
  pageScreens[name].classList.remove("hidden");
}

/**
 * Show the loading overlay with a custom message.
 */

function showSpinner(msg = "Processing...") {
  loadText.textContent = msg;
  loadOverlay.classList.remove("hidden");
}

/**
 * Hide the loading overlay.
 */
function hideSpinner() {
  loadOverlay.classList.add("hidden");
}

/**
 * Display an error message in a specified element.
 */
function displayError(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent = msg;
  el.classList.remove("hidden");
}

/**
 * Clear an error message from a specified element.
 */
function clearError(elId) {
  const el = document.getElementById(elId);
  el.textContent = "";
  el.classList.add("hidden");
}

/**
 * Send a POST request to the backend.
 * A timeout is used so the UI does not hang indefinitely.
 */
async function postRequest(path, payload, multipart = false) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120000);
  const cfg = { method: "POST", signal: controller.signal };
  if (multipart) {
    cfg.body = payload;
  } else {
    cfg.headers = { "Content-Type": "application/json" };
    cfg.body = JSON.stringify(payload);
  }
  try {
    const resp = await fetch(`${serverBase}${path}`, cfg);
    clearTimeout(timer);
    if (!resp.ok) {
      const errBody = await resp.json().catch(() => ({ detail: `${resp.status} ${resp.statusText}` }));
      throw new Error(errBody.detail || "Unknown error");
    }
    return resp.json();
  } catch (e) {
    clearTimeout(timer);
    if (e.name === "AbortError") throw new Error("Request timed out. Ollama may be overloaded.");
    throw e;
  }
}

/**
 * Calculate horizontal iris position ratio between two eye corner landmarks.
 * Returns a value from roughly 0 to 1.
 */
function hRatio(a, b, iris) {
  const lo = Math.min(a.x, b.x);
  const hi = Math.max(a.x, b.x);
  const w = hi - lo;
  if (w < 0.001) return 0.5;
  return (iris.x - lo) / w;
}

/**
 * Calculate vertical iris position ratio between upper and lower eyelid landmarks.
 * Returns a value from roughly 0 to 1.
 */
function vRatio(top, bot, iris) {
  const lo = Math.min(top.y, bot.y);
  const hi = Math.max(top.y, bot.y);
  const h = hi - lo;
  if (h < 0.001) return 0.5;
  return (iris.y - lo) / h;
}

/**
 * Callback run every time MediaPipe returns face landmarks.
 * It checks whether the user appears to be looking toward the camera.
 */
function onFaceFrame(data) {
  if (!gazeRunning) return;
  gazeTotal++;

  // No face detected in this frame
  if (!data.multiFaceLandmarks || data.multiFaceLandmarks.length === 0) {
    setBadge(false);
    return;
  }

  const lm = data.multiFaceLandmarks[0];

  // If iris landmarks are missing, treat as acceptable fallback
  if (lm.length < 474) {
    gazeOk++;
    setBadge(true);
    return;
  }

  try {
    const hl = hRatio(lm[33],  lm[133], lm[468]);
    const hr = hRatio(lm[263], lm[362], lm[473]);
    const vl = vRatio(lm[159], lm[145], lm[468]);
    const vr = vRatio(lm[386], lm[374], lm[473]);

    const leftOk  = hl >= 0.35 && hl <= 0.65 && vl >= 0.20 && vl <= 0.55;
    const rightOk = hr >= 0.35 && hr <= 0.65 && vr >= 0.20 && vr <= 0.55;

    if (leftOk && rightOk) gazeOk++;
    setBadge(leftOk && rightOk);
  } catch (e) {
    setBadge(false);
  }
}


/**
 * Update the on-screen eye contact badge.
 */
function setBadge(looking) {
  if (looking) {
    gazeBadge.textContent = "👁 Eye contact ✓";
    gazeBadge.style.background = "rgba(21, 128, 61, 0.85)";
  } else {
    gazeBadge.textContent = "👁 Look at camera";
    gazeBadge.style.background = "rgba(185, 28, 28, 0.85)";
  }
}


/**
 * Start webcam capture and begin MediaPipe eye contact tracking.
 */
async function startGaze() {
  gazeOk = 0;
  gazeTotal = 0;
  gazeScore = null;
  gazeRunning = true;

  try {
    camStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: "user" },
      audio: false,
    });
    camFeed.srcObject = camStream;
    await new Promise(r => { camFeed.onloadedmetadata = r; });
    await camFeed.play();
    camWrap.classList.remove("hidden");

    mpCamLoop = new Camera(camFeed, {
      onFrame: async () => {
        if (gazeRunning) await mpFace.send({ image: camFeed });
      },
      width: 640,
      height: 480,
    });
    await mpCamLoop.start();
  } catch (e) {
    gazeRunning = false;
  }
}


/**
 * Stop eye contact tracking and compute the final eye contact score.
 */
function stopGaze() {
  gazeRunning = false;

  if (mpCamLoop) { mpCamLoop.stop(); mpCamLoop = null; }
  if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; }

  camFeed.srcObject = null;
  camWrap.classList.add("hidden");

  gazeScore = gazeTotal > 0
    ? Math.round((gazeOk / gazeTotal) * 100) / 10
    : null;

  gazeBadge.textContent = "👁 Detecting...";
  gazeBadge.style.background = "rgba(0,0,0,0.7)";
}


/**
 * Initialise MediaPipe FaceMesh for browser-based face landmark detection.
 */
function initFaceDetector() {
  mpFace = new FaceMesh({
    locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`
  });
  mpFace.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5,
  });
  mpFace.onResults(onFaceFrame);
}


/**
 * Generate interview questions from the pasted job description.
 */
document.getElementById("btn-generate").addEventListener("click", async () => {
  clearError("jd-error");
  const jdText = document.getElementById("jd-input").value.trim();
  if (!jdText) { displayError("jd-error", "Please paste a job description."); return; }

  const numQuestions = parseInt(document.getElementById("num-questions").value, 10);
  const selectedTypes = Array.from(document.querySelectorAll(".type-checkboxes input:checked")).map(el => el.value);
  if (selectedTypes.length === 0) { displayError("jd-error", "Select at least one question type."); return; }

  showSpinner("Generating questions...");
  try {
    const resp = await postRequest("/generate-questions", {
      job_description: jdText,
      num_questions: numQuestions,
      question_types: selectedTypes,
    });
    questionBank = resp.questions;
    questionIndex = 0;
    sessionResults = [];
    loadNextQuestion();
    switchScreen("interview");
  } catch (e) {
    displayError("jd-error", e.message);
  } finally {
    hideSpinner();
  }
});


/**
 * Load the current interview question into the UI.
 * Also resets previous transcript and recording state.
 */
function loadNextQuestion() {
  const current = questionBank[questionIndex];
  document.getElementById("question-counter").textContent = `Question ${questionIndex + 1} of ${questionBank.length}`;
  document.getElementById("question-text").textContent = current.question;
  const typeBox = document.getElementById("question-type-box");
  if (typeBox) {
    if (current.type && current.type !== "General") {
      typeBox.textContent = current.type;
      typeBox.classList.remove("hidden");
    } else {
      typeBox.textContent = "";
      typeBox.classList.add("hidden");
    }
  }
  document.getElementById("transcript-box").classList.add("hidden");
  document.getElementById("transcript-text").textContent = "";
  document.getElementById("btn-submit-answer").classList.add("hidden");
  clearError("interview-error");
  resetAudio();
}


/**
 * Toggle recording on/off when the record button is clicked.
 */
document.getElementById("btn-record").addEventListener("click", async () => {
  if (recordingActive) {
    stopAudio();
  } else {
    await startAudio();
  }
});


/**
 * Start microphone recording and eye contact tracking together.
 */
async function startAudio() {
  try {
    const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioBuffer = [];
    recorder = new MediaRecorder(micStream);
    recorder.ondataavailable = e => audioBuffer.push(e.data);
    recorder.onstop = onAudioDone;
    recorder.start();
    recordingActive = true;

    document.getElementById("transcript-box").classList.add("hidden");
    document.getElementById("btn-submit-answer").classList.add("hidden");

    const btn = document.getElementById("btn-record");
    btn.textContent = "⏹ Stop Recording";
    btn.classList.add("recording");
    document.getElementById("record-status").textContent = "Recording...";

    await startGaze();
  } catch (e) {
    displayError("interview-error", "Microphone access denied. Please allow microphone use.");
  }
}


/**
 * Stop the audio recorder and stop eye contact tracking.
 */
function stopAudio() {
  if (recorder && recorder.state !== "inactive") {
    recorder.stop();
    recorder.stream.getTracks().forEach(t => t.stop());
  }
  recordingActive = false;

  const btn = document.getElementById("btn-record");
  btn.textContent = hasRecording ? "🔁 Re-record" : "🎤 Start Recording";
  btn.classList.remove("recording");
  document.getElementById("record-status").textContent = "Processing...";

  stopGaze();
}


/**
 * Reset recording-related UI and state before the next question.
 */
function resetAudio() {
  recordingActive = false;
  audioBuffer = [];
  gazeScore = null;
  hasRecording = false;
  const btn = document.getElementById("btn-record");
  btn.textContent = "🎤 Start Recording";
  btn.classList.remove("recording");
  document.getElementById("record-status").textContent = "";
}


/**
 * Called after recording stops.
 * Sends the recorded audio to the backend for transcription.
 */
async function onAudioDone() {
  document.getElementById("record-status").textContent = "Transcribing...";

  const clip = new Blob(audioBuffer, { type: "audio/webm" });
  const fd = new FormData();
  fd.append("file", clip, "answer.webm");

  try {
    const resp = await postRequest("/transcribe", fd, true);
    const text = resp.transcript;

    if (!text || !text.trim()) {
      displayError("interview-error", "No speech detected. Please try recording again.");
      document.getElementById("record-status").textContent = "";
      return;
    }

    document.getElementById("transcript-text").textContent = text;
    document.getElementById("transcript-box").classList.remove("hidden");
    document.getElementById("btn-submit-answer").classList.remove("hidden");
    document.getElementById("record-status").textContent = "Done.";
    document.getElementById("btn-submit-answer").dataset.transcript = text;

    hasRecording = true;
    document.getElementById("btn-record").textContent = "🔁 Re-record";
  } catch (e) {
    displayError("interview-error", `Transcription failed: ${e.message}`);
    document.getElementById("record-status").textContent = "";
  }
}


/**
 * Submit the current answer for evaluation and sentiment analysis.
 * Eye contact score is included with the result for final aggregation.
 */
document.getElementById("btn-submit-answer").addEventListener("click", async () => {
  clearError("interview-error");
  const transcript = document.getElementById("btn-submit-answer").dataset.transcript;
  const qText = questionBank[questionIndex].question;
  const qType = questionBank[questionIndex].type;
  const eyeResult = gazeScore;

  showSpinner("Evaluating answer...");
  try {
    const [evalResult, toneResult] = await Promise.all([
      postRequest("/evaluate", { question: qText, transcript, question_type: qType }),
      postRequest("/sentiment", { transcript }),
    ]);

    sessionResults.push({
      question: qText,
      question_type: qType,
      transcript,
      evaluation: evalResult,
      sentiment: toneResult,
      eye_contact_score: eyeResult,
    });

    questionIndex++;
    if (questionIndex < questionBank.length) {
      loadNextQuestion();
    } else {
      await buildReport();
    }
  } catch (e) {
    displayError("interview-error", `Evaluation failed: ${e.message}`);
  } finally {
    hideSpinner();
  }
});


/**
 * Request the final aggregated report from the backend.
 * Falls back to frontend aggregation if backend report generation fails.
 */
async function buildReport() {
  showSpinner("Generating final report...");
  try {
    const summary = await postRequest("/final-report", { results: sessionResults });
    summary.per_question = sessionResults;
    summary.avg_eye_contact = avgGaze(sessionResults);
    summary.avg_sentiment_score = summary.avg_sentiment_score ?? calcAvgSentiment(sessionResults);
    drawReport(summary);
    switchScreen("report");
  } catch (e) {
    const summary = fallbackAggregate(sessionResults);
    drawReport(summary);
    switchScreen("report");
  } finally {
    hideSpinner();
  }
}

/**
 * Compute average sentiment score across all answered questions.
 */
function calcAvgSentiment(data) {
  const scores = data.map(r => sentimentToScore(r.sentiment.label, r.sentiment.confidence));
  if (!scores.length) return null;
  return Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10;
}

/**
 * Compute average eye contact score across all answered questions.
 */
function avgGaze(data) {
  const valid = data.map(r => r.eye_contact_score).filter(s => s !== null && s !== undefined);
  if (!valid.length) return null;
  return Math.round((valid.reduce((a, b) => a + b, 0) / valid.length) * 10) / 10;
}


/**
 * Convert sentiment label and confidence into a score out of 10.
 */
function sentimentToScore(label, confidence) {
  const base = { POSITIVE: 10, NEUTRAL: 5, NEGATIVE: 0 };
  return Math.round((base[label] ?? 5) * confidence * 10) / 10;
}


/**
 * Frontend fallback aggregation used only if backend final-report fails.
 * Recomputes averages and weighted final score locally.
 */
function fallbackAggregate(data) {
  const keys = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"];
  const sums = Object.fromEntries(keys.map(k => [k, 0]));
  let weightedTotal = 0;
  const tones = [];

  data.forEach(r => {
    keys.forEach(k => { sums[k] += r.evaluation[k].score; });
    const sScore = sentimentToScore(r.sentiment.label, r.sentiment.confidence);
    const eyeVal = r.eye_contact_score ?? null;
    const eyeWeightUsed = eyeVal !== null ? 0.10 : 0;
    const llmScale = (1.0 - 0.10 - eyeWeightUsed) / 0.80;
    const weighted = (
      r.evaluation.relevance.score           * 0.20 * llmScale +
      r.evaluation.content_depth.score       * 0.20 * llmScale +
      r.evaluation.clarity_structure.score   * 0.20 * llmScale +
      r.evaluation.confidence_delivery.score * 0.20 * llmScale +
      sScore                                 * 0.10 +
      (eyeVal ?? 0)                          * eyeWeightUsed
    );
    weightedTotal += weighted;
    tones.push(r.sentiment.label);
  });

  const n = data.length;
  return {
    per_question:            data,
    avg_relevance:           +(sums.relevance / n).toFixed(1),
    avg_content_depth:       +(sums.content_depth / n).toFixed(1),
    avg_clarity_structure:   +(sums.clarity_structure / n).toFixed(1),
    avg_confidence_delivery: +(sums.confidence_delivery / n).toFixed(1),
    avg_sentiment_score:     calcAvgSentiment(data),
    avg_eye_contact:         avgGaze(data),
    final_overall_score:     +(weightedTotal / n).toFixed(1),
    dominant_sentiment: tones.sort((a, b) =>
      tones.filter(v => v === b).length - tones.filter(v => v === a).length
    )[0],
  };
}


/**
 * Escape text before inserting it into innerHTML.
 * This prevents HTML from being interpreted directly.
 */
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Format eye contact score for display.
 */
function fmtEye(val) {
  return (val === null || val === undefined) ? "N/A" : `${val}/10`;
}

/**
 * Render the final report screen, including summary scores
 * and detailed results for each interview question.
 */
function drawReport(data) {
  const eyeAvg = data.avg_eye_contact;

  document.getElementById("report-summary").innerHTML = `
    <h2>Overall Results</h2>
    <div class="score-row"><span>Relevance <span class="weight-tag">20%</span></span><span class="val">${data.avg_relevance}/10</span></div>
    <div class="score-row"><span>Content Depth <span class="weight-tag">20%</span></span><span class="val">${data.avg_content_depth}/10</span></div>
    <div class="score-row"><span>Clarity &amp; Structure <span class="weight-tag">20%</span></span><span class="val">${data.avg_clarity_structure}/10</span></div>
    <div class="score-row"><span>Confidence Delivery <span class="weight-tag">20%</span></span><span class="val">${data.avg_confidence_delivery}/10</span></div>
    <div class="score-row"><span>Sentiment <span class="weight-tag">10%</span></span><span class="val">${data.avg_sentiment_score !== undefined ? data.avg_sentiment_score + '/10' : 'N/A'}</span></div>
    <div class="score-row"><span>Eye Contact <span class="weight-tag">10%</span></span><span class="val">${fmtEye(eyeAvg)}</span></div>
    <div class="score-row final-score"><span>Final Weighted Score</span><span class="val">${data.final_overall_score}/10</span></div>
    <div class="score-row"><span>Answer Tone</span>
      <span class="sentiment-tag ${data.dominant_sentiment}">${toneLabel(data.dominant_sentiment)}</span>
    </div>
  `;

  const wrap = document.getElementById("report-questions");
  wrap.innerHTML = "";

  const perQ = data.per_question || sessionResults;
  perQ.forEach((item, idx) => {
    const ev = item.evaluation;
    const se = item.sentiment;

    const dimList = [
      { key: "relevance",           label: "Relevance" },
      { key: "content_depth",       label: "Content Depth" },
      { key: "clarity_structure",   label: "Clarity & Structure" },
      { key: "confidence_delivery", label: "Confidence Delivery" },
    ];

    const dimRows = dimList.map(d => `
      <div class="dim-row">
        <div class="dim-header">
          <span>${d.label}</span>
          <span>${ev[d.key].score}/10</span>
        </div>
        <div class="rationale">${escapeHtml(ev[d.key].rationale)}</div>
      </div>
    `).join("");

    wrap.innerHTML += `
      <div class="question-result">
        <h3>Q${idx + 1}: ${escapeHtml(item.question)}${item.question_type !== "General" ? ` <span class="type-tag">(${item.question_type})</span>` : ""}</h3>
        <p class="transcript-preview">"${escapeHtml(item.transcript)}"</p>
        ${dimRows}
        <div class="result-footer">
          <div class="tone-row">
            <span class="sentiment-tag ${se.label}">${toneLabel(se.label)}</span>
            <strong class="overall-score">Overall: ${ev.overall_score}/10</strong>
          </div>
          <div class="sentiment-score-row">
            <span class="eye-score-tag">Sentiment: ${sentimentToScore(se.label, se.confidence)}/10</span>
          </div>
          <div class="eye-contact-row">
            <span class="eye-score-tag">👁 Eye Contact: ${fmtEye(item.eye_contact_score)}</span>
          </div>
        </div>
      </div>
    `;
  });
}

/**
 * Reset the whole session and return the user to the JD input screen.
 */
document.getElementById("btn-restart").addEventListener("click", () => {
  questionBank = [];
  questionIndex = 0;
  sessionResults = [];
  gazeScore = null;
  document.getElementById("jd-input").value = "";
  clearError("jd-error");
  switchScreen("jd");
});

// Initialise MediaPipe FaceMesh when the page loads
initFaceDetector();
