# 🇰🇪 Nairobi Swahili Bot — Complete System Breakdown

> **Autonomous X (Twitter) Persona Bots**
> Hybrid LLM routing, cloud-based RAG, and real-time monitoring dashboard.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [The Personas (Bot Identities)](#3-the-personas-bot-identities)
4. [Content Generation Pipeline](#4-content-generation-pipeline)
5. [Hybrid LLM Router (AI Brain)](#5-hybrid-llm-router-ai-brain)
6. [RAG System (Knowledge & Context)](#6-rag-system-knowledge--context)
7. [Content Validation (Quality Control)](#7-content-validation-quality-control)
8. [Smart Scheduler (Timing & Frequency)](#8-smart-scheduler-timing--frequency)
9. [X API Integration (Posting Engine)](#9-x-api-integration-posting-engine)
10. [Monitoring Dashboard](#10-monitoring-dashboard)
11. [Database & Logging](#11-database--logging)
12. [Configuration & Environment](#12-configuration--environment)
13. [Deployment & Operations](#13-deployment--operations)
14. [Technical Stack Summary](#14-technical-stack-summary)

---

## 1. Executive Summary

The **Nairobi Swahili Bot** is an autonomous social media system that operates **two AI-powered personas** on X (Twitter). These personas — **Juma** and **Amani** — post original content, quote-tweet trending discussions, and reply to mentions, all in authentic **Kiswahili/Sheng** language that mirrors real Nairobi Twitter culture.

### What Makes It Special

- **Two distinct AI personalities** with different tones, styles, and content preferences.
- **Hybrid AI brain** that intelligently switches between two different AI models (Grok and Claude) depending on the type of content being created.
- **Real-time learning** — the system continuously pulls fresh tweets from real Nairobi accounts and uses them as style references.
- **Three-layer content validation** that catches AI-sounding content before it's posted.
- **Human-like posting schedule** that respects Kenyan time zones, work hours, and natural posting patterns.
- **Full monitoring dashboard** with login, real-time stats, and detailed activity logs.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SMART SCHEDULER                             │
│            (Every 5 mins, 08:23-23:40 EAT)                     │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐      │
│  │ Time     │───▶│ Refresh RAG  │───▶│ Select Bot        │      │
│  │ Check    │    │ (Seed Accts) │    │ (Juma / Amani)    │      │
│  └──────────┘    └──────────────┘    └────────┬──────────┘      │
│                                               │                 │
│                                     ┌─────────▼─────────┐      │
│                                     │ Action Selection   │      │
│                                     │ 60% Post           │      │
│                                     │ 30% Quote          │      │
│                                     │ 10% Reply          │      │
│                                     └─────────┬─────────┘      │
└───────────────────────────────────────────────┼─────────────────┘
                                                │
                    ┌───────────────────────────▼──────────┐
                    │       CONTENT GENERATION PIPELINE     │
                    │                                       │
                    │  1. Choose Topic                      │
                    │  2. Fetch RAG Examples (Pinecone)     │
                    │  3. Route to LLM (Grok or Claude)     │
                    │  4. Generate Content                  │
                    │  5. Validate (3-Layer Check)          │
                    │  6. Post to X via API                 │
                    │  7. Log to Database                   │
                    └───────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    ┌──────────────┐     ┌──────────────┐        ┌──────────────┐
    │  SQLite DB   │     │  Pinecone    │        │   X API      │
    │  (Logging)   │     │  (Vectors)   │        │  (Twitter)   │
    └──────┬───────┘     └──────────────┘        └──────────────┘
           │
    ┌──────▼───────┐
    │  FastAPI      │
    │  REST API     │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  Dashboard   │
    │  (React/Vite)│
    └──────────────┘
```

---

## 3. The Personas (Bot Identities)

The system operates two distinct personas. Each has its own X account, personality, and content style.

### 🧔 Juma Mwangi (`@kamaukeeeraw`)

| Attribute | Detail |
|-----------|--------|
| **Personality** | Sarcastic, blunt, witty, street-smart, no-filter |
| **Tone** | Sarcastic |
| **Topics** | Politics, daily struggles, cost of living, traffic, hustle |
| **Proverb Style** | Uses sharp Swahili methali to roast situations with dark humor |
| **LLM Preference** | Primarily uses **Grok** (edgy, fast, street energy) |
| **Example Post** | *"Sasa, unaona hii Kenya yetu... Mtu akuambie bei ya rent imeshuka, cheka tu."* |

### 👩 Amani Akinyi (`@wanjikusagee`)

| Attribute | Detail |
|-----------|--------|
| **Personality** | Warm, wise, nurturing, cultural, empowering |
| **Tone** | Wise |
| **Topics** | Culture, heritage, family, women empowerment, youth, life wisdom |
| **Proverb Style** | Weaves Swahili methali naturally with warmth and cultural depth |
| **LLM Preference** | Uses **Claude** for cultural/wisdom content, **Grok** for everyday topics |
| **Example Post** | *"Ukitaka kujua njia, uliza waliokwisha pita. Mama alisema hivi..."* |

### Language Rules (Both Personas)

- Write in **Kiswahili** and **Sheng** naturally, mixing with English the way real Nairobians do.
- Target ratio: **45-55% Swahili**, **20-30% English**, **15-25% Sheng**.
- Swahili is the **dominant** local language. Sheng adds flavor but doesn't overpower.
- Use short, punchy sentences (1-2 max). Sometimes just a phrase.
- Reference specific Nairobi places: Eastlands, Westlands, CBD, Thika Road, etc.
- Each post includes time-of-day contextual grounding (morning rush, afternoon hustle, jioni vibes).

---

## 4. Content Generation Pipeline

When the scheduler triggers a cycle, this is the step-by-step process:

### Step 1: Topic Selection
A random topic is selected from a curated list of **10 topic categories**:

| Category | Example Topics |
|----------|---------------|
| **Politics** | Siasa, parliament, taxes, county government |
| **Daily Life** | Traffic, matatu, rent, water shortage, blackouts |
| **Food** | Nyama, ugali, sukuma, mutura, githeri |
| **Hustle** | Side hustle, biashara, pesa, betting, jua kali |
| **Proverbs & Wisdom** | Swahili methali, hekima ya wazee, masomo ya maisha |
| **Diaspora** | Life abroad, homesick, immigration, familia back home |
| **Family & Home** | Nyumbani, familia, masomo ya maisha, December |
| **Ceremonies** | Sherehe za jadi, desturi, mila za wazee |
| **Reflection** | Kutafakari maisha, safari ya maisha, growing up Kenyan |
| **Culture** | Urithi, muziki wa jadi, usiku wa burudani Nairobi |

### Step 2–7: RAG → LLM → Validate → Post → Log
Same pipeline as before (see Architecture diagram).

---

## 5. Hybrid LLM Router (AI Brain)

### The Two Models

| Model | Provider | Best For | Temperature |
|-------|----------|----------|-------------|
| **Grok 4 Fast** | xAI | Street energy, sarcasm, everyday topics, politics, hustle | 0.8 |
| **Claude Sonnet 4** | Anthropic | Cultural wisdom, methali, diaspora nostalgia, empathy, family | 0.7 |

### Claude Trigger Keywords

| Category | Keywords |
|----------|----------|
| **Proverbs** | methali, proverb, wisdom, hekima, wazee, elders, ancestors |
| **Culture** | heritage, urithi, traditional, sherehe, ceremony, desturi, mila |
| **Empathy** | miss, home, family, nyumbani, familia, nyumba, homesick |
| **Diaspora** | diaspora, abroad, ughaibuni, immigration, visa, back home |
| **Reflective** | reflection, kutafakari, life, journey, maisha, safari, lessons |

If 2+ triggers match → route to Claude. Otherwise → Grok (default).

---

## 6. RAG System (Knowledge & Context)

### Seed Accounts (Content Sources)

| Category | Accounts |
|----------|----------|
| **Nairobi Locals** | @Ma3Route, @_CrazyNairobian, @bonifacemwangi, @GabrielOguda, @EricOmondi |
| **Traffic & Daily Life** | @KenyanTraffic, @naborealkenya |
| **News & Culture** | @NairobiLeo, @KenyanHistory, @MutahiKagwe, @Kilonje_Africa |
| **Community & Vibes** | @OleItumbi, @KenyanVibe, @NairobiNights |
| **Kenyan Diaspora** | @kenyandiaspora, @kenya_usa |

### Dynamic Vocabulary Injection

Every 5 minutes, the system extracts trending words and hashtags from freshly fetched tweets and injects them into the Content Validator as valid local speak.

---

## 7. Content Validation (Quality Control)

### Layer 1: Anti-Pattern Filter (Hard Fails)
Catches AI red flags: over-length, repetitive openers, English proverb framers, formal connectors, invented hashtags, emoji stacking.

### Layer 2: Style Authenticity (Scoring)
Measures code-switching ratio (Swahili/Sheng vs English), word length, punctuation density, capitalization.

### Layer 3: Contextual Fit (Time Awareness)
Ensures content matches the current time of day in Kenya.

**Pass**: Score ≥ 50 AND zero hard-fail issues. **Fail**: regenerate up to 2 retries.

---

## 8. Smart Scheduler (Timing & Frequency)

| Period | Time (EAT) | Max Posts/Hour |
|--------|-----------|----------------|
| **Sleep** | 23:40 — 08:23 | 0 |
| **Normal** | 08:23 — 10:00, 15:00 — 23:40 | 6 |
| **Work** | 10:00 — 15:00 | 2 |

Minimum gap: 2 minutes between posts. Check frequency: every 5 minutes.

---

## 9. X API Integration

Each persona has its own OAuth credentials. Capabilities: post, quote, reply, retweet, get mentions, fetch user tweets, search.

**Dry Run Mode**: When `DRY_RUN=true`, all actions are simulated without posting.

---

## 10. Monitoring Dashboard

React app (Vite) at `http://localhost:5173`. Pages: Overview, Posts, LLM Routing, RAG Activity, Knowledge Base, Bot Logic, Validation, Errors.

**Default login**: `admin` / `nairobi2024`

---

## 11. Database & Logging

SQLite database (`data/nairobi.db`) with tables: posts, rag_activity, llm_routing, knowledge_base, errors.

Log file: `nairobi_bot.log`

---

## 12. Configuration & Environment

Key settings in `.env`:

| Variable | Purpose |
|----------|---------|
| `GROK_API_KEY` | xAI API key |
| `CLAUDE_API_KEY` | Anthropic API key |
| `PINECONE_API_KEY` / `PINECONE_INDEX_NAME` | Vector DB (default: `nairobi-swahili-rag`) |
| `DRY_RUN` | false = production, true = simulation |
| `KAMAU_*` / `WANJIKU_*` | Persona X API credentials |

---

## 13. Deployment & Operations

### Local
```bash
source venv/bin/activate
python3 -m uvicorn api.server:app --host 0.0.0.0 --port 8000  # API
DRY_RUN=true python3 main.py  # Bot (dry run)
cd dashboard && npm run dev   # Dashboard
```

### Docker
```bash
docker-compose up -d
```

### Processes

| Process | Role | Port |
|---------|------|------|
| `main.py` | Bot scheduler | None |
| `uvicorn` | FastAPI REST API | 8000 |
| `npm run dev` | Dashboard (Vite) | 5173 |

---

## 14. Technical Stack Summary

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11+ |
| **AI Model 1** | Grok 4 Fast (xAI) |
| **AI Model 2** | Claude Sonnet 4 (Anthropic) |
| **Vector DB** | Pinecone (Serverless, AWS) |
| **Embeddings** | sentence-transformers (MiniLM-L6-v2) |
| **Database** | SQLite |
| **Scheduler** | APScheduler |
| **X API** | Tweepy |
| **API Server** | FastAPI + Uvicorn |
| **Frontend** | React + Vite |
| **Auth** | JWT |
| **Containerization** | Docker + Docker Compose |

---

*Document updated: February 2026*
*Nairobi Swahili Bot v2.0*
