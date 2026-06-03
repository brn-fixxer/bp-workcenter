from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI(title="BP WorkCenter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.get("/{full_path:path}")
def serve_frontend(full_path: str = ""):
    """Sirve el index.html para cualquier ruta (SPA)."""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"status": "ok", "message": "index.html no encontrado"}
