import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="GraphEditor")

app.mount("/static", StaticFiles(directory=BASE_PATH), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(BASE_PATH, "index.html"))


if __name__ == "__main__":
    import uvicorn

    print("GraphEditor server starting at http://localhost:8004", flush=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=False)