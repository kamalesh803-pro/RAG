# 🧠 RAG Web Application

A **Retrieval Augmented Generation** web app that lets you upload documents and ask questions about them, powered entirely by free & open-source tools.

| Component | Technology |
|-----------|-----------|
| Backend | Python · FastAPI |
| RAG pipeline | LangChain |
| Vector DB | FAISS |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| LLM | Llama 3.2 (3B) via Ollama (runs locally) |
| Frontend | HTML · CSS · JavaScript |

---

## 📁 Project Structure

```
RAG/
├── backend/
│   ├── main.py              # FastAPI server & routes
│   ├── rag_pipeline.py      # Document ingestion & Q/A chain
│   ├── vector_store.py      # FAISS index + embedding wrapper
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── index.html            # Main page
│   ├── style.css             # Dark glassmorphism UI
│   └── script.js             # Client-side logic
│
└── README.md
```

---

## 🚀 Setup Instructions

### 1 · Install Python Dependencies

```bash
cd RAG/backend
pip install -r requirements.txt
```

> **Tip:** Use a virtual environment (`python -m venv venv` → activate it → then pip install).

### 2 · Install & Start Ollama

1. Download Ollama from [https://ollama.com](https://ollama.com) and install it.
2. Pull the **Llama 3.2** model:

   ```bash
   ollama pull llama3.2:3b
   ```

3. Make sure Ollama is running (it starts automatically after install on most systems). You can verify with:

   ```bash
   ollama list
   ```

### 3 · Start the FastAPI Server

```bash
cd RAG/backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4 · Open the Web Interface

Open your browser and go to:

```
http://localhost:8000
```

---

## 🎯 How to Use

1. **Upload** a PDF or TXT file using the sidebar.
2. Wait for the "indexed successfully" message.
3. **Type a question** in the chat input and press Enter.
4. The AI will answer based only on the uploaded document(s) and show the **source chunks** it used.
5. You can upload more documents and keep asking questions.

---

## 🛠 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection error` in the UI | Make sure `uvicorn` is running on port 8000 |
| `Ollama connection refused` | Run `ollama serve` or restart the Ollama app |
| Slow first query | The SentenceTransformer model downloads on first run (~80 MB) |
| Out of memory | Use a smaller Ollama model: `ollama pull llama3.2:1b` and change `model="llama3.2:1b"` in `rag_pipeline.py` |

---

## 📝 License

This project is free and open-source. All third-party libraries are under permissive open-source licenses.
