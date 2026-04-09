let chart;

let counts = {
    happy: 0,
    sad: 0,
    neutral: 0,
    stressed: 0,
    surprised: 0,
    angry: 0
};

// 🔊 SOUND ALERT (FIXED)
function playSound() {
    const audio = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg");
    audio.volume = 1;
    audio.play().catch(() => {});
}

function detectEmotion() {
    fetch('/detect_emotion')
    .then(res => res.json())
    .then(data => handleResponse(data));
}

function voiceEmotion() {
    fetch('/voice_emotion')
    .then(res => res.json())
    .then(data => handleResponse(data));
}

function handleResponse(data) {
    if (data.error) {
        document.getElementById("result").innerText = data.error;
        return;
    }

    let emotion = data.emotion;

    document.getElementById("result").innerText = emotion;
    document.getElementById("suggestion").innerText = data.suggestion;

    if (!counts[emotion]) counts[emotion] = 0;
        counts[emotion]++;

    // 🔥 ALERT FOR ALL EMOTIONS
    playSound();

    if (["sad", "angry", "stressed"].includes(emotion)) {
        alert("⚠ Attention: You are " + emotion);
}

    updateChart();
}

function updateChart() {
    const ctx = document.getElementById("chart").getContext("2d");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ["Happy", "Sad", "Neutral", "Stressed", "Surprised", "Angry"],
            datasets: [{
                label: "Emotion Count",
                data: [
                    counts.happy,
                    counts.sad,
                    counts.neutral,
                    counts.stressed,
                    counts.surprised,
                    counts.angry
                ]
            }]
        }
    });
}