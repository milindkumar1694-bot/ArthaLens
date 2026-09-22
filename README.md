# ArthaLens — Quantitative Options Terminal

ArthaLens is an Indian-market derivatives intelligence terminal engineered for institutional derivatives operators navigating NSE/BSE capital markets.

> [!NOTE]
> **Decision Support Terminal** — Provides real-time options analytics, dealer gamma profiles (GEX), Max Pain pinning, and risk alerts. Not investment advice.

---

## 1. Production Architecture (Render)

```text
               INTERNET
                  │
                  ▼
             RENDER PAAS
                  │
     ┌────────────┴────────────┐
     │                         │
  Frontend                  Backend
(Static Site)            (Python Web)
     │                         │
     │                ┌────────┼────────┐
     │                │        │        │
     ▼            Angel One   News     LLM
https://...      Market Data  API     (xAI)
                      │
                  PostgreSQL
                      │
                    Redis
```

### Deployed Services
1. **`arthalens-backend`** (Render Web Service):
   - **Runtime**: Python 3.12 / FastAPI
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`
2. **`arthalens-frontend`** (Render Static Site):
   - **Runtime**: Static Site / Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
   - **SPA Routing Rewrite**: `/* -> /index.html`

---

## 2. Environment Variables Reference

Configure the following environment variables in Render Dashboard for your services:

| Variable | Service | Description / Example |
| :--- | :--- | :--- |
| `APP_ENV` | Backend | `production` |
| `DATA_MODE` | Backend | `live` (or `mock` for dev simulation) |
| `BROKER_PROVIDER` | Backend | `angelone` (or `fyers`) |
| `ANGEL_ONE_API_KEY` | Backend | Angel One SmartAPI key |
| `ANGEL_ONE_CLIENT_ID` | Backend | Angel One SmartAPI Client Code |
| `ANGEL_ONE_PASSWORD` | Backend | Angel One Password |
| `ANGEL_ONE_TOTP` | Backend | Angel One TOTP Secret |
| `DATABASE_URL` | Backend | Render PostgreSQL Connection String |
| `REDIS_URL` | Backend | Render Redis Connection String |
| `CORS_ORIGINS` | Backend | `https://arthalens-frontend.onrender.com` |
| `NEWS_API_KEY` | Backend | NewsAPI key |
| `TELEGRAM_BOT_TOKEN` | Backend | Telegram Bot Token for alerts |
| `TELEGRAM_CHAT_ID` | Backend | Telegram Target Chat ID |
| `LLM_PROVIDER` | Backend | `xai` or `openai` |
| `XAI_API_KEY` | Backend | xAI (Grok) API Key |
| `VITE_API_BASE_URL` | Frontend | `https://arthalens-backend.onrender.com/api/v1` |

---

## 3. Local Development Setup

### Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cp .env.example .env
export PYTHONPATH=backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. FastAPI Interactive OpenAPI docs are at `http://localhost:8000/docs`.

---

## 4. Test Suite Execution

### Backend Tests
```bash
python -m pytest backend/tests -q
```

### Frontend Production Build Test
```bash
cd frontend
npm run build
```

---

## 5. API Endpoints

- `GET /api/v1/health` — System status, DB check, Redis status, data mode.
- `GET /api/v1/market/{symbol}` — Normalized quote for `NIFTY`, `BANKNIFTY`, `SENSEX`, `INDIAVIX`.
- `GET /api/v1/options/expiries?symbol=NIFTY` — Discovered option expiry dates.
- `GET /api/v1/options/{symbol}?expiry=YYYY-MM-DD` — Full strike matrix option chain.
- `GET /api/v1/expiry/{symbol}?expiry=YYYY-MM-DD` — Net GEX, Gamma Flip, Pin Target, CAS Monitor.
- `GET /api/v1/analytics/{symbol}` — Technical & options analytics.
- `GET /api/v1/news?symbol=NIFTY` — News feed & AI sentiment fusion.
- `GET /api/v1/watchlist` — Multi-asset ranked scanner table with priority scores.
