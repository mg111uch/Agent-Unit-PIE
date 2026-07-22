# 📂 core_2
Generated: 2026-07-21 18:31:40
Files: 2

---

F276│simulation_model.py│340
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
   ↳Calls: F273:create_unit_config
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

F275│world_engine.py│654
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
   ↳Called by: F234:fitBounds
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F234:fitBounds]
      S: Reset simulation world.
   F: health_check(self)→Any
   F: with_agricultural_simulation(cls,params)→'WorldEngine'
      S: Create WorldEngine with agricultural simulation.
      S: Usage:
      S: world = WorldEngine.with_agricultural_simulation(params)
      S: world.start()
      S: for _ in range(100):
   F: utc_now()→str
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
---
