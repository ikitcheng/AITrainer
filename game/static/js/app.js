class WorkoutApp {
    constructor() {
        this.screens = {
            home: document.getElementById('home-screen'),
            instructions: document.getElementById('instructions-screen'),
            workout: document.getElementById('workout-screen'),
            results: document.getElementById('results-screen')
        };
        
        this.elements = {
            exerciseType: document.getElementById('exercise-type'),
            workoutMode: document.getElementById('workout-mode'),
            startWorkout: document.getElementById('start-workout'),
            readyButton: document.getElementById('ready-button'),
            positionBox: document.getElementById('position-box'),
            positionInstructions: document.getElementById('position-instructions'),
            timer: document.getElementById('timer'),
            repCounter: document.getElementById('rep-counter'),
            finalReps: document.getElementById('final-reps'),
            powerOutput: document.getElementById('power-output'),
            logResult: document.getElementById('log-result'),
            tryAgain: document.getElementById('try-again'),
            exitHome: document.getElementById('exit-home')
        };

        this.websocket = null;
        this.stream = null;
        this.workoutData = {
            reps: 0,
            power: 0
        };

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.elements.startWorkout.addEventListener('click', () => this.startWorkout());
        this.elements.readyButton.addEventListener('click', () => this.startWorkoutSession());
        this.elements.logResult.addEventListener('click', () => this.logResult());
        this.elements.tryAgain.addEventListener('click', () => this.resetWorkout());
        this.elements.exitHome.addEventListener('click', () => this.showScreen('home'));
    }

    async startWorkout() {
        const exerciseType = this.elements.exerciseType.value;
        const mode = this.elements.workoutMode.value;
        
        // Update instructions based on exercise type
        this.updateInstructions(exerciseType);
        
        // Initialize camera
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.createElement('video');
            video.srcObject = this.stream;
            video.autoplay = true;
            this.elements.positionBox.innerHTML = '';
            this.elements.positionBox.appendChild(video);
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Error accessing camera. Please make sure you have granted camera permissions.');
            return;
        }

        this.showScreen('instructions');
    }

    updateInstructions(exerciseType) {
        const instructions = {
            pushups: 'Position yourself in the box. Keep your body straight and hands shoulder-width apart.',
            pullups: 'Position yourself in the box. Stand with your back to the camera, hands on the bar.',
            squats: 'Position yourself in the box. Stand with your feet shoulder-width apart.'
        };
        
        this.elements.positionInstructions.textContent = instructions[exerciseType] || instructions.pushups;
    }

    async startWorkoutSession() {
        // Initialize WebSocket connection
        this.websocket = new WebSocket(`ws://${window.location.host}/ws/${Date.now()}`);
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.websocket.onopen = () => {
            // Send workout configuration
            this.websocket.send(JSON.stringify({
                type: 'start_workout',
                data: {
                    exercise_type: this.elements.exerciseType.value,
                    mode: this.elements.workoutMode.value
                }
            }));
        };

        this.showScreen('workout');
        this.startTimer();
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'countdown':
                this.showCountdown(data.value);
                break;
            case 'workout_start':
                this.startWorkoutTracking();
                break;
            case 'rep_update':
                this.updateRepCounter(data.reps);
                break;
            case 'power_update':
                this.updatePowerOutput(data.power);
                break;
            case 'workout_end':
                this.endWorkout(data);
                break;
        }
    }

    showCountdown(value) {
        const countdown = document.createElement('div');
        countdown.className = 'countdown';
        countdown.textContent = value;
        this.elements.positionBox.appendChild(countdown);
        
        setTimeout(() => {
            countdown.remove();
        }, 1000);
    }

    startWorkoutTracking() {
        // Move camera feed to workout screen
        const video = this.elements.positionBox.querySelector('video');
        if (video) {
            this.elements.workoutFeed.innerHTML = '';
            this.elements.workoutFeed.appendChild(video);
        }
    }

    startTimer() {
        let timeLeft = 60; // 1 minute
        this.elements.timer.textContent = timeLeft;
        
        const timer = setInterval(() => {
            timeLeft--;
            this.elements.timer.textContent = timeLeft;
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                this.endWorkout();
            }
        }, 1000);
    }

    updateRepCounter(reps) {
        this.workoutData.reps = reps;
        this.elements.repCounter.textContent = reps;
    }

    updatePowerOutput(power) {
        this.workoutData.power = power;
        this.elements.powerOutput.textContent = `${power.toFixed(1)} W`;
    }

    endWorkout(data) {
        this.showScreen('results');
        this.elements.finalReps.textContent = this.workoutData.reps;
        this.elements.powerOutput.textContent = `${this.workoutData.power.toFixed(1)} W`;
        
        // Stop camera stream
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        // Close WebSocket connection
        if (this.websocket) {
            this.websocket.close();
        }
    }

    async logResult() {
        // TODO: Implement login and leaderboard integration
        alert('Leaderboard integration coming soon!');
    }

    resetWorkout() {
        this.workoutData = { reps: 0, power: 0 };
        this.showScreen('home');
    }

    showScreen(screenName) {
        Object.values(this.screens).forEach(screen => {
            screen.classList.add('hidden');
        });
        this.screens[screenName].classList.remove('hidden');
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new WorkoutApp();
}); 