# 📂 static
Generated: 2026-07-05 14:01:18
Files: 2

---

F011│graph.js│193
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
C: GraphVisualization│[init,setupMouseControls,if,onMouseClick,if,setupWebSocket,if,loadTopics,loadGraph,createGraph,+2]
   F: init()
   ↳Calls: F011:setupMouseControls
   F: setupMouseControls()
   ↳Called by: F011:init | Calls: F011:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F011:init]
   F: if(isMouseDown)
   ↳Called by: F011:setupWebSocket,F011:createGraph,F011:loadTopics | Calls: F011:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F011:setupWebSocket],[F011:createGraph],[F011:loadTopics]
   F: onMouseClick(event)
   ↳Called by: F011:if | Calls: F011:setupWebSocket,F011:loadTopics,F011:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F011:if]
   F: if(intersects.length > 0)
   ↳Called by: F011:setupWebSocket,F011:createGraph,F011:loadTopics | Calls: F011:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F011:setupWebSocket],[F011:createGraph],[F011:loadTopics]
   F: setupWebSocket()
   ↳Called by: F011:onMouseClick | Calls: F011:createGraph,F011:loadTopics,F011:loadGraph
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F011:onMouseClick]
   F: if(message.type)
   ↳Called by: F011:setupWebSocket,F011:createGraph,F011:loadTopics | Calls: F011:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F011:setupWebSocket],[F011:createGraph],[F011:loadTopics]
   F: loadTopics()
   ↳Called by: F011:onMouseClick,F011:setupWebSocket | Calls: F011:createGraph,F011:loadGraph,F011:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F011:onMouseClick],[F011:setupWebSocket]
   F: loadGraph()
   ↳Called by: F011:setupWebSocket,F011:loadTopics | Calls: F011:createNode,F011:createGraph,F011:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F011:setupWebSocket],[F011:loadTopics]
   F: createGraph()
   ↳Called by: F011:setupWebSocket,F011:loadTopics,F011:loadGraph | Calls: F011:createNode,F011:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F011:setupWebSocket],[F011:loadTopics],[F011:loadGraph]
   F: if(edge)
   ↳Called by: F011:setupWebSocket,F011:createGraph,F011:loadTopics | Calls: F011:onMouseClick
   ↳Impact: 🔴HIGH (6 dependents) | Breaks: [F011:setupWebSocket],[F011:createGraph],[F011:loadTopics]
   F: createNode(nodeData,index)
   ↳Called by: F011:createGraph,F011:loadGraph
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F011:createGraph],[F011:loadGraph]
---

F012│index.html│32
D: ●/static/graph.js
T: Static HTML
---
