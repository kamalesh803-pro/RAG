"""
main.py
───────
FastAPI server – serves the REST API and the frontend static files.

Run with:  uvicorn main:app --reload
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rag_pipeline import ingest_document, ask_question, clear_store

# ── App setup ────────────────────────────────────────────────────────
app = FastAPI(
    title="RAG Web Application",
    description="Retrieval Augmented Generation powered by FAISS + Ollama",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────
class QuestionRequest(BaseModel):
    question: str
    k: int = 4


class UploadResponse(BaseModel):
    success: bool
    message: str
    details: dict | None = None


class AnswerResponse(BaseModel):
    answer: str
    sources: list


# ── Endpoints ────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "RAG server is running"}


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF or TXT document for ingestion."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    allowed = {"pdf", "txt"}
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Please upload a PDF or TXT file.",
        )

    try:
        contents = await file.read()
        stats = ingest_document(contents, file.filename)
        return UploadResponse(
            success=True,
            message=f"'{file.filename}' processed successfully — {stats['chunks']} chunks indexed.",
            details=stats,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing error: {exc}")


@app.post("/ask", response_model=AnswerResponse)
async def ask(req: QuestionRequest):
    """Ask a question about the uploaded documents."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = ask_question(req.question, k=req.k)
        return AnswerResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {exc}")


@app.post("/clear")
async def clear():
    """Clear all indexed documents."""
    clear_store()
    return {"success": True, "message": "Vector store cleared."}


# ── Serve frontend ──────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
