from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import json
import asyncio
from typing import Dict, List
import cv2
import numpy as np
from pathlib import Path
import sys
import os
# Add parent directory to path to import workout_monitoring
sys.path.append(str(Path(__file__).parent.parent))
from src.workout_monitoring import process_video
from src.keypoints_in_box import keypoints_in_box

app = FastAPI(title="AI Workout")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Templates
templates = Jinja2Templates(directory="./templates")

# Store active connections
active_connections: Dict[str, WebSocket] = {}

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/select-workout", response_class=HTMLResponse)
async def select_workout(request: Request):
    return templates.TemplateResponse("select_workout.html", {"request": request})

@app.get("/workout", response_class=HTMLResponse)
async def workout(request: Request):
    return templates.TemplateResponse("workout.html", {"request": request})

@app.get("/results", response_class=HTMLResponse)
async def results(request: Request):
    return templates.TemplateResponse("results.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Handle different types of messages
            message = json.loads(data)
            if message["type"] == "start_workout":
                # Start workout monitoring
                await handle_workout_start(websocket, message["data"])
            elif message["type"] == "stop_workout":
                # Stop workout monitoring
                await handle_workout_stop(websocket)
    except WebSocketDisconnect:
        del active_connections[client_id]

async def handle_workout_start(websocket: WebSocket, data: dict):
    exercise_type = data.get("exercise_type", "pushups")
    mode = data.get("mode", "timed")
    duration = data.get("duration", 60)  # Default 60 seconds
    target_reps = data.get("reps", 10)  # Default 10 reps
    
    # Send initial countdown
    for i in range(3, 0, -1):
        await websocket.send_json({
            "type": "countdown",
            "value": i
        })
        await asyncio.sleep(1)
    
    # Start workout monitoring
    await websocket.send_json({
        "type": "workout_start",
        "message": "Go!",
        "config": {
            "exercise_type": exercise_type,
            "mode": mode,
            "duration": duration,
            "target_reps": target_reps
        }
    })

    # Simulate workout progress (replace with actual video processing)
    reps = 0
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if mode == "timed" and (asyncio.get_event_loop().time() - start_time) >= duration:
            break
        if mode == "reps" and reps >= target_reps:
            break
            
        # Simulate rep detection (replace with actual video processing)
        await asyncio.sleep(2)
        reps += 1
        
        # Send updates
        await websocket.send_json({
            "type": "rep_update",
            "value": reps
        })
        
        if mode == "timed":
            elapsed_time = int(asyncio.get_event_loop().time() - start_time)
            await websocket.send_json({
                "type": "timer_update",
                "value": elapsed_time
            })
            
            # Calculate power (simplified)
            power = int(reps * 10)  # Simplified power calculation
            await websocket.send_json({
                "type": "power_update",
                "value": power
            })
    
    # Send workout end with results
    await websocket.send_json({
        "type": "workout_end",
        "message": "Workout completed!",
        "results": {
            "reps": reps,
            "time": int(asyncio.get_event_loop().time() - start_time),
            "power": int(reps * 10)  # Simplified power calculation
        }
    })

async def handle_workout_stop(websocket: WebSocket):
    await websocket.send_json({
        "type": "workout_end",
        "message": "Workout completed!"
    })

@app.post("/api/check-in-box")
async def check_in_box(file: UploadFile = File(...), x1: int = Form(...), y1: int = Form(...), x2: int = Form(...), y2: int = Form(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    box = (x1, y1, x2, y2)
    in_box = keypoints_in_box(img, box, threshold=0.8, is_display=True)
    return JSONResponse({"in_box": in_box})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 