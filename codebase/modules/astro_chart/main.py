from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, json

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
SUBS_FILE = os.path.join(BASE_PATH, "subsections.json")

app = FastAPI(title="AstroChart")

static_dir = os.path.join(BASE_PATH, "static")
app.mount("/static", StaticFiles(directory=BASE_PATH), name="static")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _load():
    if not os.path.exists(SUBS_FILE):
        return {}
    try:
        with open(SUBS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    tmp = SUBS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, SUBS_FILE)


@app.get("/")
async def root():
    return FileResponse(os.path.join(BASE_PATH, "index.html"))


@app.get("/api/subsections")
async def get_subsections():
    return {"subsections": _load()}


class SubsectionsBody(BaseModel):
    subsections: dict


@app.put("/api/subsections")
async def put_subsections(body: SubsectionsBody):
    _save(body.subsections)
    return {"ok": True, "count": len(body.subsections)}


if __name__ == "__main__":
    import uvicorn
    print("AstroChart server starting at http://localhost:8002", flush=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=False)