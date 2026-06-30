# 🧠 DocMind AI — Enterprise RAG Knowledge Assistant

> Chat with your documents using AI. Upload PDFs, ask questions in plain English, get instant answers with source citations.

[![Live Demo](https://img.shields.io/badge/demo-live-success?style=for-the-badge)](https://enterprise-ai-knowledge-assistant-v.vercel.app)
[![API Docs](https://img.shields.io/badge/API-docs-blue?style=for-the-badge)](https://enterprise-ai-knowledge-assistant-v2.onrender.com/docs)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

🔗 **Live App:** [enterprise-ai-knowledge-assistant-v.vercel.app](https://enterprise-ai-knowledge-assistant-v.vercel.app)
🔗 **API Docs:** [enterprise-ai-knowledge-assistant-v2.onrender.com/docs](https://enterprise-ai-knowledge-assistant-v2.onrender.com/docs)

---

## 📸 Screenshots

### Landing Page
![Landing Page](docs/images/hero.png)

### Features
![Features](docs/images/features.png)

### AI Workspace — Real-time Q&A with Citations
![Workspace](docs/images/workspace.png)

---

## 🎯 Overview

DocMind AI is a full-stack **Retrieval-Augmented Generation (RAG)** application built to demonstrate production-grade AI engineering — not a notebook demo, but a deployed product with a real frontend, real backend, and real users in mind.

Upload a document, ask a question, and get an answer grounded in your content — with the exact source and page number cited, streamed back token-by-token like ChatGPT.

┌──────────────────┐      ┌───────────────────┐      ┌──────────────────┐
│   React Frontend  │ ───▶ │   FastAPI Backend  │ ───▶ │     ChromaDB      │
│  (TypeScript/Vite) │◀─── │   REST API + SSE   │◀──── │   Vector Store    │
└──────────────────┘      └───────────────────┘      └──────────────────┘
Vercel                     Render                    Persistent
│                          ▲
▼                          │
┌───────────────────┐      ┌──────────────────┐
│    Groq LLM API    │      │ HuggingFace API   │
│  (Llama 3.1 8B)    │      │   (Embeddings)    │
└───────────────────┘      └──────────────────┘---

## 🏗️ Architecture

### RAG Pipeline Flow
User uploads document
│
▼
Document Loader (PDF/DOCX/TXT/MD/CSV)
│
▼
Text Chunker (1000 chars, 200 overlap)
│
▼
Embedding Model (HuggingFace API)
│
▼
ChromaDB Vector Store
│
═══════════════════════════════════
│
User asks a question
│
▼
Embed question → Semantic search ChromaDB
│
▼
Retrieve top-5 relevant chunks
│
▼
Build prompt with context + citation instructions
│
▼
Groq LLM generates answer (streamed)
│
▼
Response + source citations → User

---

## 🛠️ Tech Stack

<table>
<tr>
<td valign="top" width="50%">

**Frontend**
- React 18 + TypeScript
- Vite 8
- Tailwind CSS v4
- React Router
- Axios
- Lucide Icons

</td>
<td valign="top" width="50%">

**Backend**
- FastAPI
- ChromaDB (vector store)
- Groq API (Llama 3.1 8B)
- HuggingFace Inference API (embeddings)
- PyPDF / python-docx
- Server-Sent Events (streaming)

</td>
</tr>
</table>

**Deployment:** Vercel (frontend) · Render (backend)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Semantic Search** | Meaning-based retrieval using vector embeddings, not keyword matching |
| ⚡ **Streaming Responses** | Real-time word-by-word answers via Server-Sent Events |
| 📎 **Source Citations** | Every answer references the exact document and page number |
| 📁 **Multi-format Support** | PDF, DOCX, TXT, Markdown, CSV, and web URLs |
| 🗂️ **Multi-document Q&A** | Query across multiple uploaded documents simultaneously |
| 📝 **Auto-summarize** | One-click structured summaries of any document |
| 🎨 **Premium UI** | Aurora gradient background, glassmorphism, smooth animations |
| 🔒 **Stateless & Secure** | No user data persisted beyond session; documents processed on demand |

---

## 🚀 Getting Started Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free [Groq API key](https://console.groq.com)
- A free [HuggingFace token](https://huggingface.co/settings/tokens)

### 1. Clone the repository
```bash
git clone https://github.com/arazzaq-forgit/enterprise-ai-knowledge-assistant-v2.git
cd enterprise-ai-knowledge-assistant-v2/enterprise-ai-knowledge-assistant
```

### 2. Backend setup
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
```

Set environment variables:
```bash
# .env or export directly
GROQ_API_KEY=gsk_your_key_here
HF_TOKEN=hf_your_token_here
LLM_MODEL=llama-3.1-8b-instant
```

Run the backend:
```bash
uvicorn backend.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`

### 3. Frontend setup
```bash
cd frontend
npm install
npm run dev
```
App available at `http://localhost:5173`

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload and index a document |
| `POST` | `/api/upload/url` | Scrape and index content from a URL |
| `POST` | `/api/chat` | Ask a question (streaming SSE response) |
| `POST` | `/api/chat/sources` | Retrieve source chunks for a question |
| `POST` | `/api/summarize` | Generate a structured summary of a document |
| `GET` | `/api/documents` | List all indexed documents |
| `DELETE` | `/api/documents` | Clear the knowledge base |
| `GET` | `/api/health` | Health check + pipeline stats |

Full interactive documentation: [`/docs`](https://enterprise-ai-knowledge-assistant-v2.onrender.com/docs)

---

## 📁 Project Structure
enterprise-ai-knowledge-assistant/
├── backend/                   # FastAPI application layer
│   ├── main.py                 # App entry point, CORS, lifespan
│   ├── schemas.py               # Pydantic request/response models
│   └── routers/
│       ├── chat.py               # Chat + streaming endpoints
│       ├── upload.py             # File/URL upload endpoints
│       └── documents.py          # Document management endpoints
│
├── src/                        # Core RAG engine (framework-agnostic)
│   ├── pipeline/
│   │   └── rag_pipeline.py        # Orchestrates the full RAG flow
│   ├── llm/
│   │   └── llm_client.py           # Groq LLM client (streaming + sync)
│   ├── embeddings/
│   │   └── embedding_model.py      # HuggingFace embedding client
│   ├── chunking/
│   │   └── chunker.py              # Overlapping text chunker
│   ├── vectorstore/
│   │   └── vector_store.py         # ChromaDB interface
│   ├── retrieval/
│   │   └── retriever.py            # Semantic retrieval logic
│   ├── loaders/                   # PDF / DOCX / TXT / URL loaders
│   ├── prompts/
│   │   └── prompt_template.py      # Citation-aware prompt templates
│   └── utils/                     # Logging, helpers
│
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── landing/             # Hero, Features, Stats
│   │   │   ├── layout/              # Navbar, Footer
│   │   │   ├── chat/                # ChatWindow, Sidebar, Message
│   │   │   ├── upload/              # UploadZone
│   │   │   └── ui/                  # GradientBackground
│   │   ├── pages/                  # Home, Workspace, NotFound
│   │   ├── services/
│   │   │   └── api.ts                # Backend API client
│   │   └── styles/
│   │       └── globals.css           # Tailwind + design tokens
│   ├── vercel.json                # SPA routing config
│   └── package.json
│
├── requirements.txt             # Python dependencies
├── Procfile                     # Render process definition
└── README.md
---

## 🧠 Design Decisions

**Why Groq instead of OpenAI?**
Groq offers free, extremely fast inference (LPU-based) with no credit card required — ideal for a portfolio project that needs to stay live and free indefinitely.

**Why HuggingFace Inference API for embeddings instead of local models?**
Running `sentence-transformers` locally on Render's free tier exceeds the 512MB RAM limit. Offloading embedding computation to HuggingFace's free API keeps the backend lightweight and deployable on free infrastructure.

**Why ChromaDB?**
Zero-config, file-based persistence — no external database service required, which keeps the deployment footprint minimal while still supporting proper cosine-similarity vector search.

**Why Server-Sent Events over WebSockets?**
SSE is simpler to implement and sufficient for one-directional streaming (server → client), avoiding the complexity of full-duplex WebSocket connections for a use case that doesn't need them.

---

## 🔮 Future Improvements

- [ ] Hybrid search (BM25 + semantic) for improved retrieval precision
- [ ] Cross-encoder re-ranking of retrieved chunks
- [ ] Persistent chat history per session
- [ ] Dark/light theme toggle
- [ ] Docker Compose setup for one-command local deployment
- [ ] Automated retrieval evaluation suite (precision@k, recall@k)

---

## 👤 Author

**Mohd Abdul Razzaq**

[![GitHub](https://img.shields.io/badge/GitHub-arazzaq--forgit-181717?style=flat&logo=github)](https://github.com/arazzaq-forgit)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <i>If you found this project useful or interesting, consider giving it a ⭐</i>
</p>
