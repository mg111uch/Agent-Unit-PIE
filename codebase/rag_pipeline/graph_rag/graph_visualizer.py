# === FastAPI Backend for Graph Database Visualization ===
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import json
from graph_db import CodeGraphDB

app = FastAPI(title="Code Graph Database API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database connection
db = CodeGraphDB()

# Pydantic models for API
class NodeResponse(BaseModel):
    id: int
    name: str
    type: str
    file_path: str
    line_start: Optional[int]
    line_end: Optional[int]
    content: Optional[str]
    metadata: Optional[str]

class EdgeResponse(BaseModel):
    id: int
    source_id: int
    target_id: int
    relationship_type: str
    metadata: Optional[str]

class GraphDataResponse(BaseModel):
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]

class SearchRequest(BaseModel):
    query: str
    node_type: Optional[str] = None

class ContextRequest(BaseModel):
    node_name: str
    depth: int = 2

@app.get("/")
async def root():
    """Serve the main visualization page."""
    return FileResponse("static/index.html")

@app.get("/api")
async def api_root():
    """Root endpoint with API information."""
    return {
        "message": "Code Graph Database API",
        "version": "1.0.0",
        "endpoints": [
            "/graph - Get all graph data",
            "/nodes/search - Search nodes",
            "/nodes/{node_id}/neighbors - Get node neighbors",
            "/context - Get graph context for a node",
            "/stats - Get graph statistics"
        ]
    }

@app.get("/graph", response_model=GraphDataResponse)
async def get_graph_data():
    """Get all nodes and edges in the graph."""
    try:
        # Get all nodes
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()

            # Get nodes
            cursor.execute("SELECT * FROM nodes")
            nodes_data = cursor.fetchall()
            nodes = []
            for row in nodes_data:
                nodes.append(NodeResponse(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    file_path=row[3],
                    line_start=row[4],
                    line_end=row[5],
                    content=row[6],
                    metadata=row[7]
                ))

            # Get edges
            cursor.execute("SELECT * FROM edges")
            edges_data = cursor.fetchall()
            edges = []
            for row in edges_data:
                edges.append(EdgeResponse(
                    id=row[0],
                    source_id=row[1],
                    target_id=row[2],
                    relationship_type=row[3],
                    metadata=row[4]
                ))

        return GraphDataResponse(nodes=nodes, edges=edges)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving graph data: {str(e)}")

@app.post("/nodes/search", response_model=List[NodeResponse])
async def search_nodes(request: SearchRequest):
    """Search for nodes by name or content."""
    try:
        results = db.search_nodes(request.query, request.node_type)
        return [
            NodeResponse(
                id=r['id'],
                name=r['name'],
                type=r['type'],
                file_path=r['file_path'],
                line_start=r['line_start'],
                line_end=r['line_end'],
                content=r['content'],
                metadata=r['metadata']
            ) for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching nodes: {str(e)}")

@app.get("/nodes/{node_id}/neighbors", response_model=List[Dict[str, Any]])
async def get_node_neighbors(node_id: int, relationship_type: Optional[str] = None):
    """Get neighbors of a specific node."""
    try:
        neighbors = db.get_neighbors(node_id, relationship_type)
        return neighbors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting neighbors: {str(e)}")

@app.post("/context")
async def get_graph_context(request: ContextRequest):
    """Get graph context around a node for GraphRAG."""
    try:
        context = db.get_graph_context(request.node_name, request.depth)
        if not context:
            raise HTTPException(status_code=404, detail=f"Node '{request.node_name}' not found")
        return context
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting context: {str(e)}")

@app.get("/stats")
async def get_graph_stats():
    """Get statistics about the graph database."""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()

            # Count nodes by type
            cursor.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type")
            node_counts = dict(cursor.fetchall())

            # Count edges by relationship type
            cursor.execute("SELECT relationship_type, COUNT(*) FROM edges GROUP BY relationship_type")
            edge_counts = dict(cursor.fetchall())

            # Total counts
            cursor.execute("SELECT COUNT(*) FROM nodes")
            total_nodes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM edges")
            total_edges = cursor.fetchone()[0]

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_types": node_counts,
            "relationship_types": edge_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.post("/analyze")
async def reanalyze_codebase():
    """Re-analyze the codebase and update the graph database."""
    try:
        from graph_db import analyze_codebase
        db.clear_db()
        analyze_codebase(db, ".")
        return {"message": "Codebase re-analyzed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing codebase: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)