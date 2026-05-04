# Graph Database and Visualization Features

## Overview

This project includes a code graph database for analysis and graph visualization features.

## Technology Stack

### Backend
- **SQLite**: Graph database for code analysis

### Architecture
- **Graph Database**: SQLite-based code relationship mapping

## Getting Started

### Prerequisites
```bash
# Activate conda environment
cd python/control/Popula
eval "$(conda shell.bash hook)" && conda activate myenv

# Install dependencies
pip install fastapi uvicorn pydantic
```

### Running the System

1. **Start the Server:**
```bash
python graph_server.py
```

2. **Access Interfaces:**
   - **Graph Visualizer**: http://localhost:8000/
   - **API Documentation**: http://localhost:8000/docs

## Code Graph Database

### Features
- **AST Analysis**: Automatic Python code parsing
- **Relationship Mapping**: Inheritance, imports, containment
- **Search & Query**: Find nodes by name, type, or content
- **Context Retrieval**: GraphRAG-ready neighbor analysis
- **133 Nodes, 132 Edges**: Complete codebase mapping

### Database Schema
```sql
-- Nodes: classes, functions, modules, imports
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    content TEXT,
    metadata TEXT
);

-- Edges: relationships between nodes
CREATE TABLE edges (
    id INTEGER PRIMARY KEY,
    source_id INTEGER,
    target_id INTEGER,
    relationship_type TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (source_id) REFERENCES nodes (id),
    FOREIGN KEY (target_id) REFERENCES nodes (id)
);
```

## Visualization Features

### Graph Visualizer
- Interactive force-directed layout
- Node type color coding
- Search and filtering
- Relationship exploration
- Zoom and pan controls

## Advanced Features

### GraphRAG Integration
- Code relationship mapping for AI context
- Semantic search capabilities
- Dependency analysis
- Refactoring assistance

## API Endpoints

### REST API
- `GET /`: Graph visualizer page
- `GET /graph`: All graph data
- `POST /nodes/search`: Search nodes
- `GET /nodes/{id}/neighbors`: Get node relationships
- `POST /context`: Get graph context
- `GET /stats`: Database statistics

## Development Notes

### Performance Considerations
- SQLite queries indexed for speed

### Extensibility
- Graph database expandable for new relationships

## Educational Value

This simulation demonstrates:
- **Graph Databases**: Code relationship mapping

## Contributing

The modular architecture makes it easy to:
- Extend the graph database schema

## Project Structure

```
python/rag_pipeline
├── graph_db.py              # SQLite graph database
├── graph_server.py         # FastAPI server with WebSockets
├── static/
│   ├── index.html          # Graph visualizer
├── code_graph.db           # SQLite database file