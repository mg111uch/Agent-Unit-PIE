# 📂 static
Generated: 2026-07-17 18:00:11
Files: 2

---

F010│graph.js│193
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
   F: init()
   ↳Calls: F010:setupMouseControls
   F: setupMouseControls()
   ↳Called by: F010:init | Calls: F010:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F010:init]
   F: if(isMouseDown)
   ↳Called by: F010:loadGraph,F010:setupWebSocket,F010:setupMouseControls | Calls: F010:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F010:loadGraph],[F010:setupWebSocket],[F010:setupMouseControls]
   F: onMouseClick(event)
   ↳Called by: F010:if | Calls: F010:loadTopics,F010:if,F010:setupWebSocket
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F010:if]
   F: if(intersects.length > 0)
   ↳Called by: F010:loadGraph,F010:setupWebSocket,F010:setupMouseControls | Calls: F010:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F010:loadGraph],[F010:setupWebSocket],[F010:setupMouseControls]
   F: setupWebSocket()
   ↳Called by: F010:onMouseClick | Calls: F010:loadTopics,F010:loadGraph,F010:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F010:onMouseClick]
   F: if(message.type)
   ↳Called by: F010:loadGraph,F010:setupWebSocket,F010:setupMouseControls | Calls: F010:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F010:loadGraph],[F010:setupWebSocket],[F010:setupMouseControls]
   F: loadTopics()
   ↳Called by: F010:onMouseClick,F010:setupWebSocket | Calls: F010:loadGraph,F010:if,F010:createGraph
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F010:onMouseClick],[F010:setupWebSocket]
   F: loadGraph()
   ↳Called by: F010:loadTopics,F010:setupWebSocket | Calls: F010:createNode,F010:if,F010:createGraph
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F010:loadTopics],[F010:setupWebSocket]
   F: createGraph()
   ↳Called by: F010:loadTopics,F010:loadGraph,F010:setupWebSocket | Calls: F010:if,F010:createNode
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F010:loadTopics],[F010:loadGraph],[F010:setupWebSocket]
   F: if(edge)
   ↳Called by: F010:loadGraph,F010:setupWebSocket,F010:setupMouseControls | Calls: F010:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F010:loadGraph],[F010:setupWebSocket],[F010:setupMouseControls]
   F: createNode(nodeData,index)
   ↳Called by: F010:loadGraph,F010:createGraph
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F010:loadGraph],[F010:createGraph]
---

F011│index.html│32
D: ●/static/graph.js
T: Static HTML
---
