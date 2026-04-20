let chart;

let counts = {
    happy: 0,
    sad: 0,
    neutral: 0,
    stressed: 0,
    surprised: 0,
    angry: 0
};

function playSound() {
    const audio = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg");
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

    playSound();
    updateChart();
}

function updateChart() {
    const ctx = document.getElementById("chart").getContext("2d");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ["Happy","Sad","Neutral","Stressed","Surprised","Angry"],
            datasets: [{
                label: "Emotion Count",
                data: Object.values(counts)
            }]
        }
    });
}







// Emotion animation
setInterval(() => {
    const emotions = ["Calm", "Happy", "Neutral"];
    document.querySelector(".status b").innerText =
        emotions[Math.floor(Math.random()*3)];
}, 3000);


// Particle animation
const canvas = document.getElementById("particles");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let particles = [];

for (let i = 0; i < 80; i++) {
    particles.push({
        x: Math.random()*canvas.width,
        y: Math.random()*canvas.height,
        dx: Math.random()*1,
        dy: Math.random()*1
    });
}

function animate() {
    ctx.clearRect(0,0,canvas.width,canvas.height);

    particles.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2, 0, Math.PI*2);
        ctx.fillStyle = "#00ffff";
        ctx.fill();

        p.x += p.dx;
        p.y += p.dy;

        if(p.x > canvas.width) p.x = 0;
        if(p.y > canvas.height) p.y = 0;
    });

    requestAnimationFrame(animate);
}

animate();