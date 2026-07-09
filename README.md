# Invoxio - AI-Powered SaaS Invoice & Business Intelligence Platform

## 📁 Project Structure

```
Invoxio/
│
├── frontend/          # React + Vite (TypeScript)
├── backend/           # Node.js + Express (REST API + MongoDB)
├── agents/            # Python AI Agents (LangChain + LangGraph + Google GenAI)
├── deploy/            # Nginx & Supervisor configs for Docker
│
├── Dockerfile         # Multi-stage build (all 3 services in one image)
├── .dockerignore      # Files excluded from Docker build
├── .env.example       # Template for environment variables
├── .gitignore
└── README.md
```

## 🚀 Tech Stack

| Layer    | Technology                                       |
|----------|--------------------------------------------------|
| Frontend | React 18, Vite, Zustand, TanStack Query, Recharts |
| Backend  | Node.js, Express, MongoDB, Mongoose              |
| Agents   | Python, LangChain, LangGraph, Google GenAI        |
| DevOps   | Docker, Nginx, Supervisor                         |

---

## 🐳 Quick Start with Docker (Recommended)

> **Prerequisites:** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) on your machine. That's it — you don't need Node.js, Python, or anything else.

### Step 1: Clone the repository

```bash
git clone https://github.com/your-username/invoxio.git
cd invoxio
```

### Step 2: Create your environment file

Copy the example and fill in your actual values:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholders:

```env
# ─── Backend ──────────────────────────────────────────
PORT=5000
NODE_ENV=production
MONGODB_URI=mongodb+srv://<your-user>:<your-password>@cluster0.xxxxx.mongodb.net/invoxio
JWT_SECRET=pick_a_strong_random_secret_here
JWT_EXPIRE=7d

# ─── Agents ──────────────────────────────────────────
APP_PORT=8000
GOOGLE_GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=gemini-flash-latest
LANGCHAIN_TRACING_V2=false
```

### Step 3: Build the Docker image

```bash
docker build -t invoxio .
```

### Step 4: Run the container

```bash
docker run -d -p 3000:3000 --name invoxio --env-file .env invoxio
```

### Step 5: Open in browser

```
http://localhost:3000
```

That's it! All 3 services (frontend, backend, AI agents) are running inside one container.

### Useful commands

```bash
docker logs invoxio          # View logs for all services
docker stop invoxio          # Stop the container
docker rm invoxio            # Remove the container
docker start invoxio         # Restart a stopped container
```

### Rebuild after code changes

```bash
docker stop invoxio && docker rm invoxio
docker build -t invoxio .
docker run -d -p 3000:3000 --name invoxio --env-file .env invoxio
```

---

## ⚙️ Local Development (Without Docker)

If you prefer running each service directly on your machine:

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
npm install
npm run dev
```

### Agents (Python)
```bash
cd agents
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py
```
