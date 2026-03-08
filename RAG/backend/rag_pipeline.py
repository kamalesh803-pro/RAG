"""
rag_pipeline.py
───────────────
Document ingestion (PDF / TXT), chunking, and the RAG question-answering chain.
"""

import io
from typing import List, Dict, Any

from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_ollama import OllamaLLM

from vector_store import VectorStoreManager


# ── Globals ──────────────────────────────────────────────────────────
vector_manager = VectorStoreManager()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)

llm = OllamaLLM(
    model="llama3.2:3b",
    temperature=0.3,
)


# ── Text extraction ─────────────────────────────────────────────────
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Return all text from a PDF file given as raw bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
    return "\n\n".join(pages_text)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Return text from a .txt file given as raw bytes."""
    return file_bytes.decode("utf-8", errors="replace")


# ── Ingestion ────────────────────────────────────────────────────────
def ingest_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract → chunk → embed → store.  Returns stats about what was ingested."""
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext == "txt":
        raw_text = extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    if not raw_text.strip():
        raise ValueError("The document appears to be empty or could not be read.")

    # Create LangChain Document objects with metadata
    chunks: List[Document] = text_splitter.create_documents(
        texts=[raw_text],
        metadatas=[{"source": filename}],
    )

    total_vectors = vector_manager.add_documents(chunks)

    return {
        "filename": filename,
        "characters": len(raw_text),
        "chunks": len(chunks),
        "total_vectors": total_vectors,
    }


# ── Question-answering ───────────────────────────────────────────────
RAG_PROMPT_TEMPLATE = """You are a helpful assistant. Answer the user's question accurately using ONLY the context provided below. If the context does not contain enough information to answer, say so honestly.

Context:
{context}

Question: {question}

Answer:"""


def ask_question(question: str, k: int = 4) -> Dict[str, Any]:
    """Retrieve relevant chunks and generate an answer via the LLM."""
    if vector_manager.is_empty:
        return {
            "answer": "Please upload a document first before asking questions.",
            "sources": [],
        }

    # Retrieve
    relevant_docs = vector_manager.similarity_search(question, k=k)

    # Build context string
    context_parts = []
    sources = []
    for i, doc in enumerate(relevant_docs, 1):
        context_parts.append(f"[Chunk {i}] {doc.page_content}")
        source_info = {
            "chunk_number": i,
            "source": doc.metadata.get("source", "unknown"),
            "content_preview": doc.page_content[:200] + ("..." if len(doc.page_content) > 200 else ""),
        }
        sources.append(source_info)

    context = "\n\n".join(context_parts)

    # Generate
    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
    answer = llm.invoke(prompt)

    return {
        "answer": answer.strip(),
        "sources": sources,
    }


def clear_store() -> None:
    """Reset the vector store (useful for testing / UI reset)."""
    vector_manager.clear()
