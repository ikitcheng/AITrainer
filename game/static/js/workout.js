// workout.js
// This script auto-detects when the person is in the box and starts the workout with a countdown

document.addEventListener('DOMContentLoaded', function() {
    const workoutConfig = JSON.parse(localStorage.getItem('workoutConfig'));
    let ws = null;
    let stream = null;
    let inBoxFrames = 0;
    let countdownStarted = false;
    let countdownTimeout = null;
    const REQUIRED_FRAMES = 10; // Number of consecutive frames in box before countdown
    const COUNTDOWN_SECONDS = 3;

    // Get DOM elements
    const instructions = document.getElementById('instructions');
    const cameraContainer = document.getElementById('cameraContainer');
    const statsContainer = document.getElementById('statsContainer');
    const video = document.getElementById('camera-feed');
    const positionBox = document.querySelector('.position-box');

    // Get the box coordinates relative to the video
    function getBoxCoords() {
        const rect = positionBox.getBoundingClientRect();
        const videoRect = video.getBoundingClientRect();
        // Calculate box coordinates relative to the video element
        const x1 = Math.max(0, rect.left - videoRect.left);
        const y1 = Math.max(0, rect.top - videoRect.top);
        const x2 = Math.min(videoRect.width, rect.right - videoRect.left);
        const y2 = Math.min(videoRect.height, rect.bottom - videoRect.top);
        return { x1: Math.round(x1), y1: Math.round(y1), x2: Math.round(x2), y2: Math.round(y2) };
    }

    // Show countdown overlay
    function showCountdown(number) {
        let overlay = document.querySelector('.countdown-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'countdown-overlay';
            document.body.appendChild(overlay);
        }
        overlay.innerHTML = `<div class="countdown-number">${number}</div>`;
    }
    function removeCountdown() {
        const overlay = document.querySelector('.countdown-overlay');
        if (overlay) overlay.remove();
    }

    // Start workout
    function startWorkout(config) {
        instructions.style.display = 'none';
        cameraContainer.style.display = 'block';
        statsContainer.style.display = 'grid';
    }

    // Update stats
    function updateReps(value) {
        document.getElementById('repCount').textContent = value;
    }
    function updateTimer(value) {
        document.getElementById('timer').textContent = value;
    }
    function updatePower(value) {
        document.getElementById('powerOutput').textContent = value;
    }

    // End workout
    function endWorkout(data) {
        // Store results
        localStorage.setItem('workoutResults', JSON.stringify(data.results || {}));
        // Redirect to results page
        window.location.href = '/results';
    }

    // Initialize WebSocket connection
    function initWebSocket() {
        ws = new WebSocket(`ws://${window.location.host}/ws/${Date.now()}`);
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            switch(data.type) {
                case 'countdown':
                    showCountdown(data.value);
                    break;
                case 'workout_start':
                    removeCountdown();
                    startWorkout(data.config);
                    break;
                case 'rep_update':
                    updateReps(data.value);
                    break;
                case 'timer_update':
                    updateTimer(data.value);
                    break;
                case 'power_update':
                    updatePower(data.value);
                    break;
                case 'workout_end':
                    endWorkout(data);
                    break;
            }
        };
    }

    // Send a frame to the backend to check if person is in the box
    async function checkPersonInBox() {
        if (!video.videoWidth || !video.videoHeight) return;
        // Draw current video frame to canvas
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const { x1, y1, x2, y2 } = getBoxCoords();
        // Convert canvas to blob
        canvas.toBlob(async function(blob) {
            const formData = new FormData();
            formData.append('file', blob, 'frame.jpg');
            formData.append('x1', x1);
            formData.append('y1', y1);
            formData.append('x2', x2);
            formData.append('y2', y2);
            try {
                const resp = await fetch('/api/check-in-box', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();
                if (data.in_box) {
                    inBoxFrames++;
                    if (inBoxFrames >= REQUIRED_FRAMES && !countdownStarted) {
                        countdownStarted = true;
                        let count = COUNTDOWN_SECONDS;
                        showCountdown(count);
                        countdownTimeout = setInterval(() => {
                            count--;
                            if (count > 0) {
                                showCountdown(count);
                            } else {
                                removeCountdown();
                                clearInterval(countdownTimeout);
                                // Start workout
                                initWebSocket();
                                ws.onopen = function() {
                                    ws.send(JSON.stringify({
                                        type: 'start_workout',
                                        data: workoutConfig
                                    }));
                                };
                            }
                        }, 1000);
                    }
                } else {
                    inBoxFrames = 0;
                    if (!countdownStarted) removeCountdown();
                }
            } catch (err) {
                // Ignore errors for now
            }
        }, 'image/jpeg', 0.85);
    }

    // Initialize camera and start checking
    async function initCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.transform = 'scaleX(-1)';
            video.onloadedmetadata = () => {
                video.play();
                // Start checking every 300ms
                setInterval(checkPersonInBox, 300);
            };
        } catch (err) {
            alert('Error accessing camera. Please make sure you have granted camera permissions.');
        }
    }

    // Start camera immediately
    initCamera();
}); 