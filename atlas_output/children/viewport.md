# 📂 viewport
Generated: 2026-07-21 18:31:40
Files: 2

---

F233│navigation.js│222
C: GraphNavigation│[fitGraph,if,centerOnNode,if,zoomToNode,if,centerOnCluster,if,zoomToCluster,if,+9]
C: GraphNavigation│[fitGraph,if,centerOnNode,if,zoomToNode,if,centerOnCluster,if,zoomToCluster,if,+9]
   F: fitGraph()
   ↳Calls: F233:zoomToNode,F249:if,F248:if
   F: if(!nodes.length)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: centerOnNode(nodeId)
   ↳Called by: F233:if,F233:fitGraph | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F233:if],[F233:fitGraph]
   F: if(!node)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: zoomToNode(nodeId,zoom)
   ↳Called by: F233:centerOnNode,F233:if,F248:on | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F233:centerOnNode],[F233:if],[F248:on]
   F: if(!node)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: centerOnCluster(clusterId)
   ↳Called by: F233:zoomToNode,F233:centerOnNode | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F233:zoomToNode],[F233:centerOnNode]
   F: if(!bounds)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: zoomToCluster(clusterId,zoom)
   ↳Called by: F233:zoomToNode,F233:centerOnCluster | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F233:zoomToNode],[F233:centerOnCluster]
   F: if(!bounds)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: fitCluster(clusterId)
   ↳Called by: F233:zoomToCluster | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F233:zoomToCluster]
   F: if(!bounds)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: zoomToBounds(bounds)
   ↳Called by: F233:fitCluster,F233:zoomToCluster | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F233:fitCluster],[F233:zoomToCluster]
   F: if(!bounds)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: getClusterBounds(clusterId)
   ↳Called by: F233:fitCluster,F233:zoomToBounds | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F233:fitCluster],[F233:zoomToBounds]
   F: if(!cluster)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(!nodes.length)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F233:zoomToNode,F249:if,F248:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: resetView()
   ↳Calls: F233:getCurrentView
   F: getCurrentView()
   ↳Called by: F233:resetView
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F233:resetView]
---

F234│viewport.js│250
C: ViewportController│[setZoom,if,zoomIn,zoomOut,setPan,panBy,screenToGraph,graphToScreen,centerOn,fitBounds,+7]
C: ViewportController│[setZoom,if,zoomIn,zoomOut,setPan,panBy,screenToGraph,graphToScreen,centerOn,fitBounds,+7]
   F: setZoom(zoom,anchorX,anchorY)
   ↳Calls: F249:if,F234:zoomOut,F248:if
   F: if(anchorX)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F234:panBy,F234:setPan,F234:zoomIn
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: zoomIn(factor)
   ↳Called by: F234:setZoom,F234:if | Calls: F234:graphToScreen,F234:panBy,F234:zoomOut
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F234:setZoom],[F234:if]
   F: zoomOut(factor)
   ↳Called by: F234:zoomIn,F234:setZoom,F234:if | Calls: F234:graphToScreen,F234:screenToGraph,F234:panBy
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F234:zoomIn],[F234:setZoom],[F234:if]
   F: setPan(x,y)
   ↳Called by: F234:zoomIn,F234:setZoom,F234:if | Calls: F234:graphToScreen,F234:panBy,F234:screenToGraph
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F234:zoomIn],[F234:setZoom],[F234:if]
   F: panBy(dx,dy)
   ↳Called by: F234:zoomIn,F234:setPan,F234:if | Calls: F234:graphToScreen,F234:centerOn,F234:screenToGraph
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F234:zoomIn],[F234:setPan],[F234:if]
   F: screenToGraph(screenX,screenY)
   ↳Called by: F234:panBy,F234:zoomIn,F234:setPan | Calls: F234:centerOn,F234:graphToScreen
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F234:panBy],[F234:zoomIn],[F234:setPan]
   F: graphToScreen(graphX,graphY)
   ↳Called by: F234:panBy,F234:zoomOut,F234:screenToGraph | Calls: F234:fitBounds,F249:if,F248:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F234:panBy],[F234:zoomOut],[F234:screenToGraph]
   F: centerOn(graphX,graphY)
   ↳Called by: F234:graphToScreen,F234:screenToGraph,F234:panBy | Calls: F234:fitBounds,F249:if,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F234:graphToScreen],[F234:screenToGraph],[F234:panBy]
   F: fitBounds(bounds,padding)
   ↳Called by: F234:centerOn,F234:graphToScreen | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F234:centerOn],[F234:graphToScreen]
   F: if(!bounds ||
            bounds.width <)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F234:panBy,F234:setPan,F234:zoomIn
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: reset()
   ↳Called by: F234:fitBounds | Calls: F249:if,F234:updateTransform,F234:_syncState
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F234:fitBounds]
   F: updateTransform()
   ↳Called by: F234:reset | Calls: F249:if,F234:_syncState,F248:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F234:reset]
   F: _syncState()
   ↳Called by: F234:updateTransform,F234:reset | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F234:updateTransform],[F234:reset]
   F: if(this.state)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F234:panBy,F234:setPan,F234:zoomIn
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: _resolveElement(value)
   ↳Called by: F234:updateTransform,F234:reset,F234:_syncState | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F234:updateTransform],[F234:reset],[F234:_syncState]
   F: if(value instanceof Element)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F234:panBy,F234:setPan,F234:zoomIn
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
---
