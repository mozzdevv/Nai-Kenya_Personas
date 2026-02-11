# 🇰🇪 Kikuyu Project — X Persona Bots

Autonomous X (Twitter) bot system for authentic Kikuyu/Nairobi personas with hybrid LLM routing (Grok + Claude), cloud-based RAG, and a built-in content authenticity validator.

## ✨ Features

- **2 Distinct Personas**: Kamau (sarcastic hustler) & Wanjiku (warm sage)
- **Hybrid LLM Routing**: Grok for daily/edgy content, Claude for proverbs/wisdom
- **Cloud RAG**: Pinecone vector store for authentic slang/phrasing
- **Content Authenticity Validator**: 3-layer pipeline catches AI patterns before posting
- **Full X Integration**: Post, quote, retweet, reply
- **Monitoring Dashboard**: Real-time stats, post history, LLM routing, error logs
- **Production Security**: Rate limiting, JWT auth, security headers
- **Dockerized**: 3-container setup ready for cloud deployment

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    APScheduler (4-12hr loop)                  │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐     │
│  │ Seed     │───▶│  Pinecone   │───▶│  Hybrid Router   │     │
│  │ Accounts │    │  RAG Store  │    │  (Grok/Claude)   │     │
│  └──────────┘    └─────────────┘    └────────┬─────────┘     │
│                                               │               │
│                                    ┌──────────▼─────────┐     │
│                                    │ Content Validator   │     │
│                                    │ (Anti-AI Pipeline)  │     │
│                                    └──────────┬─────────┘     │
│                                               │               │
│  ┌────────────────────────────────────────────▼─────────────┐ │
│  │                    Persona Bots                          │ │
│  │  ┌─────────────────┐      ┌─────────────────┐            │ │
│  │  │ Kamau @kamaukeeeraw│    │ Wanjiku @wanjikusagee│       │ │
│  │  │ Sarcastic/Edgy  │      │ Warm/Wise        │           │ │
│  │  └────────┬────────┘      └────────┬─────────┘           │ │
│  └───────────┼───────────────────────┼──────────────────────┘ │
│              └───────────┬───────────┘                        │
│                          ▼                                    │
│                    X API (Post/Quote/Reply)                   │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- X Developer account with API access
- Pinecone account (free tier available)
- Grok API key (xAI) — Grok 4 model access
- Claude API key (Anthropic)

### Local Setup

```bash
# Clone and setup
cd "Kikuyu Project"
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run (dry-run mode for testing)
DRY_RUN=true python main.py
```

### Docker Deployment

```bash
# Build and run all 3 services (bot, API, dashboard)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOOP_INTERVAL_HOURS` | Time between posting cycles | `6` |
| `DRY_RUN` | If true, don't actually post | `false` |
| `PINECONE_INDEX_NAME` | Pinecone index name | `kikuyu-rag` |
| `GROK_MODEL` | Grok 4 model to use | `grok-4-fast` |

## 📁 Project Structure

```
Kikuyu Project/
├── main.py                  # Entry point
├── config.py                # Settings, credentials, seed accounts & topics
├── llm/
│   ├── router.py            # Hybrid LLM routing (Grok/Claude decision)
│   ├── grok_client.py       # Grok API client
│   └── claude_client.py     # Claude API client
├── rag/
│   ├── pinecone_store.py    # Pinecone vector storage
│   └── embeddings.py        # Sentence-transformer embeddings
├── x_api/
│   ├── client.py            # X posting client (Tweepy)
│   ├── retrieval.py         # Seed account tweet fetcher
│   └── engagement.py        # Engagement scoring & filtering
├── personas/
│   └── base.py              # Persona configs (Kamau/Wanjiku) + anti-AI prompt system
├── validation/
│   ├── __init__.py
│   └── content_validator.py # 3-layer authenticity validation engine
├── scheduler/
│   └── loop.py              # MVP loop with validator integration
├── api/
│   ├── server.py            # FastAPI dashboard backend
│   ├── database.py          # SQLite logging (posts, RAG, routing, errors)
│   ├── auth.py              # JWT authentication
│   └── security.py          # Rate limiting, headers
├── dashboard/               # React frontend (Vite)
│   └── src/pages/
│       ├── Overview.jsx
│       ├── Posts.jsx         # Posts timeline (with authenticity scores)
│       ├── RagActivity.jsx   # RAG fetch/store/retrieve logs
│       ├── Routing.jsx       # LLM routing decisions
│       └── Errors.jsx
├── Dockerfile               # Bot container
├── Dockerfile.api           # API container (lightweight)
├── docker-compose.yml       # 3-service orchestration
├── requirements.txt         # Full dependencies (bot)
└── requirements-api.txt     # Lightweight API dependencies
```

## 🛡️ Content Authenticity Validator

Every generated post passes through a 3-layer validation pipeline before posting. If a post fails, it's regenerated up to 2 more times with the rejection reason appended to the LLM prompt.

### Layer 1: Anti-Pattern Filter
Catches obvious AI tells:
- **Repetitive openers** — Detects same opening phrase as last 5 posts → FAIL
- **English proverb translations** — "which means", "as our elders say" → FAIL
- **Formal connectors** — "Furthermore", "Additionally" → FAIL
- **Invented hashtags** — Only known Kenyan hashtags allowed (e.g. `#KOT`)
- **Exclamation/emoji stacking** — Real tweets don't do `!!!` or 5+ emojis
- **Over-structured** — Real tweets are 1 thought, not intro→body→conclusion

### Layer 2: Style Authenticity
Scores tweets against real Nairobi Twitter patterns:
- **Code-switching ratio**: ~60% Swahili/Sheng, ~25% English, ~15% Kikuyu
- **Word length**: Real tweets use shorter words
- **Punctuation density**: Real tweets have sparse punctuation
- **Capitalization**: Real tweets are mostly lowercase

### Layer 3: Contextual Grounding
- **Time-of-day awareness**: Morning references blocked at night, and vice versa (Nairobi = UTC+3)
- **Context injection**: System prompts include current Nairobi time-of-day context

### Scoring
Each post gets an **authenticity score (0–100)**. Posts need ≥50 and zero hard failures to pass. Scores are stored in the database and visible on the dashboard.

## 🎭 Personas

### Kamau Njoroge (@kamaukeeeraw)
> "Niaje wasee wa mtaa! 🔥 Kamau hapa, Eastlands representative."

- **Tone**: Sarcastic, blunt, dark humor
- **Topics**: Politics, daily struggles, traffic, cost of living
- **LLM**: Primarily Grok (edgy/street energy)

### Wanjiku Njeri (@wanjikusagee)
> "Rĩrĩa mwagĩrĩru, my dear ones! 🌸"

- **Tone**: Warm, wise, nurturing
- **Topics**: Culture, heritage, family, wisdom
- **LLM**: Routes to Claude for proverbs/cultural content

## 🔄 MVP Loop

Every 4-12 hours:
1. **Retrieve** fresh posts from 20+ seed accounts (Nairobi-focused)
2. **Store** in Pinecone RAG for style reference
3. **Find** engaging content for quotes (likes≥20, RTs≥5)
4. **Generate** 1-2 original posts per persona
5. **Validate** each post through the authenticity pipeline (retry up to 2x on failure)
6. **Quote** top engaging content with commentary
7. **Reply** to mentions

## 📊 Monitoring Dashboard

A real-time React dashboard at `http://localhost:3000`:

| Page | Description |
|------|-------------|
| **Overview** | Total posts, engagement stats, LLM usage pie chart |
| **Posts** | Filterable timeline with authenticity scores |
| **RAG Activity** | Fetch/store/retrieval logs with explainer cards |
| **LLM Routing** | Grok vs Claude decisions with trigger analysis |
| **Knowledge Base** | RAG corpus contents and sources |
| **Errors** | Filterable error log with tracebacks |

**Default login**: `admin` / `kikuyu2024`

## 🔒 Security

- **JWT Authentication**: Token-based login for dashboard
- **Rate Limiting**: 100 req/min per IP
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, HSTS
- **Request Logging**: All requests logged
- **Production Mode**: Disable docs, enforce strict CORS

### Production Checklist
1. Change `DASHBOARD_PASSWORD` to a strong password
2. Generate a secure `DASHBOARD_SECRET_KEY` (32+ chars)
3. Set `PRODUCTION=true`
4. Configure `CORS_ORIGINS` to your domain only

## ☁️ Cloud Deployment

### Railway
```bash
railway init
railway up
```

### Render
1. Create new Web Service → connect GitHub repo
2. Set environment variables from `.env`
3. Deploy

### AWS ECS / Fargate
1. Push image to ECR
2. Create ECS task definition
3. Run as scheduled task or always-on service

## ⚠️ Safety Guidelines

- **Balanced politics**: Fair critique, no hate/incitement
- **No misinformation**: Factual content only
- **Rate limits**: Respects X API limits
- **Deduplication**: Won't quote same tweet twice
- **Anti-AI detection**: Content validator prevents detectable AI patterns

## 📄 License

MIT
