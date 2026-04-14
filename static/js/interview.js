(function () {
    const answerInput = document.getElementById("answer-input");
    const thinkTimeInput = document.getElementById("think_time");
    const voiceBtn = document.getElementById("voice-btn");
    const voiceStatus = document.getElementById("voice-status");
    const cameraBtn = document.getElementById("camera-btn");
    const cameraStatus = document.getElementById("camera-status");
    const cameraPreview = document.getElementById("camera-preview");
    const canvas = document.getElementById("capture-canvas");
    const answerForm = document.getElementById("answer-form");
    const elapsedEl = document.getElementById("interview-elapsed");
    const countdownEl = document.getElementById("question-countdown");

    if (!answerInput || !thinkTimeInput) return;

    const loadTime = Date.now();
    let thinkCaptured = false;
    let questionSecondsLeft = 120;

    const formatTime = (total) => {
        const m = Math.floor(total / 60).toString().padStart(2, "0");
        const s = Math.floor(total % 60).toString().padStart(2, "0");
        return `${m}:${s}`;
    };

    if (elapsedEl || countdownEl) {
        const timer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - loadTime) / 1000);
            if (elapsedEl) elapsedEl.textContent = formatTime(elapsed);

            questionSecondsLeft = Math.max(0, 120 - elapsed);
            if (countdownEl) {
                countdownEl.textContent = formatTime(questionSecondsLeft);
                countdownEl.parentElement.classList.toggle("timer-warning", questionSecondsLeft <= 20);
            }
        }, 1000);

        if (answerForm) {
            answerForm.addEventListener("submit", () => clearInterval(timer));
        }
    }

    const captureThinkTime = () => {
        if (!thinkCaptured) {
            const seconds = (Date.now() - loadTime) / 1000;
            thinkTimeInput.value = seconds.toFixed(2);
            thinkCaptured = true;
        }
    };

    answerInput.addEventListener("focus", captureThinkTime, { once: true });
    answerInput.addEventListener("keydown", captureThinkTime, { once: true });

    if (voiceBtn && "webkitSpeechRecognition" in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";
        let recording = false;

        recognition.onresult = (event) => {
            let transcript = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            answerInput.value = transcript.trim();
            captureThinkTime();
        };

        recognition.onend = () => {
            if (recording) {
                recognition.start();
            }
        };

        voiceBtn.addEventListener("click", () => {
            if (!recording) {
                recognition.start();
                recording = true;
                voiceBtn.textContent = "Stop Voice Input";
                voiceStatus.textContent = "Listening...";
            } else {
                recording = false;
                recognition.stop();
                voiceBtn.textContent = "Start Voice Input";
                voiceStatus.textContent = "Voice capture stopped.";
            }
        });
    } else if (voiceBtn) {
        voiceBtn.disabled = true;
        voiceStatus.textContent = "Speech recognition not supported in this browser.";
    }

    if (cameraBtn && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        let stream = null;

        const startCamera = async () => {
            if (stream) return true;
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                cameraPreview.srcObject = stream;
                cameraPreview.classList.remove("hidden");
                cameraBtn.textContent = "Analyze Confidence";
                cameraStatus.textContent = "Camera is live during this interview.";
                return true;
            } catch (err) {
                cameraStatus.textContent = "Camera access failed.";
                return false;
            }
        };

        startCamera();

        cameraBtn.addEventListener("click", async () => {
            try {
                const ready = await startCamera();
                if (!ready) {
                    return;
                }

                const width = 320;
                const height = 240;
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(cameraPreview, 0, 0, width, height);

                const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
                const formData = new FormData();
                formData.append("frame", blob, "frame.jpg");

                const res = await fetch(window.interviewContext.confidenceApi, {
                    method: "POST",
                    body: formData
                });
                const data = await res.json();
                cameraStatus.textContent = `Confidence check: ${data.confidence}% - ${data.message}`;
            } catch (err) {
                cameraStatus.textContent = "Camera access failed.";
            }
        });
    } else if (cameraBtn) {
        cameraBtn.disabled = true;
        cameraStatus.textContent = "Camera API not supported.";
    }
})();
