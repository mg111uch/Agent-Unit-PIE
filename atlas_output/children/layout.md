# 📂 layout
Generated: 2026-07-21 18:31:40
Files: 1

---

F235│layout.js│545
C: GraphLayoutEngine│[hierarchical,circular,if,grid,clusterGrid,if,for,for,if]
F: assignLevel(nodeId,depth)
   ↳Called by: F235:assignLevel,F235:hierarchical | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F235:assignLevel],[F235:hierarchical]
F: refresh(box,members)
   ↳Called by: F248:resetStaleSuppress,F235:refresh | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F248:resetStaleSuppress],[F235:refresh]
C: GraphLayoutEngine│[hierarchical,circular,if,grid,clusterGrid,if,for,for,if]
   F: hierarchical(graph,options)
   ↳Calls: F249:if,F236:for,F248:if
   F: circular(graph,options)
   ↳Calls: F249:if,F248:if,F241:if
   F: if(count)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F235:clusterGrid,F235:grid
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: grid(graph,options)
   ↳Called by: F235:if,F235:circular | Calls: F235:clusterGrid
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F235:if],[F235:circular]
   F: clusterGrid(graph,options)
   ↳Called by: F235:if,F235:circular,F235:grid | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F235:if],[F235:circular],[F235:grid]
   F: if(!nodes.length)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F235:clusterGrid,F235:grid
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const node of nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const node of nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: if(index !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F235:clusterGrid,F235:grid
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
---
