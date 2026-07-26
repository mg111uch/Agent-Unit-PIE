# 📂 popula_dyn
Generated: 2026-07-26 16:20:18
Files: 4

---

F111│behavior_registry.py│99
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

F108│constants.py│27
D: ●typing
---

F110│main.py│12
D: ►F108 ●simulation
---

F109│simulation_game.py│173│⚡
D: ►F108 ●asyncio,json,model,pydantic,threading,+3
F: game_page()
   S: Serve the game page.
F: start_simulation()
   ↳Called by: F109:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F109:simulation_websocket]
   S: Start the simulation.
F: stop_simulation()
   ↳Called by: F109:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F109:simulation_websocket]
   S: Stop the simulation.
F: reset_simulation()
   ↳Called by: F109:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F109:simulation_websocket]
   S: Reset the simulation.
F: update_params(params)
   ↳Called by: F109:simulation_websocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F109:simulation_websocket]
   S: Update simulation parameters.
F: get_simulation_state()
   ↳Called by: F109:simulation_websocket,F109:broadcast_simulation_updates
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F109:simulation_websocket],[F109:broadcast_simulation_updates]
   S: Get current simulation state.
F: step_simulation()
   ↳Called by: F109:simulation_websocket,F109:broadcast_simulation_updates
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F109:simulation_websocket],[F109:broadcast_simulation_updates]
   S: Advance simulation by one step.
F: simulation_websocket(websocket)
   ↳Calls: F109:update_params,F109:reset_simulation,F109:step_simulation
   S: WebSocket endpoint for real-time simulation updates.
F: broadcast_simulation_updates()
   ↳Called by: F109:startup_event | Calls: F109:get_simulation_state,F109:step_simulation
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F109:startup_event]
   S: Broadcast simulation state to all connected clients.
F: startup_event()
   ↳Calls: F109:broadcast_simulation_updates
   S: Start background tasks on startup.
---
