## Manuscript Writer (Clinical/HEOR)

Full-stack web app for clinical/HEOR researchers to generate publication-ready manuscripts from study reports and curated literature.

### Tech stack

- **Frontend**: React + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (async) + Motor (MongoDB)
- **DB**: MongoDB
- **AI**: Claude Sonnet 4.5 via LiteLLM

---

## Local development

### 1) Start MongoDB

```bash
docker compose up -d
```

### 2) Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000` and Swagger docs at `http://localhost:8000/docs`.

### 3) Frontend (React)

This repo includes a complete frontend scaffold, but **Node.js is required**.

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## Environment variables

- **Backend** (`backend/.env`)
  - `MONGO_URL`
  - `MONGO_DB_NAME`
  - `JWT_SECRET`
  - `JWT_EXPIRE_MINUTES`
  - `LITELLM_MODEL` (default: `claude-sonnet-4-5`)
  - `LITELLM_API_KEY`
  - `CORS_ORIGINS` (comma-separated)

- **Frontend** (`frontend/.env`)
  - `VITE_API_BASE_URL` (default `http://localhost:8000`)

---

## Deploy to Render

This repo includes a Render blueprint: `render.yaml`.

### Prereqs

- Use **MongoDB Atlas** (Render does not provide a first-party MongoDB database on all plans).
- Create an Atlas cluster and get a connection string like:
  - `mongodb+srv://USER:PASS@cluster.mongodb.net/?retryWrites=true&w=majority`

### Steps

1. In Render, create a **New Blueprint Instance** from your repo (it will pick up `render.yaml`).
2. Set backend env vars for `manuscript-writer-api`:
   - `MONGO_URL`: your Atlas connection string
   - `JWT_SECRET`: a long random string
   - `LITELLM_API_KEY`: your Claude key (through LiteLLM)
   - `CORS_ORIGINS`: your frontend URL (after the static site is created)
3. Set frontend env var for `manuscript-writer-web`:
   - `VITE_API_BASE_URL`: your backend URL


