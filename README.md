# Procurement AI Assistant

A conversational assistant over the **State of California large-purchases**
procurement dataset (~346K purchase-order line items, 2012–2015). Ask questions
in natural language; an LLM agent translates them into MongoDB queries /
aggregation pipelines, runs them, and answers.

**Stack**

- **Backend:** FastAPI (Python 3.12)
- **Agent:** LangGraph ReAct agent with read-only MongoDB tools
- **LLM:** **Groq** (free tier) via `langchain-groq`
- **Database:** MongoDB (via Docker)
- **Frontend:** Angular 19

## How it works

```
Angular chat UI  ──POST /api/chat──▶  FastAPI
                                        │
                                        ▼
                              LangGraph ReAct agent (LLM)
                                        │  aggregate / find / count / distinct
                                        ▼
                                     MongoDB  ◀── purchase_orders
```

The agent is given the collection schema and read-only query tools. It decides
which MongoDB queries to run, executes them, and writes a grounded answer.

## Prerequisites

- Docker (running) — for MongoDB
- Python 3.12 (`brew install python@3.12`)
- Node 22 + Angular CLI 19
- A free Groq API key (see [LLM provider](#llm-provider) below)

## 1. Database

```bash
docker compose up -d
# Starts MongoDB on :27017 (+ mongo-express UI on :8081)
```

## 2. Dataset

The CSV is not committed (it is large). Download the **State of California —
Large Purchases** dataset from Kaggle and drop the CSV into `backend/data/`:

- https://www.kaggle.com/datasets/sohier/large-purchases-by-the-state-of-ca

The loader expects `backend/data/PURCHASE_ORDER_DATA.csv` (rename the download
if needed). Then load it into MongoDB:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db.load_csv data/PURCHASE_ORDER_DATA.csv --drop
```

The loader cleans types (currency `$` strings → float, `MM/DD/YYYY` → dates,
`YES/NO` → bool), bulk-inserts, and builds indexes. Expect ~346,018 documents.

## 3. Backend

```bash
cd backend
source .venv/bin/activate
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API serves `POST /api/chat` (see the interactive docs at
`http://localhost:8000/docs`).

## 4. Frontend

```bash
cd frontend
npm install
ng serve
```

## LLM provider

The agent runs on **Groq**, whose free tier needs no billing. Grab a key at
https://console.groq.com/keys and set it in `backend/.env`:

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
```

See `backend/.env.example` for all variables.

## Example questions

- "What was the total spend per fiscal year?"
- "Top 10 suppliers by total spend."
- "How much did the state spend on IT Goods?"
- "Which departments made the most purchases?"

## Project layout

```
procurement-ai-assistant/
├── docker-compose.yml        # MongoDB + mongo-express
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/                 # CSV dataset (gitignored)
│   └── app/
│       ├── main.py           # FastAPI entrypoint + /health
│       ├── core/config.py    # settings from .env
│       ├── db/               # Mongo client + CSV loader
│       ├── agent/            # LangGraph agent (schema, tools, graph)
│       └── api/chat.py       # POST /api/chat
└── frontend/                 # Angular 19 chat UI
```
