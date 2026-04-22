# 🌍 Orbitix: Deep Travel Agent Planner

**A multi-agent AI system that generates deep, personalized travel insights by orchestrating real-time APIs, a Knowledge Graph, and cross-session episodic memory.**

<a href="https://x.com/akhtarrr012/status/1955229103495184846?s=20">
  <img width="1898" height="797" alt="Demo" src="https://github.com/user-attachments/assets/35896c5c-a35c-4ef1-ac95-0f5af19fe45a" />
</a>

---

## 📖 Overview

Orbitix is an autonomous multi-agent travel concierge. Unlike standard travel bots, it combines **Neo4j Knowledge-Graph RAG**, **Hybrid Search (Voyage-3 + BM25)**, and a **3-tier memory system** (working, episodic, semantic) to deliver context-aware itineraries, real-time safety advisories, flight comparisons, hotel/restaurant recommendations, and even cinematic AI-narrated audio tour guides — all streamed token-by-token to the frontend.

- **Coordinator:** Claude Sonnet 4 (with `thinking` enabled) via the Agno `Team` framework in `coordinate` mode.
- **Workers:** GPT-4.1 / GPT-4o / Gemini 2.5 Pro across specialized agents.
- **TTFT target:** < 1.5 s (async memory pre-fetch + streaming SSE).

---

## 🚀 Key Features

- **⚡ High Performance:** Built on **Agno AI** for streaming, async, low-latency responses. Concurrent memory fetch via `asyncio.gather`. Time-to-First-Token under 1.5 s.
- **🧠 3-Tier Memory:** **Working memory** (Postgres `working_memory` table, per-turn), **Episodic memory** (GPT-4o structured summaries of past sessions, semantic cosine search), **Semantic memory** (Neo4j Knowledge Graph).
- **🕸️ Knowledge-Graph RAG:** **Neo4j** + **`neo4j-graphrag`** with a custom `VoyageEmbeddings` adapter over `voyage-3-large` (1024-dim) — models complex relationships between locations, preferences, and constraints.
- **🔍 Hybrid Search:** Voyage-3 dense embeddings + BM25 + custom re-ranking (Naive + Alpha) for high-quality retrieval.
- **🎙️ Audio Tour Generation:** Gemini 2.5 Pro scripts → **ElevenLabs** TTS (`eleven_multilingual_v2`) → direct GCP upload → inline `<audio>` playback in markdown.
- **🔌 6 Specialized Agents** coordinated by a single Claude coordinator.
- **🧪 DI throughout:** `dependency-injector` container with Singletons (agents, LLM clients) and async Resources (asyncpg pool, Supabase).
- **📡 Server-Sent-Event streaming:** granular `reasoning` / `response` / `end` / `error` events with tool-call tracing.

---

## 🤖 The Agent Team

| Agent | Tech Stack | Function |
| :--- | :--- | :--- |
| **Amadeus Agent** | `Amadeus API`, GPT-4.1 | Real-time flight search, airport discovery, multi-date cheapest scans, route comparison. |
| **Deep Search Agent** | `Perplexity` (`sonar-deep-research` / `sonar-reasoning`), Claude Sonnet 4 | Cultural, historical, and itinerary research prioritizing blogs/YouTube/Reddit. |
| **News Agent** | `NewsAPI` + `DuckDuckGoTools`, GPT-4o | Safety alerts, travel advisories, strikes, festivals — 7-day rolling window. |
| **Logistics Agent** | `Google Maps`, `Perplexity`, GPT-4.1 | Walking vs. driving decision (<400 m → walk), distance, live fuel price, cost estimate. |
| **Hospitality Agent** | `TripAdvisor` (RapidAPI), GPT-4o | Hotels + restaurants with amenities, nearby attractions, reviews, pricing, images. |
| **Audio Tour Agent** | `Gemini 2.5 Pro`, `ElevenLabs`, `Perplexity`, GPT-5 (formatter) | Cinematic AI audio guides with GCP-hosted playable URLs. |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  React + Three.js Frontend (Vite, TailwindCSS, react-markdown)   │
└───────────────────────────┬──────────────────────────────────────┘
                            │  SSE / multipart
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│            FastAPI (main.py)  –  /api/v1/*                        │
│       lifespan: init_resources() + DI wiring                      │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│    dependency-injector Container (core/container.py)              │
│    Singletons: LLM clients, agents, services                      │
│    Resources:  asyncpg.Pool, Supabase async client                │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                       ChatService                                 │
│  asyncio.gather(                                                  │
│      fetch_recent_history_direct(max_pairs=2),                    │
│      search_similar_sessions(episodic, limit=2),                  │
│      get_next_sequence_id()                                       │
│  )                                                                │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│   TeamAgent — Claude Sonnet 4, mode="coordinate", stream=True     │
│   Dynamic per-run context injection (history + episodic);         │
│   original instructions restored in `finally` (stateless).        │
│                                                                   │
│  ┌─────────┬──────────┬────────┬───────┬──────────┬────────────┐  │
│  │ Amadeus │Perplexity│NewsAPI │ GMaps │TripAdv.  │ ElevenLabs │  │
│  └─────────┴──────────┴────────┴───────┴──────────┴────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Memory System

### Working Memory (`services/working_memory_service.py`)
- Postgres table `working_memory(user_id, session_id, sequence_id, role, text_content, reasoning_content, attachments JSONB)`.
- `fetch_recent_history_direct(max_pairs)` — `ORDER BY sequence_id DESC LIMIT max_pairs*2`, reversed to chronological.
- `get_next_sequence_id()` uses `COALESCE(MAX(sequence_id), 0) + 1` for atomic turn ordering.
- `save_history_tuples(user, assistant)` — single 2-row SQL insert, atomic.

### Episodic Memory (`services/episodic_memory_service.py`)
- Postgres table `episodic_memory(... session_tags[], what_worked, what_not_worked, what_to_avoid, metadata JSONB, session_embeddings vector, ...)`.
- `search_similar_sessions(user_id, query_text, limit)` → SQL function `episodic_similarity_search(user_id, query_embedding, k)` over Voyage-3-large embeddings.
- `update_episodic_memory(user_id, session_id)`:
  1. Fetch full session history.
  2. Read prior summary (transaction).
  3. `openai.responses.parse(model=gpt-4o-2024-08-06, text_format=EpisodicMemory)` — blocking call wrapped via **`asyncio.to_thread`** to keep the event loop free.
  4. Re-embed concatenated content with Voyage-3-large.
  5. `INSERT ... ON CONFLICT (user_id, session_id) DO UPDATE`.

### Semantic / Knowledge Graph
- `neo4j` + `neo4j_graphrag` with a custom `VoyageEmbeddings` implementing `neo4j_graphrag.embeddings.base.Embedder` over `voyage-3-large`.
- `utils/schemas.py` defines the node/relationship ontology (Country, Port, Route, Shipment, Supplier, Carrier, CustomsProcess, RiskFactor, TimePeriod, …).
- `neo4j_ex_llm` = GPT-4o-mini at temp 0 — deterministic graph extraction.

---

## 🔁 Coordinator Event Loop

`TeamAgent.arun_team_intermediate_steps` consumes `team.arun(stream=True, stream_intermediate_steps=True)` and dispatches by `event.event`:

| Agno Event | Mapped to |
| :-- | :-- |
| `TeamRunResponseContent` (thinking only) | `type=reasoning` |
| `TeamRunCompleted` (clean content) | final `response` |
| `ToolCallStarted` / `ToolCallCompleted` | formatted `⚙️` / `🏁` reasoning lines |
| `TeamReasoningStep` / `TeamReasoningCompleted` | `🧠 Reasoning: ...` |

- Events deduplicated via `{event.event}_{tool_call_id or id(event)}` set.
- `_parse_tool_args` pretty-prints args differently per tool (`think`, `analyze`, `perplexity_search`, `search_news_everything`, `fetch_recent_history`, `fetch_all_session_history`, …).
- `_clean_final_response` pipes the raw assembled answer through `gpt-4o-mini` to strip routing chatter, `<think>` tags, and tool-status noise — keeping the UX clean without constraining the coordinator's verbosity.

---

## 📡 API Endpoints

| Method | Path | Purpose |
| :-- | :-- | :-- |
| `POST` | `/api/v1/stream-chat/stream` | Main chat SSE stream (`text/plain`, frames: `data: {"type","content","sequence","task_id"}\n\n`). |
| `POST` | `/api/v1/audio-tour/` | Cinematic audio-tour SSE stream from `AudioTourAgent`. |
| `POST` | `/api/v1/update-create/register_user/` | Register new user (Pydantic `User` validation, UUID, password hash). |
| `POST` | `/api/v1/update-create/update_session_data/` | Persist episodic summary for a session. |
| `POST` | `/api/v1/upload` | Multipart upload → GCP bucket → public CDN URL. |
| `POST` | `/api/v1/stream-chat/dummy_stream/` | Dev-only replay of `dummy_response.json` at 1 s cadence. |
| `GET`  | `/health`, `/` | Liveness + service info. |

---

## 🔑 Notable Engineering Decisions

- **Stateless coordinator with dynamic context injection** — prompt mutated per-run, restored in `finally`, preventing cross-request bleed and avoiding per-user agent instances.
- **Concurrent memory fetch** — `asyncio.gather(..., return_exceptions=True)` with per-task fallback cuts preamble latency ~3×.
- **pgbouncer-safe asyncpg pool** — `statement_cache_size=0`, `jit='off'`, `ssl='require'`, `min_size=2, max_size=10` — required for Supabase pooler.
- **Final-response cleaner** — cheap GPT-4o-mini post-processor lets the coordinator stay verbose/traceable during reasoning without polluting UX.
- **Custom `ElevenLabsTools` toolkit** — uploads TTS bytes directly to GCP and returns public CDN URLs (instead of base64), keeping streamed payloads small and enabling CDN caching.
- **Claude Sonnet 4 with `thinking` (budget 1024)** as coordinator; cheaper GPT-4.1 / GPT-4o / Gemini handle per-tool agent work.
- **Voyage-3-large** chosen over OpenAI embeddings for stronger retrieval on long-form travel narratives.

---

## 📂 Project Structure

```text
backend/
├── main.py                          # FastAPI entry, lifespan, routers, /upload
├── requirements.txt
└── src
    ├── agents/                      # Individual Agent Logic
    │   ├── amadeus/amadeus_agent.py         # Flights, airports, cheapest scans
    │   ├── deepsearch_agent/deep_search_agent.py  # Perplexity (2 modes)
    │   ├── elevenlabs/
    │   │   ├── audio_tour_agent.py          # Gemini 2.5 Pro + ElevenLabs
    │   │   ├── elevenlabs_agent.py
    │   │   └── elevenlabs_toolkit.py        # Custom: TTS → GCP → public URL
    │   ├── google_maps/google_maps_agent.py # Walk/drive + fuel-cost
    │   ├── news_agent/news_agent.py         # NewsAPI + DuckDuckGo
    │   └── traveladvisor/travel_advisor_agent.py  # TripAdvisor / RapidAPI
    ├── api/
    │   ├── chat_streaming.py                # SSE main chat
    │   ├── audio_tour_guide_api.py          # SSE audio
    │   ├── memory_management.py             # Episodic upsert endpoint
    │   ├── user_registration.py
    │   ├── development_stream.py
    │   └── health.py
    ├── core/
    │   └── container.py                     # dependency-injector wiring
    ├── providers/
    │   └── voyage_embedder.py               # voyage-3-large adapter
    ├── services/
    │   ├── chat_service.py                  # Orchestrator
    │   ├── team_agent_service.py
    │   ├── working_memory_service.py
    │   ├── episodic_memory_service.py
    │   └── user_registration_service.py
    ├── teams/
    │   ├── travel_agent_team.py             # Coordinator + event-stream loop
    │   └── agno_native_team.py              # Forked Agno Team core
    └── utils/
        ├── prompts.py                       # Coordinator prompt + cleaners
        ├── schemas.py                       # Pydantic models + KG ontology
        ├── gcs_uploads.py                   # GCP upload (PIL / bytes / str)
        └── constants.py                     # GCP credential assembly

frontend/                                    # React 18 + TS + Vite + Three.js
├── package.json                             # react-markdown, framer-motion,
└── src/                                     # @react-three/fiber, three-globe,
                                             # supabase-js, idb, react-router v7
```

---

## 🧰 Tech Stack

**Backend:** FastAPI · Agno AI · dependency-injector · asyncpg · Supabase (async) · Neo4j + neo4j-graphrag · Voyage AI (`voyage-3-large`) · OpenAI (GPT-4.1 / 4o / 4o-mini / GPT-5) · Anthropic Claude Sonnet 4 · Google Gemini 2.5 Pro · ElevenLabs · Amadeus · Perplexity · NewsAPI · Google Maps · TripAdvisor (RapidAPI) · GCP Cloud Storage · loguru · Pydantic v2.

**Frontend:** React 18 · TypeScript · Vite · TailwindCSS · Framer Motion · `@react-three/fiber` / `drei` / `three-globe` · `react-markdown` + `rehype-raw` + `remark-gfm` · `react-syntax-highlighter` · `@supabase/supabase-js` · `idb` (IndexedDB) · `react-router-dom` v7.

---

## 🚀 Running Locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Populate backend/.env with keys for: OPENAI_API_KEY, CLAUDE_API_KEY,
# VOYAGE_API_KEY, PERPLEXITY_API_KEY, NEWS_API_KEY, AMADEUS_CLIENT_ID/SECRET,
# NEO4J_URI/USERNAME/PASSWORD, SUPABASE_URL/KEY, POSTGRES_URI,
# GOOGLE_MAPS_API_KEY, TRIPADVISOR_API_KEY, GOOGLE_API_KEY,
# ELEVENLABS_API_KEY, BUCKET_NAME, CDN_API, GCP_* credentials.
python main.py     # uvicorn on :8080

# Frontend
cd frontend
npm install
npm run dev
```

---

See [ORBITIX_REPORT.md](ORBITIX_REPORT.md) for the full technical deep-dive and resume-ready bullet points.
