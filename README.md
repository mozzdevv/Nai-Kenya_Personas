# 🇰🇪 Nairobi Swahili Bot — X Persona Bots

Autonomous X (Twitter) bot system for authentic Nairobi Swahili personas with hybrid LLM routing (Grok + Claude), cloud-based RAG, and a built-in content authenticity validator.

## ✨ Features

- **2 Distinct Personas**: Juma (sarcastic hustler) & Amani (warm sage)
- **Hybrid LLM Routing**: Grok for daily/edgy content, Claude for methali/wisdom
- **Cloud RAG**: Pinecone vector store for authentic Swahili/Sheng phrasing
- **Content Authenticity Validator**: 3-layer pipeline catches AI patterns before posting
- **Full X Integration**: Post, quote, retweet, reply
- **Monitoring Dashboard**: Real-time stats, post history, LLM routing, error logs
- **Production Security**: Rate limiting, JWT auth, security headers
- **Dockerized**: 3-container setup ready for cloud deployment

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    APScheduler (5-min check loop)             │
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
│  │  │ Juma @kamaukeeeraw│    │ Amani @wanjikusagee│          │ │
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
cd "Nairobi Swahili Bot"
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
| `PINECONE_INDEX_NAME` | Pinecone index name | `nairobi-swahili-rag` |
| `GROK_MODEL` | Grok 4 model to use | `grok-4-fast` |

## 📁 Project Structure

```
Nairobi Swahili Bot/
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
│   └── base.py              # Persona configs (Juma/Amani) + anti-AI prompt system
├── validation/
│   └── content_validator.py # 3-layer authenticity validation engine
├── scheduler/
│   └── loop.py              # Smart scheduler with validator integration
├── api/
│   ├── server.py            # FastAPI dashboard backend
│   ├── database.py          # SQLite logging (posts, RAG, routing, errors)
│   ├── auth.py              # JWT authentication
│   └── security.py          # Rate limiting, headers
├── dashboard/               # React frontend (Vite)
│   └── src/pages/
│       ├── Overview.jsx
│       ├── Posts.jsx
│       ├── RagActivity.jsx
│       ├── Routing.jsx
│       └── Errors.jsx
├── Dockerfile               # Bot container
├── Dockerfile.api           # API container
├── docker-compose.yml       # 3-service orchestration
├── requirements.txt         # Full dependencies (bot)
└── requirements-api.txt     # Lightweight API dependencies
```

## 🛡️ Content Authenticity Validator

Every generated post passes through a 3-layer validation pipeline before posting. If a post fails, it's regenerated up to 2 more times with the rejection reason appended to the LLM prompt.

### Layer 1: Anti-Pattern Filter
Catches obvious AI tells: repetitive openers, English proverb translations, formal connectors, invented hashtags, emoji stacking, over-structured tweets.

### Layer 2: Style Authenticity
Scores tweets against real Nairobi Twitter patterns:
- **Code-switching ratio**: ~45-55% Swahili, ~20-30% English, ~15-25% Sheng
- **Word length**: Real tweets use shorter words
- **Punctuation density**: Real tweets have sparse punctuation
- **Capitalization**: Real tweets are mostly lowercase

### Layer 3: Contextual Grounding
Time-of-day awareness: morning references blocked at night, and vice versa (Nairobi = UTC+3).

## 🎭 Personas

### Juma Mwangi (@kamaukeeeraw)
> "Niaje wasee wa mtaa! 🔥 Juma hapa, Eastlands representative."

- **Tone**: Sarcastic, blunt, dark humor
- **Topics**: Politics, daily struggles, traffic, cost of living
- **LLM**: Primarily Grok (edgy/street energy)

### Amani Akinyi (@wanjikusagee)
> "Habari zenu wapendwa! 🌸 Amani hapa, tuko pamoja."

- **Tone**: Warm, wise, nurturing
- **Topics**: Culture, heritage, family, wisdom
- **LLM**: Routes to Claude for methali/cultural content

## 🔄 Smart Scheduler

Every 5 minutes (08:23–23:40 EAT):
1. **Retrieve** fresh posts from 16+ seed accounts (Nairobi-focused)
2. **Store** in Pinecone RAG for style reference
3. **Extract** dynamic vocabulary from trending words
4. **Select** one bot randomly (Juma or Amani)
5. **Roll** action type: 60% original, 30% quote, 10% reply
6. **Generate** content → **Validate** through 3-layer pipeline → **Post** to X

## 📊 Monitoring Dashboard

A real-time React dashboard at `http://localhost:5173`:

| Page | Description |
|------|-------------|
| **Overview** | Total posts, engagement stats, LLM usage pie chart |
| **Posts** | Filterable timeline with authenticity scores |
| **RAG Activity** | Fetch/store/retrieval logs |
| **LLM Routing** | Grok vs Claude decisions with trigger analysis |
| **Knowledge Base** | RAG corpus contents and sources |
| **Errors** | Filterable error log with tracebacks |

**Default login**: `admin` / `nairobi2024`

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

### Docker Compose
```bash
docker-compose up -d --build
```

## ⚠️ Safety Guidelines

- **Balanced politics**: Fair critique, no hate/incitement
- **No misinformation**: Factual content only
- **Rate limits**: Respects X API limits
- **Deduplication**: Won't quote same tweet twice
- **Anti-AI detection**: Content validator prevents detectable AI patterns

## 📄 License

MIT
