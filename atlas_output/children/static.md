# 📂 static
Generated: 2026-07-23 14:15:38
Files: 3

---

F111│game.html│415
T: Static HTML
---

F148│graph.js│193
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
   F: init()
   ↳Calls: F148:setupMouseControls
   F: setupMouseControls()
   ↳Called by: F148:init | Calls: F148:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F148:init]
   F: if(isMouseDown)
   ↳Called by: F148:createGraph,F148:loadGraph,F148:onMouseClick | Calls: F148:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F148:createGraph],[F148:loadGraph],[F148:onMouseClick]
   F: onMouseClick(event)
   ↳Called by: F148:if | Calls: F148:if,F148:setupWebSocket,F148:loadTopics
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F148:if]
   F: if(intersects.length > 0)
   ↳Called by: F148:createGraph,F148:loadGraph,F148:onMouseClick | Calls: F148:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F148:createGraph],[F148:loadGraph],[F148:onMouseClick]
   F: setupWebSocket()
   ↳Called by: F148:onMouseClick | Calls: F148:if,F148:createGraph,F148:loadGraph
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F148:onMouseClick]
   F: if(message.type)
   ↳Called by: F148:createGraph,F148:loadGraph,F148:onMouseClick | Calls: F148:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F148:createGraph],[F148:loadGraph],[F148:onMouseClick]
   F: loadTopics()
   ↳Called by: F148:setupWebSocket,F148:onMouseClick | Calls: F148:if,F148:createGraph,F148:loadGraph
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F148:setupWebSocket],[F148:onMouseClick]
   F: loadGraph()
   ↳Called by: F148:setupWebSocket,F148:loadTopics | Calls: F148:if,F148:createGraph,F148:createNode
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F148:setupWebSocket],[F148:loadTopics]
   F: createGraph()
   ↳Called by: F148:loadGraph,F148:setupWebSocket,F148:loadTopics | Calls: F148:if,F148:createNode
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F148:loadGraph],[F148:setupWebSocket],[F148:loadTopics]
   F: if(edge)
   ↳Called by: F148:createGraph,F148:loadGraph,F148:onMouseClick | Calls: F148:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F148:createGraph],[F148:loadGraph],[F148:onMouseClick]
   F: createNode(nodeData,index)
   ↳Called by: F148:createGraph,F148:loadGraph
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F148:createGraph],[F148:loadGraph]
---

F149│index.html│32
D: ●/static/graph.js
T: Static HTML
---
