# 📂 core
Generated: 2026-07-26 16:20:18
Files: 7

---

F121│agent_factory.py│181
S: core/agent_factory.py
D: ●numpy,typing,uuid
F: create_unit_config(agent_type,model,position,seed)→Any
   ↳Called by: F124:_create_unit
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F124:_create_unit]
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
   ↳Called by: F121:summary
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F121:summary]
   S: List all available agent types.
F: summary()→Any
   ↳Calls: F121:list_agent_types
   S: Get factory summary.
---

F122│event_bridge.py│226
S: simulation_engine/event_bridge.py
D: ●__future__,datetime,logging,typing
C: EventBridge│[__init__,process_simulation_step,process_simulation_event,convert_event_to_observation,process_observation,process_multiple_simulations,process_simulation_snapshot,health_check,utc_now]
   S: Simulation cognition bridge.
C: EventBridge│[__init__,process_simulation_step,process_simulation_event,convert_event_to_observation,process_observation,process_multiple_simulations,process_simulation_snapshot,health_check,utc_now]
   S: Simulation cognition bridge.
   F: __init__(self,observation_pipeline)
   F: process_simulation_step(self,simulation_id,events,metadata)→Any
      S: Process all events from one simulation step.
   F: process_simulation_event(self,simulation_id,event,metadata)→Any
      S: Process single simulation event.
   F: convert_event_to_observation(self,simulation_id,event,metadata)→Any
      S: Convert simulation event into universal observation.
   F: process_observation(self,observation)→Any
      S: Send observation into cognition pipeline.
   F: process_multiple_simulations(self,simulation_batches)→Any
      S: Process multiple simulation batches.
   F: process_simulation_snapshot(self,simulation_id,snapshot)→Any
      S: Convert world snapshot into observation.
   F: health_check(self)→Any
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
---

F119│resource_engine.py│628
S: simulation_engine/resource_engine.py
D: ●__future__,datetime,logging,typing
C: ResourceEngine│[__init__,create_resource_pool,get_resource_pool,add_resource,remove_resource,allocate_resource,transfer_resource,consume_resource,detect_scarcity,detect_abundance,+9]
   S: Unified resource simulation engine.
C: ResourceEngine│[__init__,create_resource_pool,get_resource_pool,add_resource,remove_resource,allocate_resource,transfer_resource,consume_resource,detect_scarcity,detect_abundance,+9]
   S: Unified resource simulation engine.
   F: __init__(self,ontology_registry,unit_registry,event_engine,pattern_engine,config)
   F: create_resource_pool(self,resource_type,initial_amount,metadata)→Any
      S: Create global resource pool.
   F: get_resource_pool(self,resource_type)→Any
   F: add_resource(self,resource_type,amount)→bool
      S: Add resources into pool.
   F: remove_resource(self,resource_type,amount)→bool
      S: Remove resources from pool.
   F: allocate_resource(self,unit_id,resource_type,amount)→bool
      S: Allocate resource to unit.
   F: transfer_resource(self,source_unit_id,target_unit_id,resource_type,amount,metadata)→bool
      S: Transfer resources between units.
   F: consume_resource(self,unit_id,resource_type,amount)→bool
      S: Consume resources from unit.
   F: detect_scarcity(self,threshold)→Any
      S: Detect scarce resources.
   F: detect_abundance(self,threshold)→Any
      S: Detect highly abundant resources.
   F: detect_bottlenecks(self)→Any
      S: Detect resource bottlenecks.
   F: detect_corruption_patterns(self)→Any
      S: Detect suspicious resource flows.
   F: simulate_economic_cycle(self)→Any
      S: Simulate economic movement.
   F: forecast_resource_collapse(self)→Any
      S: Forecast collapse risks.
   F: summarize_resources(self)→Any
      S: Generate resource statistics.
   F: emit_resource_event(self,event_type,unit_id,resource_type,amount)→None
      S: Emit simulation resource event.
   F: resolve_unit(self,unit_id)→Any
      S: Resolve unit from registry.
   F: health_check(self)→Any
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
---

F124│simulation_model.py│340
S: core/simulation_model.py
D: ●modules,numpy,pandas,typing
C: SimulationModel│[__init__,_init_units,_create_unit,add_unit,step,_execute_behaviors,_process_behavior_result,run,get_population_count,get_total_wealth,+4]
   S: Behavior-based agricultural simulation model.
C: DataCollector│[__init__,collect,get_model_vars_dataframe]
   S: Data collector for simulation metrics.
C: SimulationModel│[__init__,_init_units,_create_unit,add_unit,step,_execute_behaviors,_process_behavior_result,run,get_population_count,get_total_wealth,+4]
   S: Behavior-based agricultural simulation model.
   F: __init__(self,params)
   F: _init_units(self)→None
      S: Initialize all units from agent configs.
   F: _create_unit(self,agent_type,position,seed)→UnitAgent
   ↳Calls: F121:create_unit_config
      S: Create and register a unit.
   F: add_unit(self,unit_data)→UnitAgent
      S: Add a new unit to the simulation.
   F: step(self)→None
      S: Advance simulation by one tick.
   F: _execute_behaviors(self,unit,world_state)→None
      S: Execute all behaviors for a unit.
   F: _process_behavior_result(self,unit,result)→None
      S: Process behavior output.
   F: run(self,years)→None
      S: Run simulation for specified years.
   F: get_population_count(self)→int
      S: Get count of alive humans.
   F: get_total_wealth(self)→float
      S: Get total wealth of alive units.
   F: get_average_skill(self)→float
      S: Get average skill of alive humans.
   F: get_unit_type_count(self,unit_type,behavior)→int
      S: Get count of units by type and optional behavior.
   F: get_dataframe(self)→pd.DataFrame
      S: Get collected data as dataframe.
   F: summary(self)→Any
      S: Get simulation summary.
C: DataCollector│[__init__,collect,get_model_vars_dataframe]
   S: Data collector for simulation metrics.
   F: __init__(self,model_reporters)
   F: collect(self,model)→None
      S: Collect data from model.
   F: get_model_vars_dataframe(self)→pd.DataFrame
      S: Return collected data as dataframe.
---

F120│spatial_engine.py│136
S: core/spatial_engine.py
D: ●numpy,typing
C: SpatialEngine│[__init__,place_agent,remove_agent,move_agent,get_cell_list_contents,get_neighborhood,is_cell_empty,get_neighbors,get_units_at,is_valid_position,+3]
   S: Grid-based spatial management for units.
C: SpatialEngine│[__init__,place_agent,remove_agent,move_agent,get_cell_list_contents,get_neighborhood,is_cell_empty,get_neighbors,get_units_at,is_valid_position,+3]
   S: Grid-based spatial management for units.
   F: __init__(self,width,height,torus)
   F: place_agent(self,unit,pos)→None
      S: Place a unit at the specified position.
   F: remove_agent(self,unit)→None
      S: Remove a unit from its current position.
   F: move_agent(self,unit,pos)→None
      S: Move a unit to a new position.
   F: get_cell_list_contents(self,positions)→List[Any]
      S: Get all units at the specified positions.
   F: get_neighborhood(self,pos,moore,include_center,radius)→Any
      S: Get neighboring positions within the given radius.
   F: is_cell_empty(self,pos)→bool
      S: Check if a cell is empty.
   F: get_neighbors(self,pos,moore,radius,include_center)→List[Any]
      S: Get all units in neighboring positions.
   F: get_units_at(self,pos)→List[Any]
      S: Get all units at a specific position.
   F: is_valid_position(self,pos)→bool
      S: Check if position is within grid bounds.
   F: get_random_position(self)→Any
      S: Get a random position on the grid.
   F: get_all_positions(self)→Any
      S: Get all valid grid positions.
   F: summary(self)→Any
      S: Get spatial summary.
---

F118│unit_agent.py│410
S: simulation_engine/unit_agent.py
D: ●__future__,copy,datetime,logging,uuid,+1
C: UnitAgent│[__init__,step,process_behavior_result,add_signal,decay_signals,add_event,add_goal,remove_goal,add_relation,modify_resource,+8]
   S: Universal simulation unit.
C: UnitAgent│[__init__,step,process_behavior_result,add_signal,decay_signals,add_event,add_goal,remove_goal,add_relation,modify_resource,+8]
   S: Universal simulation unit.
   F: __init__(self,unit_id,unit_type,state,resources,behaviors,goals,relations,metadata)
   F: step(self,world_state,behavior_registry)→Any
      S: Execute one simulation step.
   F: process_behavior_result(self,result)→None
      S: Process outputs from behavior execution.
   F: add_signal(self,signal)→None
      S: Add active signal.
   F: decay_signals(self)→None
      S: Decay transient signals over time.
   F: add_event(self,event)→None
      S: Add generated event.
   F: add_goal(self,goal)→None
   F: remove_goal(self,goal_id)→bool
   F: add_relation(self,relation)→None
   F: modify_resource(self,resource_name,delta)→None
   F: get_resource(self,resource_name,default)→float
   F: set_state(self,key,value)→None
   F: get_state(self,key,default)→Any
   F: to_dict(self)→Any
      S: Export unit state.
   F: from_dict(cls,data)→'UnitAgent'
      S: Restore unit from serialized state.
   F: terminate(self,reason)→None
      S: Mark unit inactive.
   F: summary(self)→Any
      S: Lightweight runtime summary.
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
---

F123│world_engine.py│654
S: simulation_engine/world_engine.py
D: ●__future__,datetime,logging,modules,typing
C: WorldEngine│[__init__,start,stop,tick,process_simulation,process_behaviors,process_resources,process_events,evolve_environment,process_patterns,+7]
   S: Master simulation orchestrator.
C: WorldEngine│[__init__,start,stop,tick,process_simulation,process_behaviors,process_resources,process_events,evolve_environment,process_patterns,+7]
   S: Master simulation orchestrator.
   F: __init__(self,unit_registry,resource_engine,behavior_registry,event_engine,timeline_engine,pattern_engine,relation_engine,simulation_model,config)
   F: start(self)→None
      S: Start simulation.
   F: stop(self)→None
      S: Stop simulation.
   F: tick(self,delta_time)→Any
      S: Advance world simulation.
   F: process_simulation(self)→Any
      S: Advance the agricultural simulation model.
   F: process_behaviors(self)→Any
      S: Process all active unit behaviors.
   F: process_resources(self)→Any
      S: Process resource dynamics.
   F: process_events(self)→Any
      S: Process world events.
   F: evolve_environment(self)→Any
      S: Evolve world environment state.
   F: process_patterns(self)→Any
      S: Process pattern generation.
   F: generate_projection(self,unit_id,future_ticks)→Any
      S: Generate future simulation projection.
   F: generate_world_snapshot(self)→Any
      S: Generate full world snapshot.
   F: world_statistics(self)→Any
      S: Generate world statistics.
   F: reset(self)→None
      S: Reset simulation world.
   F: health_check(self)→Any
   F: with_agricultural_simulation(cls,params)→'WorldEngine'
      S: Create WorldEngine with agricultural simulation.
      S: Usage:
      S: world = WorldEngine.with_agricultural_simulation(params)
      S: world.start()
      S: for _ in range(100):
   F: utc_now()→str
   ↳Called by: F035:update_timestamp,F036:deactivate,F033:update_timestamp
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F035:update_timestamp],[F036:deactivate],[F033:update_timestamp]
---
