# IntelliPlant — AI for Industrial Knowledge Intelligence

An AI-powered Industrial Knowledge Intelligence platform that ingests heterogeneous industrial documents and makes their collective intelligence queryable, actionable, and continuously updated.

## Architecture

```
intelliplant/
├── backend/          # FastAPI + RAG + Knowledge Graph + Agents
├── frontend/         # React + Tailwind (web + mobile-responsive)
├── data/             # Sample industrial documents for demo
└── docker-compose.yml
```

## Modules

1. **Document Ingestion Pipeline** — PDF, P&ID, scanned forms, spreadsheets, email archives
2. **Expert Knowledge Copilot** — RAG-powered conversational AI with citations
3. **Maintenance Intelligence & RCA Agent** — Predictive maintenance + root cause analysis
4. **Compliance Intelligence** — Regulatory gap detection + audit evidence generation
5. **Lessons Learned Engine** — Pattern detection + proactive warnings

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Tech Stack

- **Backend**: FastAPI, LangChain, ChromaDB (vector store), NetworkX (knowledge graph), PyMuPDF, Tesseract OCR
- **LLM**: OpenAI GPT-4o (configurable) / local Ollama
- **Frontend**: React 18, Tailwind CSS, shadcn/ui, React Query
- **Storage**: SQLite (metadata), ChromaDB (embeddings), JSON (knowledge graph)
