from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket
import os, json
from llm_compiler import compile_topic_llm

app = FastAPI(title="ArguGod")

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        await ws.send_json({"type": "ping"})

@app.get("/api/topics")
async def list_topics():
    topics_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topics")
    return {"topics": os.listdir(topics_dir) if os.path.exists(topics_dir) else []}

@app.get("/api/graph")
async def get_graph(topic: str = "theism_atheism"):
    path = os.path.join("topics", topic, "graph.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print("Invalid graph.json:", e)
    return {"nodes": [], "edges": []}   # safe fallback - no crash

@app.post("/api/compile/{topic}")
async def compile_topic(topic: str):
    return compile_topic_llm(topic)

@app.get("/api/mindmap")
async def get_mindmap():
    path = os.path.join("mindmaps", "local_user", "mindmap.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"topics": {}, "total_topics_explored": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)