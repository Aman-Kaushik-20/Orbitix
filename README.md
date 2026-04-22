# 🌍 Orbitix: Deep Travel Agent Planner

**A multi-agent AI system designed to generate deep travel insights using realtime and structured dat from specialized Agents and Public Resources.**

<a href="https://x.com/akhtarrr012/status/1955229103495184846?s=20">
  <img width="1898" height="797" alt="Demo" src="https://github.com/user-attachments/assets/35896c5c-a35c-4ef1-ac95-0f5af19fe45a" />
</a>

---

## 📖 Overview

Orbitix is an autonomous multi-agent system that acts as a comprehensive travel concierge. Unlike standard travel bots, Orbitix leverages a **Knowledge Graph (Neo4j)** and **Hybrid RAG** to provide context-aware, deep insights. 

It orchestrates specialized agents to handle everything from real-time flight data to hyper-local news and restaurant recommendations, delivering a personalized itinerary with an AI-generated voice guide.

## 🚀 Key Features

* **⚡ High Performance:** Built on **Agno AI** architecture for streaming, async, and low-latency responses (Time to First Token < 1.5s).
* **🧠 Advanced Memory:** Utilizes **Supabase** for managing Working, Episodic, and Semantic memory, allowing the AI to "remember" user preferences across sessions.
* **🕸️ Knowledge Graph RAG:** Integrates **Neo4j** to model complex relationships between locations, preferences, and constraints.
* **🔍 Hybrid Search:** Implements **Voyage-3 embeddings**, **BM25**, and custom re-ranking (Naive + Alpha) to optimize information retrieval.
* **🎙️ Audio Guide:** Generates immersive audio travel guides using **ElevenLabs**.

---

## 🤖 The Agent Team

Orbitix employs a modular team of specialized agents, coordinated to deliver a unified experience:

| Agent | Tech Stack | Function |
| :--- | :--- | :--- |
| **Amadeus Agent** | `Amadeus API` | Real-time flight search, airport data, and pricing. |
| **Deep Search** | `Perplexity` | Deep web research for cultural context and hidden gems. |
| **News Agent** | `News API` | Scans for real-time events (festivals, strikes, weather alerts). |
| **Logistics Agent** | `Google Maps` | Calculates routes, distances, and transit costs. |
| **Hospitality Agent** | `Travel Advisor` | Finds hotels and restaurants based on user vibe/budget. |
| **Voice Agent** | `ElevenLabs` | Narrates the itinerary and provides audio tours. |

---

## 📂 Project Structure

```text
backend/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
└── src
    ├── agents/                 # Individual Agent Logic
    │   ├── amadeus/            # Flight search logic
    │   ├── deepsearch_agent/   # Perplexity integration
    │   ├── elevenlabs/         # Audio generation
    │   ├── google_maps/        # Routing & Logistics
    │   ├── news_agent/         # Real-time updates
    │   └── traveladvisor/      # Hotels & Restaurants
    ├── api/                    # FASTAPI Endpoints
    │   ├── chat_streaming.py
    │   ├── memory_management.py
    │   └── ...
    ├── core/                   # Core container logic
    ├── providers/              # External Integrations
    │   ├── neo4j_graph_query.py
    │   └── voyage_embedder.py
    ├── services/               # Business Logic
    │   ├── team_agent_service.py
    │   └── ...
    ├── teams/                  # Orchestration Logic
    │   ├── agno_native_team.py
    │   └── travel_agent_team.py
    └── utils/                  # Helpers (GCS, Prompts, Schemas)
