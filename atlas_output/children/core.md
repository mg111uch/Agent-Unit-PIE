# 📂 core
Generated: 2026-06-01 13:39:55
Files: 7

---

F107│agent_factory.py│181
S: core/agent_factory.py
D: ●numpy,typing,uuid
F: create_unit_config(agent_type,model,position,seed)→Any
   ↳Called by: F110:_create_unit
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F110:_create_unit]
   S: Create a unit configuration with unique ID.
   S: Parameters
   S: ----------
   S: agent_type : str
   S: Type: "farmer", "healer", "toolmaker", "trader", "land"
F: get_agent_behaviors(agent_type)→list
   S: Get behavior list for agent type.
F: get_agent_type_from_behavior(behavior_name)→Optional[str]
   S: Find agent type that uses a given behavior.
F: list_agent_types()→list
   ↳Called by: F107:summary
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F107:summary]
   S: List all available agent types.
F: summary()→Any
   ↳Calls: F107:list_agent_types
   S: Get factory summary.
---

F108│event_bridge.py│244
S: simulation_engine/event_bridge.py
D: ●__future__,datetime,logging,typing
C: EventBridge│[__init__,process_simulation_step,process_simulation_event,convert_event_to_observation,process_observation,process_multiple_simulations,process_simulation_snapshot,health_check,utc_now]
   S: Simulation cognition bridge.
---

F105│resource_engine.py│682
S: simulation_engine/resource_engine.py
D: ●__future__,datetime,logging,typing
C: ResourceEngine│[__init__,create_resource_pool,get_resource_pool,add_resource,remove_resource,allocate_resource,transfer_resource,consume_resource,detect_scarcity,detect_abundance,+9]
   S: Unified resource simulation engine.
---

F110│simulation_model.py│340
S: core/simulation_model.py
D: ●modules,numpy,pandas,typing
C: SimulationModel│[__init__,_init_units,_create_unit,add_unit,step,_execute_behaviors,_process_behavior_result,run,get_population_count,get_total_wealth,+4]
   S: Behavior-based agricultural simulation model.
C: DataCollector│[__init__,collect,get_model_vars_dataframe]
   S: Data collector for simulation metrics.
---

F106│spatial_engine.py│136
S: core/spatial_engine.py
D: ●numpy,typing
C: SpatialEngine│[__init__,place_agent,remove_agent,move_agent,get_cell_list_contents,get_neighborhood,is_cell_empty,get_neighbors,get_units_at,is_valid_position,+3]
   S: Grid-based spatial management for units.
---

F104│unit_agent.py│452
S: simulation_engine/unit_agent.py
D: ●copy,datetime,logging,typing,uuid,+1
C: UnitAgent│[__init__,step,process_behavior_result,add_signal,decay_signals,add_event,add_goal,remove_goal,add_relation,modify_resource,+8]
   S: Universal simulation unit.
---

F109│world_engine.py│712
S: simulation_engine/world_engine.py
D: ●__future__,datetime,logging,modules,typing
C: WorldEngine│[__init__,start,stop,tick,process_simulation,process_behaviors,process_resources,process_events,evolve_environment,process_patterns,+7]
   S: Master simulation orchestrator.
---
