# 📂 render
Generated: 2026-07-21 18:31:40
Files: 6

---

F243│clusters.js│308
C: ClusterRenderer│[render,for,if,createCluster,if,if,createBackground,createLabel,getClusterNodes,getBorderColor]
C: ClusterRenderer│[render,for,if,createCluster,if,if,createBackground,createLabel,getClusterNodes,getBorderColor]
   F: render(layer,state,items)
   ↳Called by: F242:initialize,F242:whenMeasured,F242:check | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F242:initialize],[F242:whenMeasured],[F242:check]
   F: for(const cluster of clusters)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: if(!element)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: createCluster(cluster,state)
   ↳Called by: F243:render,F243:if,F243:for | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F243:render],[F243:if],[F243:for]
   F: if(!nodes.length)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(state.selectedClusterId)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: createBackground(bounds,cluster,state)
   F: createLabel(bounds,cluster,state)
   ↳Calls: F249:if,F248:if,F241:if
   F: getClusterNodes(cluster,state)
   ↳Called by: F243:createLabel | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F243:createLabel]
   F: getBorderColor(cluster,state)
   ↳Called by: F243:getClusterNodes | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F243:getClusterNodes]
---

F241│edges.js│531
C: EdgeRenderer│[render,for,if,createEdge,if,if,if,if,if,shouldRenderLabel,+2]
C: EdgeRenderer│[render,for,if,createEdge,if,if,if,if,if,shouldRenderLabel,+2]
   F: render(layer,state,items)
   ↳Called by: F242:initialize,F242:whenMeasured,F242:check | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F242:initialize],[F242:whenMeasured],[F242:check]
   F: for(const edge of edges)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: if(!source || !target)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: createEdge(edge,source,target,state,count)
   ↳Called by: F241:if | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F241:if]
   F: if(state.selectedEdgeId)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(count > 1)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(count > 1)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(count > 1)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(badge)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: shouldRenderLabel(state)
   ↳Calls: F249:if,F248:if,F241:if
   F: if(graphType)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: createLine(edge,source,target,state)
   ↳Called by: F241:shouldRenderLabel | Calls: F232:nodeConnectionPoints
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F241:shouldRenderLabel]
---

F245│nodes.js│509
C: NodeRenderer│[render,for,createNode,if,if,if,if,if,if,if,+2]
C: NodeRenderer│[render,for,createNode,if,if,if,if,if,if,if,+2]
   F: render(layer,state,items)
   ↳Called by: F242:initialize,F242:whenMeasured,F242:check | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F242:initialize],[F242:whenMeasured],[F242:check]
   F: for(const node of nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: createNode(node,state)
   ↳Called by: F245:render,F300:loadGraph,F300:createGraph | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F245:render],[F300:loadGraph],[F300:createGraph]
   F: if(lod)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(state.selectedNodeId)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(lod !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(lod)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(node.entry_point)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(node.risk_level)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(node.scope)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: createDotNode(node,state)
   ↳Calls: F245:createBackgroundRect
   F: createBackgroundRect(node,width,height,state)
   ↳Called by: F245:createDotNode
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F245:createDotNode]
---

F242│renderer.js│634
C: GraphRenderer←EventEmitter│[setNodeRenderer,setEdgeRenderer,setClusterRenderer,_bindStateEvents,if,initialize,whenMeasured,if,if,if,+6]
F: yieldToBrowser()
   ↳Calls: F249:if,F248:if,F241:if
F: check()
   ↳Called by: F242:initialize,F242:whenMeasured,F242:check | Calls: F249:if,F248:if,F245:render
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F242:initialize],[F242:whenMeasured],[F242:check]
C: GraphRenderer←EventEmitter│[setNodeRenderer,setEdgeRenderer,setClusterRenderer,_bindStateEvents,if,initialize,whenMeasured,if,if,if,+6]
   F: setNodeRenderer(renderer)
   ↳Calls: F249:if,F248:if,F242:setClusterRenderer
   F: setEdgeRenderer(renderer)
   ↳Called by: F242:setNodeRenderer | Calls: F249:if,F248:if,F242:setClusterRenderer
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F242:setNodeRenderer]
   F: setClusterRenderer(renderer)
   ↳Called by: F242:setNodeRenderer,F242:setEdgeRenderer | Calls: F249:if,F242:initialize,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F242:setNodeRenderer],[F242:setEdgeRenderer]
   F: _bindStateEvents()
   ↳Called by: F242:setNodeRenderer,F242:setClusterRenderer,F242:setEdgeRenderer | Calls: F249:if,F242:initialize,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F242:setNodeRenderer],[F242:setClusterRenderer],[F242:setEdgeRenderer]
   F: if(!this.state)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F247:initialize,F248:initialize,F242:initialize
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: initialize()
   ↳Called by: F229:createGraphViewer,F242:_bindStateEvents,F242:setClusterRenderer | Calls: F249:if,F248:if,F245:render
   ↳Impact: 🔴HIGH (4 dependents) | Breaks: [F229:createGraphViewer],[F242:_bindStateEvents],[F242:setClusterRenderer]
   F: whenMeasured(callback)
   ↳Called by: F242:_bindStateEvents,F242:initialize,F242:if | Calls: F249:if,F248:if,F245:render
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F242:_bindStateEvents],[F242:initialize],[F242:if]
   F: if(!this.svg)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F247:initialize,F248:initialize,F242:initialize
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(rect.width > 0 &&
                rect.height > 0)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F247:initialize,F248:initialize,F242:initialize
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(polls >)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F247:initialize,F248:initialize,F242:initialize
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(typeof requestAnimationFrame)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F247:initialize,F248:initialize,F242:initialize
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: render()
   ↳Called by: F242:initialize,F242:whenMeasured,F242:check | Calls: F242:updateSelection,F249:if,F248:if
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F242:initialize],[F242:whenMeasured],[F242:check]
   F: updateSelection()
   ↳Called by: F242:render | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F242:render]
   F: if(!this.state)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F247:initialize,F248:initialize,F242:initialize
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: _toggleSelectedClass(renderer,previousId,currentId)
   ↳Called by: F242:updateSelection | Calls: F250:if,F244:if,F238:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F242:updateSelection]
   F: if(!renderer || typeof renderer.getElement !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F247:initialize,F248:initialize,F242:initialize
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
---

F246│styles.js│163
F: getNodeColor(nodeType)
   ↳Calls: F246:getRiskColor,F246:getEdgeStyle
F: getRiskColor(riskLevel)
   ↳Called by: F246:getNodeColor | Calls: F246:getEdgeStyle
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F246:getNodeColor]
F: getEdgeStyle(edgeType)
   ↳Called by: F246:getRiskColor,F246:getNodeColor
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F246:getRiskColor],[F246:getNodeColor]
---

F244│viewport_culler.js│237
C: ViewportCuller│[getVisibleBounds,if,if,isNodeVisible,resolveEdgeEndpoint,if,computeLod,isClusterVisible,if,if,+6]
C: ViewportCuller│[getVisibleBounds,if,if,isNodeVisible,resolveEdgeEndpoint,if,computeLod,isClusterVisible,if,if,+6]
   F: getVisibleBounds()
   ↳Calls: F249:if,F248:if,F241:if
   F: if(!this.svg)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(rect.width)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: isNodeVisible(node,bounds)
   ↳Called by: F244:if,F244:getVisibleBounds | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F244:if],[F244:getVisibleBounds]
   F: resolveEdgeEndpoint(node)
   ↳Called by: F244:isNodeVisible | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F244:isNodeVisible]
   F: if(node.scope !)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: computeLod(node,zoom)
   ↳Called by: F244:resolveEdgeEndpoint,F244:isNodeVisible | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F244:resolveEdgeEndpoint],[F244:isNodeVisible]
   F: isClusterVisible(cluster,bounds)
   ↳Called by: F244:computeLod,F244:resolveEdgeEndpoint | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F244:computeLod],[F244:resolveEdgeEndpoint]
   F: if(!cluster.bounds &&
            !cluster.node_ids?.length)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: if(cluster.bounds)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: cull(graph)
   ↳Called by: F244:computeLod,F244:isClusterVisible | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F244:computeLod],[F244:isClusterVisible]
   F: if(!bounds || !graph)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const node of graph.nodes)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: for(const edge of graph.edges)
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
   F: if(!source || !target)
   ↳Called by: F234:setZoom,F234:updateTransform,F231:hideLoadingOverlay | Calls: F249:if,F248:if,F241:if
   ↳Impact: 🔴HIGH (149 dependents) | Breaks: [F234:setZoom],[F234:updateTransform],[F231:hideLoadingOverlay]
   F: for(const cluster of graph.clusters ?? [])
   ↳Called by: F235:for,F245:render,F236:off | Calls: F249:if,F236:for,F248:if
   ↳Impact: 🔴HIGH (33 dependents) | Breaks: [F235:for],[F245:render],[F236:off]
---
