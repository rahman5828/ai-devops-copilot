# AI DevOps Copilot — Frontend

A high-signal, evidence-first operations console for the FastAPI AI DevOps Copilot backend.

## Design goals

- Dense but calm enterprise operations UI
- Dark-first visual system with light mode
- Incident severity and impact are always visually distinct
- Deterministic infrastructure evidence is clearly separated from AI inference
- Command palette (`⌘K` / `Ctrl+K`)
- Responsive layouts for desktop and tablet
- Works immediately with demo data if the API is unavailable
- Automatically switches to real incident history when the backend responds

## Run

```bash
npm install
cp .env.example .env
npm run dev
```

Backend default:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Backend contract used

- `GET /incidents`
- `GET /incidents?service=&severity=&impact=`
- `POST /analyze/incident`

If your backend uses a slightly different analysis route, update `src/lib/api.ts` only; the UI is intentionally isolated from transport details.
