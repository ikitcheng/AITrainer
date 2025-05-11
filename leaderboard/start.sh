#!/bin/bash

# Start the inference service in the background
cd /app/leaderboard
python inference_service.py &

# Start the Flask application
python app.py 