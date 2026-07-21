# 📂 static
Generated: 2026-07-21 18:31:40
Files: 4

---

F264│game.html│415
T: Static HTML
---

F300│graph.js│193
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
   F: init()
   ↳Calls: F300:setupMouseControls
   F: setupMouseControls()
   ↳Called by: F300:init | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F300:init]
   F: if(isMouseDown)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F300:onMouseClick
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: onMouseClick(event)
   ↳Called by: F300:if | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F300:if]
   F: if(intersects.length > 0)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F300:onMouseClick
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: setupWebSocket()
   ↳Called by: F300:onMouseClick | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F300:onMouseClick]
   F: if(message.type)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F300:onMouseClick
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: loadTopics()
   ↳Called by: F300:setupWebSocket,F300:onMouseClick | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F300:setupWebSocket],[F300:onMouseClick]
   F: loadGraph()
   ↳Called by: F300:setupWebSocket,F300:loadTopics | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F300:setupWebSocket],[F300:loadTopics]
   F: createGraph()
   ↳Called by: F300:setupWebSocket,F300:loadGraph,F300:loadTopics | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F300:setupWebSocket],[F300:loadGraph],[F300:loadTopics]
   F: if(edge)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F300:onMouseClick
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: createNode(nodeData,index)
   ↳Called by: F245:render,F300:loadGraph,F300:createGraph
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F245:render],[F300:loadGraph],[F300:createGraph]
---

F020│index.html│411
T: Static HTML
---

F301│index.html│32
D: ●/static/graph.js
T: Static HTML
---
