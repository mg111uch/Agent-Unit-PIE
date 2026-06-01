# 📂 popula_dyn
Generated: 2026-06-01 13:39:55
Files: 4

---

F097│behavior_registry.py│99
S: behavior_registry.py
D: ●logging,modules,typing
C: BehaviorRegistry│[__init__,register_default_behaviors,register_behavior,get_behavior,behavior_exists,remove_behavior,list_behaviors,execute_behavior,summary]
   S: Global reusable behavior registry.
---

F094│constants.py│27
D: ●typing
---

F096│main.py│12
D: ►F094 ●simulation
---

F095│simulation_game.py│173│⚡
D: ►F094 ●fastapi,json,pydantic,threading,typing,+3
F: game_page()
   S: Serve the game page.
F: start_simulation()
   ↳Called by: F095:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:simulation_websocket]
   S: Start the simulation.
F: stop_simulation()
   ↳Called by: F095:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:simulation_websocket]
   S: Stop the simulation.
F: reset_simulation()
   ↳Called by: F095:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:simulation_websocket]
   S: Reset the simulation.
F: update_params(params)
   ↳Called by: F095:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:simulation_websocket]
   S: Update simulation parameters.
F: get_simulation_state()
   ↳Called by: F095:simulation_websocket,F095:broadcast_simulation_updates
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F095:simulation_websocket],[F095:broadcast_simulation_updates]
   S: Get current simulation state.
F: step_simulation()
   ↳Called by: F095:simulation_websocket,F095:broadcast_simulation_updates
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F095:simulation_websocket],[F095:broadcast_simulation_updates]
   S: Advance simulation by one step.
F: simulation_websocket(websocket)
   ↳Calls: F095:stop_simulation,F095:get_simulation_state,F095:start_simulation
   S: WebSocket endpoint for real-time simulation updates.
F: broadcast_simulation_updates()
   ↳Called by: F095:startup_event | Calls: F095:get_simulation_state,F095:step_simulation
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F095:startup_event]
   S: Broadcast simulation state to all connected clients.
F: startup_event()
   ↳Calls: F095:broadcast_simulation_updates
   S: Start background tasks on startup.
---
