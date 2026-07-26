# 📂 static
Generated: 2026-07-26 16:20:18
Files: 3

---

F112│game.html│415
T: Static HTML
---

F149│graph.js│193
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
   F: init()
   ↳Calls: F149:setupMouseControls
   F: setupMouseControls()
   ↳Called by: F149:init | Calls: F149:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F149:init]
   F: if(isMouseDown)
   ↳Called by: F149:setupMouseControls,F149:createGraph,F149:setupWebSocket | Calls: F149:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F149:setupMouseControls],[F149:createGraph],[F149:setupWebSocket]
   F: onMouseClick(event)
   ↳Called by: F149:if | Calls: F149:setupWebSocket,F149:loadTopics,F149:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F149:if]
   F: if(intersects.length > 0)
   ↳Called by: F149:setupMouseControls,F149:createGraph,F149:setupWebSocket | Calls: F149:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F149:setupMouseControls],[F149:createGraph],[F149:setupWebSocket]
   F: setupWebSocket()
   ↳Called by: F149:onMouseClick | Calls: F149:loadGraph,F149:createGraph,F149:loadTopics
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F149:onMouseClick]
   F: if(message.type)
   ↳Called by: F149:setupMouseControls,F149:createGraph,F149:setupWebSocket | Calls: F149:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F149:setupMouseControls],[F149:createGraph],[F149:setupWebSocket]
   F: loadTopics()
   ↳Called by: F149:setupWebSocket,F149:onMouseClick | Calls: F149:loadGraph,F149:createGraph,F149:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F149:setupWebSocket],[F149:onMouseClick]
   F: loadGraph()
   ↳Called by: F149:setupWebSocket,F149:loadTopics | Calls: F149:createGraph,F149:if,F149:createNode
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F149:setupWebSocket],[F149:loadTopics]
   F: createGraph()
   ↳Called by: F149:setupWebSocket,F149:loadGraph,F149:loadTopics | Calls: F149:if,F149:createNode
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F149:setupWebSocket],[F149:loadGraph],[F149:loadTopics]
   F: if(edge)
   ↳Called by: F149:setupMouseControls,F149:createGraph,F149:setupWebSocket | Calls: F149:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F149:setupMouseControls],[F149:createGraph],[F149:setupWebSocket]
   F: createNode(nodeData,index)
   ↳Called by: F149:createGraph,F149:loadGraph
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F149:createGraph],[F149:loadGraph]
---

F150│index.html│32
D: ●/static/graph.js
T: Static HTML
---
