# 📂 popula_dyn
Generated: 2026-07-21 18:31:40
Files: 4

---

F263│behavior_registry.py│99
S: behavior_registry.py
D: ●logging,modules,typing
C: BehaviorRegistry│[__init__,register_default_behaviors,register_behavior,get_behavior,behavior_exists,remove_behavior,list_behaviors,execute_behavior,summary]
   S: Global reusable behavior registry.
C: BehaviorRegistry│[__init__,register_default_behaviors,register_behavior,get_behavior,behavior_exists,remove_behavior,list_behaviors,execute_behavior,summary]
   S: Global reusable behavior registry.
   F: __init__(self)
   F: register_default_behaviors(self)→None
      S: Register all built-in behaviors.
   F: register_behavior(self,behavior)→None
      S: Register a behavior instance.
   F: get_behavior(self,behavior_name)→Optional[BaseBehavior]
      S: Retrieve behavior by name.
   F: behavior_exists(self,behavior_name)→bool
      S: Check if behavior exists.
   F: remove_behavior(self,behavior_name)→bool
      S: Remove a registered behavior.
   F: list_behaviors(self)→List[str]
      S: List all available behaviors.
   F: execute_behavior(self,behavior_name,unit,world_state)→Any
      S: Execute behavior directly.
   F: summary(self)→Any
      S: Get registry summary.
---

F260│constants.py│27
D: ●typing
---

F262│main.py│12
D: ►F237 ●simulation
---

F261│simulation_game.py│173│⚡
D: ►F237 ●fastapi,model,pydantic,threading,typing,+3
F: game_page()
   S: Serve the game page.
F: start_simulation()
   ↳Called by: F261:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F261:simulation_websocket]
   S: Start the simulation.
F: stop_simulation()
   ↳Called by: F261:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F261:simulation_websocket]
   S: Stop the simulation.
F: reset_simulation()
   ↳Called by: F261:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F261:simulation_websocket]
   S: Reset the simulation.
F: update_params(params)
   ↳Called by: F261:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F261:simulation_websocket]
   S: Update simulation parameters.
F: get_simulation_state()
   ↳Called by: F261:simulation_websocket,F261:broadcast_simulation_updates
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F261:simulation_websocket],[F261:broadcast_simulation_updates]
   S: Get current simulation state.
F: step_simulation()
   ↳Called by: F261:simulation_websocket,F261:broadcast_simulation_updates
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F261:simulation_websocket],[F261:broadcast_simulation_updates]
   S: Advance simulation by one step.
F: simulation_websocket(websocket)
   ↳Calls: F261:start_simulation,F261:step_simulation,F261:reset_simulation
   S: WebSocket endpoint for real-time simulation updates.
F: broadcast_simulation_updates()
   ↳Called by: F261:startup_event | Calls: F261:step_simulation,F261:get_simulation_state
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F261:startup_event]
   S: Broadcast simulation state to all connected clients.
F: startup_event()
   ↳Calls: F261:broadcast_simulation_updates
   S: Start background tasks on startup.
---
