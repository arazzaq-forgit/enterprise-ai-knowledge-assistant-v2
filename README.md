# 🧠 Enterprise AI Knowledge Assistant

> A production-ready RAG (Retrieval Augmented Generation) 
> system built with Ollama, ChromaDB, and Streamlit.
> 100% local — no API keys, no cost, no data privacy issues!

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorDB-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 What is this?

An **Enterprise-grade AI assistant** that lets you:
- 📄 Upload **PDF, Word, TXT, CSV, MD** documents
- 🌐 Add **website URLs** as knowledge sources  
- 💬 Ask **natural language questions** about your docs
- 🤖 Get **AI-powered answers** with source citations
- 📋 Generate **instant summaries** of any document
- 📊 Track **response quality** with evaluation metrics

All running **100% locally** on your machine!

---

## 🏗️ Architecture

Documents/URLs

│

▼

┌─────────────────┐

│  Document       │  PDF, DOCX, TXT, CSV, URL

│  Manager        │  Loads all file types

└────────┬────────┘

│

▼

┌─────────────────┐

│  Text           │  Splits into 1000 char chunks

│  Chunker        │  with 200 char overlap

└────────┬────────┘

│

▼

┌─────────────────┐

│  Embedding      │  nomic-embed-text via Ollama

│  Model          │  Converts text → vectors

└────────┬────────┘

│

▼

┌─────────────────┐

│  ChromaDB       │  Stores vectors locally

│  VectorStore    │  Persists between sessions

└────────┬────────┘

│

User Question

│

▼

┌─────────────────┐

│  Retriever      │  Finds top-5 relevant chunks

│                 │  using cosine similarity

└────────┬────────┘

│

▼

┌─────────────────┐

│  Prompt         │  Crafts smart prompts

│  Templates      │  for different scenarios

└────────┬────────┘

│

▼

┌─────────────────┐

│  Ollama LLM     │  llama3.2:3b generates

│  Client         │  streaming answers

└────────┬────────┘

│

▼

┌─────────────────┐

│  Streamlit UI   │  Beautiful dark themed

│  + Evaluator    │  web interface

└─────────────────┘

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/enterprise-ai-knowledge-assistant.git
cd enterprise-ai-knowledge-assistant
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Ollama
Download from: https://ollama.com/download

### 5. Download AI Models
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 6. Run the App
```bash
streamlit run app.py
```

Open browser at: **http://localhost:8501** 🎉

---

## 📁 Project Structure

enterprise-ai-knowledge-assistant/

│

├── app.py                    # Main Streamlit application

├── configs.yaml              # All project settings

├── requirements.txt          # Python dependencies

├── README.md                 # You are here!

│

├── src/

│   ├── config/

│   │   └── settings.py       # Config loader

│   │

│   ├── loaders/

│   │   ├── pdf_loader.py     # PDF extraction

│   │   ├── docx_loader.py    # Word doc extraction

│   │   ├── txt_loader.py     # Text/CSV extraction

│   │   └── document_manager.py # Master loader + URLs

│   │

│   ├── chunking/

│   │   └── chunker.py        # Smart text splitter

│   │

│   ├── embeddings/

│   │   └── embedding_model.py # Ollama embeddings

│   │

│   ├── vectorstore/

│   │   └── vector_store.py   # ChromaDB manager

│   │

│   ├── llm/

│   │   └── llm_client.py     # Ollama LLM client

│   │

│   ├── retrieval/

│   │   └── retriever.py      # Semantic search

│   │

│   ├── prompts/

│   │   └── prompt_template.py # Prompt engineering

│   │

│   ├── pipeline/

│   │   └── rag_pipeline.py   # Master orchestrator

│   │

│   ├── evaluation/

│   │   └── evaluator.py      # Quality metrics

│   │

│   └── utils/

│       ├── logger.py         # Professional logging

│       ├── helpers.py        # Utility functions

│       └── session_manager.py # Session state

│

├── data/

│   ├── raw/                  # Original documents

│   ├── processed/            # Processed files

│   └── vectorstore/          # ChromaDB storage

│

├── logs/                     # Application logs

└── tests/                    # Unit tests

---

## ✨ Features

### 📄 Multi-Format Document Support
| Format | Support |
|--------|---------|
| PDF    | ✅ Full text + metadata extraction |
| DOCX   | ✅ Paragraphs + tables |
| TXT    | ✅ Smart encoding detection |
| MD     | ✅ Markdown documents |
| CSV    | ✅ Tabular data as text |
| URLs   | ✅ Web scraping |

### 🤖 AI Capabilities
- **Streaming Answers** — ChatGPT-like typing effect
- **Source Citations** — Know exactly which document answered
- **Multi-doc Search** — Search across all documents at once
- **Chat History** — Follow-up questions with context
- **Summarization** — One-click document summaries

### 📊 Quality Evaluation
Every response is automatically graded on:
| Metric | Weight | Description |
|--------|--------|-------------|
| Relevance | 30% | Answer matches question |
| Coverage | 20% | Uses available context |
| Sources | 20% | Cites documents properly |
| Faithfulness | 20% | No hallucinations |
| Speed | 10% | Response time |

### 🎨 Beautiful UI
- Dark themed professional interface
- Real-time system status monitoring
- Interactive analytics dashboard
- Export chat history as text file

---

## 🔧 Configuration

All settings in `configs.yaml`:

```yaml
ollama:
  llm_model: "llama3.2:3b"      # Change AI model
  embedding_model: "nomic-embed-text"
  temperature: 0.1               # 0=focused, 1=creative

vectorstore:
  chunk_size: 1000               # Characters per chunk
  chunk_overlap: 200             # Overlap between chunks
  top_k_results: 5               # Results to retrieve
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.12 | Core language |
| Streamlit | Web UI framework |
| LangChain | LLM orchestration |
| Ollama | Local LLM runtime |
| ChromaDB | Vector database |
| PyMuPDF | PDF processing |
| python-docx | Word processing |
| Plotly | Analytics charts |
| BeautifulSoup4 | Web scraping |

---

## 👨‍💻 Author

**Mohd Abdul Razzaq**
- 🎓 Data Science & AI-ML
- 💼 Building production-ready AI systems
- 🌟 Passionate about making AI accessible

---

## 📜 License

MIT License — feel free to use for learning!