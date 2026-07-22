# 📂 web
Generated: 2026-07-21 18:31:40
Files: 3

---

F231│bootstrap.js│88
F: hideLoadingOverlay()
   ↳Called by: F231:updateSummary,F231:bootstrap | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F231:updateSummary],[F231:bootstrap]
F: showLoading(message)
   ↳Called by: F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F231:hideLoadingOverlay]
F: showLoadError(message)
   ↳Called by: F231:hideLoadingOverlay,F231:showLoading,F231:showLoadError | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F231:hideLoadingOverlay],[F231:showLoading],[F231:showLoadError]
F: updateSummary(graphData)
   ↳Called by: F231:hideLoadingOverlay,F231:showLoading,F231:showLoadError | Calls: F249:if,F236:catch,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F231:hideLoadingOverlay],[F231:showLoading],[F231:showLoadError]
F: bootstrap()
   ↳Called by: F231:showLoadError,F231:updateSummary,F231:showLoading | Calls: F249:if,F236:catch,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F231:showLoadError],[F231:updateSummary],[F231:showLoading]
---

F230│graph_viewer.html│580
D: ●core/constants.js,core/state.js,core/types.js,data:,,render/nodes.js,+10
T: Jinja2/Django
---

F229│graph_viewer.js│659
C: GraphViewer│[if,initialize,if,_initialRender,if,if]
F: createGraphViewer(graphData,options)
   ↳Called by: F231:updateSummary,F231:bootstrap | Calls: F229:initialize,F242:initialize,F247:initialize
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F231:updateSummary],[F231:bootstrap]
C: GraphViewer│[if,initialize,if,_initialRender,if,if]
   F: if(!this.graphData)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: initialize()
   ↳Called by: F229:createGraphViewer,F242:_bindStateEvents,F242:setClusterRenderer | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F229:createGraphViewer],[F242:_bindStateEvents],[F242:setClusterRenderer]
   F: if(this._hadViewportSnapshot &&
            this.viewport)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: _initialRender()
   ↳Called by: F229:initialize | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F229:initialize]
   F: if(nodeCount >)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(this._hadViewportSnapshot)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
---
