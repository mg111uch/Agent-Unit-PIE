from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import json
import threading
from model import AgriculturalModel
from constants import PARAMS

app = FastAPI(title="Simulation Game API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global simulation state
simulation_model = None
simulation_running = False
simulation_params = PARAMS.copy()
simulation_params["fertility_movement"] = False
connected_clients = set()

@app.get("/game")
async def game_page():
    """Serve the game page."""
    return FileResponse("static/game.html")

# === Simulation Game Endpoints ===

@app.post("/simulation/start")
async def start_simulation():
    """Start the simulation."""
    global simulation_model, simulation_running
    try:
        simulation_model = AgriculturalModel(simulation_params)
        simulation_running = True
        return {"message": "Simulation started", "params": simulation_params}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting simulation: {str(e)}")

@app.post("/simulation/stop")
async def stop_simulation():
    """Stop the simulation."""
    global simulation_running
    simulation_running = False
    return {"message": "Simulation stopped"}

@app.post("/simulation/reset")
async def reset_simulation():
    """Reset the simulation."""
    global simulation_model, simulation_running
    simulation_running = False
    simulation_model = None
    return {"message": "Simulation reset"}

@app.post("/simulation/params")
async def update_params(params: Dict[str, Any]):
    """Update simulation parameters."""
    global simulation_params
    simulation_params.update(params)
    return {"message": "Parameters updated", "params": simulation_params}

@app.get("/simulation/state")
async def get_simulation_state():
    """Get current simulation state."""
    if simulation_model:
        data = simulation_model.datacollector.get_model_vars_dataframe()
        latest = data.iloc[-1] if not data.empty else {}

        # Get agent positions for visualization
        agent_positions = []
        for agent in simulation_model.agents:
            if hasattr(agent, 'pos') and agent.pos:
                agent_type = 'land'
                if hasattr(agent, '__class__'):
                    class_name = agent.__class__.__name__
                    if 'Farmer' in class_name:
                        agent_type = 'farmer'
                    elif 'Healer' in class_name:
                        agent_type = 'healer'
                    elif 'Toolmaker' in class_name:
                        agent_type = 'toolmaker'
                    elif 'Trader' in class_name:
                        agent_type = 'trader'

                agent_positions.append({
                    'x': agent.pos[0],
                    'y': agent.pos[1],
                    'type': agent_type,
                    'id': agent.unique_id
                })

        return {
            "running": simulation_running,
            "year": len(data) if not data.empty else 0,
            "population": latest.get('Population', 0),
            "wealth": latest.get('Total_Wealth', 0),
            "births": latest.get('Births', 0),
            "deaths": latest.get('Deaths', 0),
            "avg_skill": latest.get('Avg_Skill', 0),
            "healers": latest.get('Healer_Count', 0),
            "toolmakers": latest.get('Toolmaker_Count', 0),
            "traders": latest.get('Trader_Count', 0),
            "agent_positions": agent_positions,
            "grid_width": simulation_params.get('grid_width', 50),
            "grid_height": simulation_params.get('grid_height', 50)
        }
    return {"running": False, "year": 0, "agent_positions": [], "grid_width": 50, "grid_height": 50}

@app.post("/simulation/step")
async def step_simulation():
    """Advance simulation by one step."""
    global simulation_model
    if simulation_model and simulation_running:
        simulation_model.step()
        return {"message": "Simulation stepped"}
    return {"message": "Simulation not running"}

# === WebSocket for Real-time Updates ===

@app.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time simulation updates."""
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        # Send initial state
        state = await get_simulation_state()
        await websocket.send_json({"type": "state", "data": state})

        while True:
            # Listen for client messages
            data = await websocket.receive_json()

            if data.get("type") == "start":
                await start_simulation()
                state = await get_simulation_state()
                await websocket.send_json({"type": "state", "data": state})

            elif data.get("type") == "stop":
                await stop_simulation()
                state = await get_simulation_state()
                await websocket.send_json({"type": "state", "data": state})

            elif data.get("type") == "reset":
                await reset_simulation()
                state = await get_simulation_state()
                await websocket.send_json({"type": "state", "data": state})

            elif data.get("type") == "step":
                await step_simulation()
                state = await get_simulation_state()
                await websocket.send_json({"type": "state", "data": state})

            elif data.get("type") == "update_params":
                await update_params(data.get("params", {}))
                state = await get_simulation_state()
                await websocket.send_json({"type": "state", "data": state})

    except WebSocketDisconnect:
        connected_clients.remove(websocket)

# Background task to broadcast simulation updates
async def broadcast_simulation_updates():
    """Broadcast simulation state to all connected clients."""
    while True:
        if simulation_running and simulation_model and connected_clients:
            try:
                await step_simulation()
                state = await get_simulation_state()

                # Broadcast to all clients
                for client in connected_clients.copy():
                    try:
                        await client.send_json({"type": "update", "data": state})
                    except:
                        connected_clients.remove(client)

            except Exception as e:
                print(f"Error in simulation broadcast: {e}")

        await asyncio.sleep(1.0)  # Update every second

# Start background task
@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    asyncio.create_task(broadcast_simulation_updates())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)