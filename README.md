# 🤖 AI DevOps Copilot

> AI-powered DevOps incident analysis using a local LLM (Ollama +
> Qwen2.5) and FastAPI.

## 🚀 Overview

AI DevOps Copilot helps DevOps and SRE engineers quickly analyze
incidents from logs and infrastructure metrics. It uses a locally hosted
Large Language Model (LLM) through Ollama to generate structured
incident reports.

## ✨ Features

-   AI-powered incident analysis
-   Local inference using Ollama
-   FastAPI REST API
-   Swagger UI
-   Structured JSON responses
-   Pydantic validation
-   Foundation for log file analysis

## 🛠 Tech Stack

  Category          Technology
  ----------------- ---------------------
  Language          Python 3.13
  API               FastAPI
  AI                Ollama + Qwen2.5:3B
  Validation        Pydantic
  Server            Uvicorn
  Package Manager   uv

## 📁 Project Structure

``` text
backend/
├── app/
│   ├── ai/
│   ├── api/routes/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── sample-logs/
├── pyproject.toml
└── uv.lock
```

## 🔄 Architecture

``` text
                User
                  │
                  ▼
          FastAPI REST API
                  │
                  ▼
         Incident Analyzer
                  │
                  ▼
           AI Provider Layer
                  │
                  ▼
        Ollama (Qwen2.5:3B)
                  │
                  ▼
      Structured JSON Response
```

## 📡 API

### POST `/analyze`

Request

``` json
{
  "service": "payment-service",
  "logs": "Redis connection refused",
  "cpu": 95,
  "memory": 87
}
```

Response

``` json
{
  "severity": "high",
  "summary": "Payment Service Performance and Connectivity Issues Detected",
  "root_cause": "Redis connectivity failure causing service degradation.",
  "recommendations": [
    "Investigate Redis connectivity",
    "Monitor CPU and Memory",
    "Scale the payment service if required"
  ]
}
```

## ⚙️ Run Locally

``` bash
git clone https://github.com/rahman5828/ai-devops-copilot.git
cd ai-devops-copilot

uv sync

ollama serve
```

In another terminal:

``` bash
ollama pull qwen2.5:3b
```

Run the backend:

``` bash
cd backend
uv run --active uvicorn app.main:app --reload
```

Open Swagger:

``` text
http://127.0.0.1:8000/docs
```

## 🗺 Roadmap

### ✅ Version 0.1.0 (Current)

-   FastAPI backend
-   Ollama integration
-   AI incident analysis
-   Structured JSON output
-   Swagger documentation

### 🔜 Next

-   Smart log parser
-   File upload analysis
-   Docker log analysis
-   Kubernetes incident analysis
-   Prometheus metrics integration
-   Incident history
-   React dashboard

## 👨‍💻 Author

**Abdul Rahman V A**

-   GitHub: https://github.com/rahman5828
