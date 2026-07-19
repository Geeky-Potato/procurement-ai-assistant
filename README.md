# Procurement AI Assistant

A conversational assistant over the **State of California large-purchases** procurement
dataset. Ask questions in natural language; an LLM agent translates them into MongoDB
queries / aggregation pipelines, runs them, and answers.

**Stack**
- **Backend:** FastAPI (Python 3.12)
- **Agent:** LangGraph + Anthropic Claude (`claude-opus-4-8`)
- **Database:** MongoDB (via Docker)
- **Frontend:** Angular 19

## Prerequisites
- Docker (running) — for MongoDB
- Python 3.12 (`brew install python@3.12`)
- Node 22 + Angular CLI 19

## 1. Database
```bash
docker compose up -d          # starts MongoDB on :27017 (+ mongo-express UI on :8081)
```

## 2. Dataset
The CSV is not committed (it is large). Download the **State of California — Large
Purchases** dataset from Kaggle and drop the CSV into `backend/data/`:

- https://www.kaggle.com/datasets/sohier/large-purchases-by-the-state-of-ca

Then load it into MongoDB (loader added in the next step):
```bash
cd backend
source .venv/bin/activate
python -m app.db.load_csv data/PURCHASE_ORDER_DATA.csv
```

## 3. Backend
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

## 4. Frontend
```bash
cd frontend
npm install
ng serve                      # http://localhost:4200
```

## Environment variables
See `backend/.env.example`. You need an Anthropic API key from
https://console.anthropic.com/settings/keys.

## Project layout
```
procurement-assistant/
├── docker-compose.yml        # MongoDB + mongo-express
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/                 # CSV dataset (gitignored)
│   └── app/
│       ├── main.py           # FastAPI entrypoint
│       ├── core/             # config, settings
│       ├── db/               # Mongo client + CSV loader
│       ├── agent/            # LangGraph agent (NL -> Mongo query)
│       └── api/              # chat routes
└── frontend/                 # Angular chat UI
```
