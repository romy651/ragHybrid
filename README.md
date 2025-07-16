# Hybrid RAG & Analytics Service

## Overview

This project is a fullstack data integration project that stores data locally. It performs a “Text-to-Query” service over a small dataset.

<img src="./app.png" width="90%">

The data files are located in the `backend/data` folder (including `products.csv` and `rules.md`), from which the store folder is created containing SQLite databases for both files and embeddings.

Here's what the program does:

1. **Data Ingestion & Indexing**: Raw data is ingested and indexed into a vector store.
2. **Context Retrieval**: Retrieves relevant context for free-text questions.
3. **Ad-hoc Analytics**: Performs SQL-style queries for analytics.
4. **Natural Language Generation**: Generates natural-language answers via OpenAI, with a persona flag to adjust tone.
5. **HTTP API Exposure**: Exposes a simple HTTP API.
6. **Docker Containerization**: Containerizes the application for deployment.

## Key Highlights

### Features

- 💬 **Fullstack Application**: Combines a React frontend with a LangGraph backend, representing each state of execution as a node.
- 🤔 **Automatic Routing**: Identifies which action to perform (RAG-based or analytics), addresses knowledge gaps, and refines searches.

### Project Structure

The project is organized into two main directories:

- `frontend/`: Contains the React application built with Vite.
- `backend/`: Contains the LangGraph/FastAPI application, including the agent logic.

The core of the backend is a LangGraph agent defined in backend/src/agent/graph.py. It follows these steps:

<img src="./agent.png" title="Agent Flow" alt="Agent Flow" width="50%">

## Getting Started: Development and Local Testing

Follow these steps to set up the application for local development and testing.

### Prerequisites

- **Node.js and npm** (or yarn/pnpm)
- **Python 3.11+**
- **API Keys**: The backend agent requires an OpenAI API key.
  1. Navigate to the main directory.
  3. Open the `.env` file and add your OpenAI API key: `OPENAI_API_KEY="YOUR_ACTUAL_API_KEY"` and your LangSmith API Key: `LANGSMITH_API_KEY=YOUR_API_KEY`

### Install Dependencies

Use `uv` as the package manager.

**Backend:**

```bash
cd backend
uv sync
```

**Frontend:**

```bash
cd frontend
npm install
```

### Run Development Servers:

**Backend:**

```bash
cd backend
uv langgraph dev --allow-blocking
```

**Frontend:**

```bash
cd backend
npm run dev
```

_The backend API will be available at `http://127.0.0.1:2024\docs`. It will also open a browser window to the FastAPI docs where request can be accessed. For the frontend, open a terminal in the `frontend/` directory and run `npm run dev`. The frontend will be available at `http://localhost:5173/app`_

The core of the backend is a LangGraph agent defined in `backend/src/agent/graph.py`. It follows these steps:

## Deployment

**1. Build the Docker Image:**

Notice!: You might encounter some issue when building the image, I am currently fixing the error

Run the following command from the **project root directory**:

```bash
docker build -t hybrid-rag-service -f Dockerfile .
```

**2. Run the Production Server:**

```bash
docker-compose up
```

Open your browser and navigate to `http://localhost:8123/app/` to see the application. The API will be available at `http://localhost:8123`.

## Technologies Used

- [React](https://reactjs.org/) (with [Vite](https://vitejs.dev/)) - For the frontend user interface.
- [Tailwind CSS](https://tailwindcss.com/) - For styling.
- [Shadcn UI](https://ui.shadcn.com/) - For components.
- [LangGraph](https://github.com/langchain-ai/langgraph) - For building the backend research agent.
- [Open AI](https://platform.openai.com/docs/models) - LLM for query generation and answer synthesis.
