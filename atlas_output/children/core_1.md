# 📂 core_1
Generated: 2026-07-21 18:31:40
Files: 10

---

F273│agent_factory.py│181
S: core/agent_factory.py
D: ●numpy,typing,uuid
F: create_unit_config(agent_type,model,position,seed)→Any
   ↳Called by: F276:_create_unit
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F276:_create_unit]
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
   ↳Called by: F273:summary
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F273:summary]
   S: List all available agent types.
F: summary()→Any
   ↳Calls: F273:list_agent_types
   S: Get factory summary.
---

F237│constants.js│115
F: clampZoom(value)
   ↳Called by: F234:centerOn,F234:setZoom,F234:fitBounds | Calls: F237:isMultiSelectKey
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F234:centerOn],[F234:setZoom],[F234:fitBounds]
F: isMultiSelectKey(event)
   ↳Called by: F248:bindSelection,F248:initialize,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F248:bindSelection],[F248:initialize],[F248:if]
---

F274│event_bridge.py│226
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
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
---

F236│events.js│157
C: EventEmitter│[on,if,once,off,if,if,emit,if,for,catch,+5]
F: wrapper(payload)
   ↳Calls: F249:if,F236:catch,F236:for
C: EventEmitter│[on,if,once,off,if,if,emit,if,for,catch,+5]
   F: on(eventName,callback)
   ↳Calls: F249:if,F248:if,F241:if
   F: if(typeof callback !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: once(eventName,callback)
   ↳Called by: F236:on,F236:if | Calls: F249:if,F236:catch,F236:for
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F236:on],[F236:if]
   F: off(eventName,callback)
   ↳Called by: F236:on,F236:wrapper,F236:once | Calls: F249:if,F236:catch,F236:hasListeners
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F236:on],[F236:wrapper],[F236:once]
   F: if(!listeners)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(listeners.size)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: emit(eventName,payload)
   ↳Called by: F236:once,F240:subscribe,F236:if | Calls: F249:if,F236:catch,F236:hasListeners
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F236:once],[F240:subscribe],[F236:if]
   F: if(!listeners || listeners.size)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const listener of snapshot)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:catch,F236:hasListeners
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: catch(error)
   ↳Called by: F236:once,F236:emit,F239:storageKey | Calls: F249:if,F236:hasListeners,F248:if
   ↳Impact: 🔴HIGH (13 dependents) | Breaks: [F236:once],[F236:emit],[F239:storageKey]
   F: clear(eventName)
   ↳Called by: F236:emit,F236:catch,F236:for | Calls: F249:if,F236:hasListeners,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F236:emit],[F236:catch],[F236:for]
   F: if(eventName)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: hasListeners(eventName)
   ↳Called by: F236:emit,F236:catch,F236:clear | Calls: F236:listenerCount,F236:eventNames
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F236:emit],[F236:catch],[F236:clear]
   F: listenerCount(eventName)
   ↳Called by: F236:emit,F236:catch,F236:clear | Calls: F236:eventNames
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F236:emit],[F236:catch],[F236:clear]
   F: eventNames()
   ↳Called by: F236:emit,F236:catch,F236:clear
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F236:emit],[F236:catch],[F236:clear]
---

F271│resource_engine.py│628
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
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
---

F272│spatial_engine.py│136
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

F240│state.js│539
C: GraphState←EventEmitter│[_buildIndexes,for,for,for,_buildRelationships,for,for,_buildCallNodeParent,for,if,+9]
C: GraphState←EventEmitter│[_buildIndexes,for,for,for,_buildRelationships,for,for,_buildCallNodeParent,for,if,+9]
   F: _buildIndexes()
   ↳Calls: F249:if,F236:for,F248:if
   F: for(const node of this.graph.nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const edge of this.graph.edges)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const cluster of this.graph.clusters)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: _buildRelationships()
   ↳Called by: F240:for,F240:_buildIndexes | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F240:for],[F240:_buildIndexes]
   F: for(const node of this.graph.nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const edge of this.graph.edges)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: _buildCallNodeParent()
   ↳Called by: F240:_buildRelationships,F240:for,F240:_buildIndexes | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F240:_buildRelationships],[F240:for],[F240:_buildIndexes]
   F: for(const edge of this.graph.edges)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: if(sourceParent && targetParent)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(sourceParent !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(sourceParent)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(targetParent)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: subscribe(eventName,callback)
   ↳Calls: F240:clearNodeSelection,F249:if,F236:for
   F: emit(eventName,payload)
   ↳Called by: F236:once,F240:subscribe,F236:if | Calls: F240:clearNodeSelection,F249:if,F236:for
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F236:once],[F240:subscribe],[F236:if]
   F: if(listeners)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const callback of listeners)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: selectNode(nodeId)
   ↳Called by: F240:subscribe,F248:bindSelection,F250:if | Calls: F240:clearNodeSelection,F249:if,F248:if
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F240:subscribe],[F248:bindSelection],[F250:if]
   F: clearNodeSelection()
   ↳Called by: F240:subscribe,F240:emit,F240:selectNode
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F240:subscribe],[F240:emit],[F240:selectNode]
---

F239│storage.js│217
C: GraphStorage│[storageKey,createSnapshot,save,catch,load,if,catch,restore,if,if,+10]
F: createStorage(namespace)
   ↳Called by: F239:for,F239:resume,F239:suspend
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F239:for],[F239:resume],[F239:suspend]
F: save()
   ↳Called by: F239:storageKey,F239:createSnapshot | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F239:storageKey],[F239:createSnapshot]
C: GraphStorage│[storageKey,createSnapshot,save,catch,load,if,catch,restore,if,if,+10]
   F: storageKey()
   ↳Calls: F239:catch,F239:save,F239:createSnapshot
   F: createSnapshot(state)
   ↳Called by: F239:storageKey | Calls: F236:catch,F239:catch,F239:save
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F239:storageKey]
   F: save(state)
   ↳Called by: F239:storageKey,F239:createSnapshot | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F239:storageKey],[F239:createSnapshot]
   F: catch(error)
   ↳Called by: F236:once,F236:emit,F239:storageKey | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (13 dependents) | Breaks: [F236:once],[F236:emit],[F239:storageKey]
   F: load()
   ↳Called by: F239:catch,F239:createSnapshot | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F239:catch],[F239:createSnapshot]
   F: if(!raw)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: catch(error)
   ↳Called by: F236:once,F236:emit,F239:storageKey | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (13 dependents) | Breaks: [F236:once],[F236:emit],[F239:storageKey]
   F: restore(state)
   ↳Called by: F239:catch,F239:if,F239:load | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F239:catch],[F239:if],[F239:load]
   F: if(!snapshot)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(snapshot.viewport)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: catch(error)
   ↳Called by: F236:once,F236:emit,F239:storageKey | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (13 dependents) | Breaks: [F236:once],[F236:emit],[F239:storageKey]
   F: clear()
   ↳Called by: F236:emit,F236:catch,F236:for | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F236:emit],[F236:catch],[F236:for]
   F: catch(error)
   ↳Called by: F236:once,F236:emit,F239:storageKey | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (13 dependents) | Breaks: [F236:once],[F236:emit],[F239:storageKey]
   F: attach(state)
   ↳Called by: F239:clear | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F239:clear]
   F: if(this._suspendCount > 0)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const unsubscribe of unsubscribers)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: suspend()
   ↳Called by: F239:for | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F239:for]
   F: resume()
   ↳Called by: F239:for,F239:suspend | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F239:for],[F239:suspend]
   F: if(this._suspendCount > 0)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F236:catch,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: createStorage(namespace)
   ↳Called by: F239:for,F239:resume,F239:suspend
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F239:for],[F239:resume],[F239:suspend]
---

F238│types.js│253
C: GraphNode│[validate,if]
C: GraphEdge│[validate,if,if]
C: GraphCluster│[validate,if]
C: GraphData│[buildIndexes,for,for,for,validate,for,for,for,getNode,getEdge,+2]
F: isObject(value)
   ↳Called by: F238:ensureArray,F238:ensureString,F238:ensureNumber | Calls: F238:ensureArray,F238:ensureString,F238:ensureNumber
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F238:ensureArray],[F238:ensureString],[F238:ensureNumber]
F: ensureArray(value)
   ↳Called by: F238:isObject | Calls: F238:ensureString,F238:isObject,F238:ensureNumber
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F238:isObject]
F: ensureString(value,fallback)
   ↳Called by: F238:ensureArray,F238:ensureString,F238:isObject | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F238:ensureArray],[F238:ensureString],[F238:isObject]
F: ensureNumber(value,fallback)
   ↳Called by: F238:ensureArray,F238:ensureString,F238:isObject | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F238:ensureArray],[F238:ensureString],[F238:isObject]
F: createGraphData(rawData)
   ↳Called by: F238:getNode,F238:getEdge,F238:getCluster
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F238:getNode],[F238:getEdge],[F238:getCluster]
C: GraphNode│[validate,if]
   F: validate()
   ↳Called by: F238:for,F238:buildIndexes,F238:ensureString | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F238:for],[F238:buildIndexes],[F238:ensureString]
   F: if(!this.id)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
C: GraphEdge│[validate,if,if]
   F: validate()
   ↳Called by: F238:for,F238:buildIndexes,F238:ensureString | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F238:for],[F238:buildIndexes],[F238:ensureString]
   F: if(!this.source)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(!this.target)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
C: GraphCluster│[validate,if]
   F: validate()
   ↳Called by: F238:for,F238:buildIndexes,F238:ensureString | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F238:for],[F238:buildIndexes],[F238:ensureString]
   F: if(!this.id)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
C: GraphData│[buildIndexes,for,for,for,validate,for,for,for,getNode,getEdge,+2]
   F: buildIndexes()
   ↳Calls: F249:if,F236:for,F248:if
   F: for(const node of this.nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const edge of this.edges)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const cluster of this.clusters)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: validate()
   ↳Called by: F238:for,F238:buildIndexes,F238:ensureString | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F238:for],[F238:buildIndexes],[F238:ensureString]
   F: for(const node of this.nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const edge of this.edges)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const cluster of this.clusters)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: getNode(id)
   ↳Called by: F238:for | Calls: F238:createGraphData,F238:getEdge,F238:getCluster
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F238:for]
   F: getEdge(id)
   ↳Called by: F238:getNode | Calls: F238:createGraphData,F238:getCluster
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F238:getNode]
   F: getCluster(id)
   ↳Called by: F238:getNode,F238:getEdge | Calls: F238:createGraphData
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F238:getNode],[F238:getEdge]
   F: createGraphData(rawData)
   ↳Called by: F238:getNode,F238:getEdge,F238:getCluster
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F238:getNode],[F238:getEdge],[F238:getCluster]
---

F270│unit_agent.py│410
S: simulation_engine/unit_agent.py
D: ●__future__,copy,datetime,logging,typing,+1
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
   ↳Called by: F072:update_timestamp,F073:update_timestamp,F076:mark_interaction
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F072:update_timestamp],[F073:update_timestamp],[F076:mark_interaction]
---
