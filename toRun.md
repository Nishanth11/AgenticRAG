# How to Run — Agentic RAG (Maintenance-Aware Production Assistant)

## Prerequisites

- Python 3.13+
- [Ollama](https://ollama.com) running locally with two models:
  - `mistral` — LLM for reasoning
  - `mxbai-embed-large` — embeddings for RAG

### Install and start Ollama

```bash
# Install Ollama (macOS)
brew install ollama

# Pull required models
ollama pull mistral
ollama pull mxbai-embed-large

# Start Ollama (runs on http://localhost:11434)
ollama serve
```

---

## Step 1 — Create a Virtual Environment

```bash
cd "Agentic RAG"
python -m venv venv
```

Activate it:

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

---

## Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 3 — Set Up the .env File

Create a `.env` file in the `Agentic RAG` directory:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=mistral
OLLAMA_EMBED_MODEL=mxbai-embed-large

# RAG paths (defaults match code — override if needed)
MAINTENANCE_DOCS_PATH=./maintenance_docs
CHROMA_PERSIST_DIR=./chroma_db
```

---

## Step 4 — Run the Agent

```bash
python main.py
```

You will be prompted to enter a query. Example queries:

```
Can we produce 50 batches of Product A starting August 20, 2026?
Is it safe to start Product A production on August 16?
Check if we can run 30 batches of Product B today
Any maintenance planned for next week?
```

---

## How RAG Works in This Project

On first run, the agent:
1. Loads maintenance documents from `maintenance_docs/`
2. Embeds them using `mxbai-embed-large` via Ollama
3. Stores vectors in `chroma_db/` (persisted for future runs)

Subsequent runs reuse the existing ChromaDB — no re-embedding needed.

---

## Dummy Files (no real hardware needed)

| File | Replaces |
|------|----------|
| `dummy_opc_ua.py` | Real OPC UA server (tank levels + machine states) |
| `dummy_storage.py` | TimescaleDB/PostgreSQL (product recipes) |

These are imported automatically by `main.py` — no changes needed.
