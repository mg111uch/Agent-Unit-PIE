# 📂 interaction
Generated: 2026-07-21 18:31:40
Files: 4

---

F249│drag.js│274
C: DragController│[_bindEvents,if,onPointerDown,if,if,for,onPointerMove,if,if,if,+10]
C: DragController│[_bindEvents,if,onPointerDown,if,if,for,onPointerMove,if,if,if,+10]
   F: _bindEvents()
   ↳Called by: F247:if,F247:destroy,F247:initialize | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F247:if],[F247:destroy],[F247:initialize]
   F: if(!this.events)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: onPointerDown(event)
   ↳Called by: F249:_bindEvents,F249:if | Calls: F249:if,F250:getSelectedNodes,F236:for
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F249:_bindEvents],[F249:if]
   F: if(event.button !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(event.target?.type !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const id of selected)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: onPointerMove(event)
   ↳Called by: F249:for | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F249:for]
   F: if(!this.dragTarget)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(!this.dragging)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(distance <
                DRAG.START_THRESHOLD_PX)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: onPointerUp()
   ↳Called by: F249:onPointerMove | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F249:onPointerMove]
   F: if(this.dragging)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: moveNodes(deltaX,deltaY)
   ↳Called by: F249:onPointerUp | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F249:onPointerUp]
   F: for(const nodeId
            of this.draggedNodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: if(!group)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const childId
                of group.childNodeIds)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: _moveSingleNode(nodeId,deltaX,deltaY)
   ↳Called by: F249:moveNodes | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F249:moveNodes]
   F: if(!node)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(!node.position)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(DRAG.ENABLE_GRID_SNAP)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
---

F247│events.js│383
C: GraphEventController←EventEmitter│[initialize,if,destroy,if,_bindEvents,_unbindEvents,createGraphEvent,resolveTarget,if,if,+2]
C: GraphEventController←EventEmitter│[initialize,if,destroy,if,_bindEvents,_unbindEvents,createGraphEvent,resolveTarget,if,if,+2]
   F: initialize()
   ↳Called by: F229:createGraphViewer,F242:_bindStateEvents,F242:setClusterRenderer | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F229:createGraphViewer],[F242:_bindStateEvents],[F242:setClusterRenderer]
   F: if(this.enabled)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: destroy()
   ↳Called by: F247:if,F247:initialize,F248:initialize | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F247:if],[F247:initialize],[F248:initialize]
   F: if(!this.enabled)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: _bindEvents()
   ↳Called by: F247:if,F247:destroy,F247:initialize
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F247:if],[F247:destroy],[F247:initialize]
   F: _unbindEvents()
   ↳Calls: F247:createGraphEvent
   F: createGraphEvent(event)
   ↳Called by: F247:_unbindEvents | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F247:_unbindEvents]
   F: resolveTarget(element)
   ↳Called by: F247:createGraphEvent | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F247:createGraphEvent]
   F: if(!element)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(node)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(edge)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(cluster)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
---

F248│interaction.js│666
C: GraphInteractionManager│[initialize,destroy,if,bindSelection,if,if,if,if,if,if,+5]
F: getBoxRect(clientX,clientY)
   ↳Called by: F248:getBoxRect,F248:updateBoxRect | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F248:getBoxRect],[F248:updateBoxRect]
F: updateBoxRect(clientX,clientY)
   ↳Calls: F249:if,F248:if,F241:if
F: resetStaleSuppress()
   ↳Calls: F249:if,F248:if,F241:if
C: GraphInteractionManager│[initialize,destroy,if,bindSelection,if,if,if,if,if,if,+5]
   F: initialize()
   ↳Called by: F229:createGraphViewer,F242:_bindStateEvents,F242:setClusterRenderer | Calls: F249:if,F248:if,F247:destroy
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F229:createGraphViewer],[F242:_bindStateEvents],[F242:setClusterRenderer]
   F: destroy()
   ↳Called by: F247:if,F247:initialize,F248:initialize | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F247:if],[F247:initialize],[F248:initialize]
   F: if(this.events?.destroy)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: bindSelection()
   ↳Called by: F248:if,F248:destroy,F248:initialize | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F248:if],[F248:destroy],[F248:initialize]
   F: if(!this.events ||
            !this.selection)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(additive)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(!node)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(node.scope !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(additive)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(additive)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(this._suppressNextClick)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(this.state?.subscribe)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: bindNavigation()
   ↳Calls: F233:zoomToNode,F249:if,F248:if
   F: if(!this.events ||
            !this.navigation)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: on(INTERACTION_EVENTS.DOUBLE_CLICK,event)
   ↳Calls: F233:zoomToNode,F249:if,F248:if
---

F250│selection.js│308
C: SelectionManager←EventEmitter│[clear,if,hasSelection,selectNode,if,deselectNode,toggleNode,isNodeSelected,getSelectedNodes,selectEdge,+10]
C: SelectionManager←EventEmitter│[clear,if,hasSelection,selectNode,if,deselectNode,toggleNode,isNodeSelected,getSelectedNodes,selectEdge,+10]
   F: clear()
   ↳Called by: F236:emit,F236:catch,F236:for | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F236:emit],[F236:catch],[F236:for]
   F: if(changed)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: hasSelection()
   ↳Called by: F250:if,F250:clear | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F250:if],[F250:clear]
   F: selectNode(nodeId,additive)
   ↳Called by: F240:subscribe,F248:bindSelection,F250:if | Calls: F249:if,F250:getSelectedNodes,F248:if
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F240:subscribe],[F248:bindSelection],[F250:if]
   F: if(!additive)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: deselectNode(nodeId)
   ↳Called by: F250:if,F250:selectNode,F250:clear | Calls: F249:if,F250:getSelectedNodes,F248:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F250:if],[F250:selectNode],[F250:clear]
   F: toggleNode(nodeId)
   ↳Called by: F250:if,F248:bindSelection,F250:clear | Calls: F249:if,F250:getSelectedNodes,F248:if
   ↳Impact: 🔴HIGH (9 dependents) | Breaks: [F250:if],[F248:bindSelection],[F250:clear]
   F: isNodeSelected(nodeId)
   ↳Called by: F250:selectNode,F250:toggleNode,F250:deselectNode | Calls: F249:if,F250:getSelectedNodes,F248:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F250:selectNode],[F250:toggleNode],[F250:deselectNode]
   F: getSelectedNodes()
   ↳Called by: F250:deselectNode,F250:isNodeSelected,F249:onPointerDown | Calls: F249:if,F250:getSelectedEdges,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F250:deselectNode],[F250:isNodeSelected],[F249:onPointerDown]
   F: selectEdge(edgeId,additive)
   ↳Called by: F250:getSelectedNodes,F250:toggleNode,F250:isNodeSelected | Calls: F249:if,F250:selectCluster,F250:getSelectedEdges
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F250:getSelectedNodes],[F250:toggleNode],[F250:isNodeSelected]
   F: if(!additive)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: deselectEdge(edgeId)
   ↳Called by: F250:getSelectedNodes,F250:toggleNode,F250:isNodeSelected | Calls: F249:if,F250:selectCluster,F250:getSelectedEdges
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F250:getSelectedNodes],[F250:toggleNode],[F250:isNodeSelected]
   F: toggleEdge(edgeId)
   ↳Called by: F250:selectEdge,F250:getSelectedNodes,F250:isNodeSelected | Calls: F249:if,F250:selectCluster,F250:getSelectedEdges
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F250:selectEdge],[F250:getSelectedNodes],[F250:isNodeSelected]
   F: isEdgeSelected(edgeId)
   ↳Called by: F250:selectEdge,F250:getSelectedNodes,F250:isNodeSelected | Calls: F249:if,F250:selectCluster,F250:getSelectedEdges
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F250:selectEdge],[F250:getSelectedNodes],[F250:isNodeSelected]
   F: getSelectedEdges()
   ↳Called by: F250:selectEdge,F250:getSelectedNodes,F250:isEdgeSelected | Calls: F249:if,F250:selectCluster,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F250:selectEdge],[F250:getSelectedNodes],[F250:isEdgeSelected]
   F: selectCluster(clusterId,additive)
   ↳Called by: F250:selectEdge,F250:getSelectedEdges,F250:isEdgeSelected | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F250:selectEdge],[F250:getSelectedEdges],[F250:isEdgeSelected]
   F: if(!additive)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: deselectCluster(clusterId)
   ↳Called by: F250:selectCluster,F250:getSelectedEdges,F250:isEdgeSelected | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F250:selectCluster],[F250:getSelectedEdges],[F250:isEdgeSelected]
   F: toggleCluster(clusterId)
   ↳Called by: F250:selectCluster,F250:getSelectedEdges,F250:isEdgeSelected | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F250:selectCluster],[F250:getSelectedEdges],[F250:isEdgeSelected]
   F: isClusterSelected(clusterId)
   ↳Called by: F250:getSelectedEdges,F250:deselectCluster,F250:toggleCluster | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F250:getSelectedEdges],[F250:deselectCluster],[F250:toggleCluster]
---
