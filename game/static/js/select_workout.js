// select_workout.js
// roundSlider CDN should be included in the template for this to work

document.addEventListener('DOMContentLoaded', function() {
    let selectedExercise = localStorage.getItem('selectedExercise') || null;
    let selectedMode = localStorage.getItem('selectedMode') || 'timed';
    let selectedMinutes = parseInt(localStorage.getItem('selectedMinutes')) || 1;
    let selectedSeconds = parseInt(localStorage.getItem('selectedSeconds')) || 0;
    let selectedReps = parseInt(localStorage.getItem('selectedReps')) || 10;
    let cameraStream = null;

    // Initialize exercise cards
    document.querySelectorAll('.exercise-card').forEach(card => {
        card.addEventListener('click', function() {
            selectedExercise = this.dataset.exercise;
            localStorage.setItem('selectedExercise', selectedExercise);
            document.querySelectorAll('.exercise-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            document.getElementById('modeSelection').classList.add('active');
        });
        // Restore selection
        if (card.dataset.exercise === selectedExercise) {
            card.classList.add('active');
            document.getElementById('modeSelection').classList.add('active');
        }
    });

    // Initialize mode tabs
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            selectedMode = this.dataset.mode;
            localStorage.setItem('selectedMode', selectedMode);
            document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            document.getElementById('timedMode').style.display = selectedMode === 'timed' ? 'block' : 'none';
            document.getElementById('repsMode').style.display = selectedMode === 'reps' ? 'block' : 'none';
        });
        // Restore selection
        if (tab.dataset.mode === selectedMode) {
            tab.classList.add('active');
            document.getElementById('timedMode').style.display = selectedMode === 'timed' ? 'block' : 'none';
            document.getElementById('repsMode').style.display = selectedMode === 'reps' ? 'block' : 'none';
        }
    });

    // roundSlider wheels
    $("#minutesWheel").roundSlider({
        radius: 100,
        width: 20,
        handleSize: 20,
        handleShape: "round",
        sliderType: "min-range",
        value: selectedMinutes,
        min: 0,
        max: 10,
        step: 1,
        change: function(e) {
            selectedMinutes = e.value;
            localStorage.setItem('selectedMinutes', selectedMinutes);
        }
    });
    $("#secondsWheel").roundSlider({
        radius: 100,
        width: 20,
        handleSize: 20,
        handleShape: "round",
        sliderType: "min-range",
        value: selectedSeconds,
        min: 0,
        max: 59,
        step: 1,
        change: function(e) {
            selectedSeconds = e.value;
            localStorage.setItem('selectedSeconds', selectedSeconds);
        }
    });
    $("#repsWheel").roundSlider({
        radius: 100,
        width: 20,
        handleSize: 20,
        handleShape: "round",
        sliderType: "min-range",
        value: selectedReps,
        min: 1,
        max: 100,
        step: 1,
        change: function(e) {
            selectedReps = e.value;
            localStorage.setItem('selectedReps', selectedReps);
        }
    });

    // Restore wheel values visually
    $("#minutesWheel").roundSlider("setValue", selectedMinutes);
    $("#secondsWheel").roundSlider("setValue", selectedSeconds);
    $("#repsWheel").roundSlider("setValue", selectedReps);

    // Camera initialization after pressing Start Workout
    document.getElementById('startWorkoutBtn').addEventListener('click', async function() {
        if (!selectedExercise) return;
        // Camera preview (optional, can be shown in a modal or next page)
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
            // You can show a preview here if desired
            cameraStream.getTracks().forEach(track => track.stop()); // Stop immediately for now
        } catch (err) {
            alert('Camera access denied or unavailable.');
            return;
        }
        const workoutConfig = {
            exercise_type: selectedExercise,
            mode: selectedMode,
            duration: selectedMode === 'timed' ? (selectedMinutes * 60 + selectedSeconds) : null,
            reps: selectedMode === 'reps' ? selectedReps : null
        };
        localStorage.setItem('workoutConfig', JSON.stringify(workoutConfig));
        window.location.href = '/workout';
    });
}); 