# AI Workout

An interactive workout game that uses computer vision to track and analyze your exercises in real-time.

## Features

- Real-time exercise tracking using computer vision
- Multiple exercise types (push-ups, pull-ups, squats)
- Different workout modes (timed, rep-based)
- Real-time rep counting and power output calculation
- Clean and modern UI with smooth animations
- WebSocket-based real-time communication
- Leaderboard integration (coming soon)

## Prerequisites

- Python 3.8 or higher
- Modern web browser with camera access
- WebGL support for optimal performance

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd game
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

## Usage

1. Select your exercise type and workout mode
2. Click "Start Workout"
3. Position yourself in the highlighted box following the instructions
4. Click "I'm Ready" when positioned correctly
5. Wait for the countdown and begin your workout
6. View your results and choose to log them, try again, or exit

## Development

The application is built with:
- FastAPI for the backend
- WebSocket for real-time communication
- OpenCV for computer vision
- Modern JavaScript (ES6+) for the frontend
- TailwindCSS for styling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 