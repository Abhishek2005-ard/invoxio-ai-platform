# Invoxio — AI-Powered SaaS Invoice & Business Intelligence Platform

## 📁 Project Structure

```
Invoxio/
│
├── frontend/          # React + Vite (JavaScript/TypeScript)
├── backend/           # Node.js + Express (REST API + MongoDB)
├── agents/            # Python AI Agents (LangChain + LangGraph + Google GenAI)
│
├── .gitignore
└── README.md
```

## 🚀 Tech Stack

| Layer    | Technology                                      |
|----------|-------------------------------------------------|
| Frontend | React 18, Vite, Zustand, TanStack Query, Recharts |
| Backend  | Node.js, Express, MongoDB, Mongoose, Redis       |
| Agents   | Python, LangChain, LangGraph, Google GenAI       |

## ⚙️ Getting Started

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
