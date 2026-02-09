# 🇰🇪 Kikuyu Project — X Persona Bots

Autonomous X (Twitter) bot system for authentic Kikuyu/Nairobi personas with hybrid LLM routing (Grok + Claude) and cloud-based RAG.

## ✨ Features

- **2 Distinct Personas**: Kamau (sarcastic hustler) & Wanjiku (warm sage)
- **Hybrid LLM Routing**: Grok for daily/edgy content, Claude for proverbs/wisdom
- **Cloud RAG**: Pinecone vector store for authentic slang/phrasing
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
│  ┌────────────────────────────────────────────▼─────────────┐ │
│  │                    Persona Bots                          │ │
│  │  ┌─────────────────┐      ┌─────────────────┐            │ │
│  │  │ Kamau @KamauRawKE│      │ Wanjiku @WanjikuSage│       │ │
│  │  │ Sarcastic/Edgy  │      │ Warm/Wise        │           │ │
│  │  └────────┬────────┘      └────────┬─────────┘           │ │
│  └───────────┼───────────────────────┼──────────────────────┘ │
│              │                       │                        │
│              └───────────┬───────────┘                        │
│                          ▼                                    │
│                    X API (Post/Quote/Reply)                   │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- X Developer account with API access
- Pinecone account (free tier available)
- Grok API key (xAI) - with Grok 4 model access enabled
- Claude API key (Anthropic)

### Local Setup

```bash
# Clone and setup
cd "Kikuyu Project"
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

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
# Build and run
docker-compose up -d

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
| `GROK_MODEL` | Grok 4 model to use (grok-4-fast, grok-4, grok-4.1, grok-4-heavy) | `grok-4-fast` |

## 📁 Project Structure

```
Kikuyu Project/
├── main.py               # Entry point
├── config.py             # Settings & credentials
├── llm/
│   ├── router.py         # Hybrid LLM routing
│   ├── grok_client.py    # Grok API
│   └── claude_client.py  # Claude API
├── rag/
│   ├── pinecone_store.py # Vector storage
│   └── embeddings.py     # Embedding generation
├── x_api/
│   ├── client.py         # X posting client
│   ├── retrieval.py      # Seed account fetcher
│   └── engagement.py     # Engagement scoring
├── personas/
│   └── base.py           # Kamau & Wanjiku configs
├── scheduler/
│   └── loop.py           # MVP loop
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🎭 Personas

### Kamau Njoroge (@KamauRawKE)
> "Niaje wasee wa mtaa! 🔥 Kamau hapa, Eastlands representative."

- **Tone**: Sarcastic, blunt, dark humor
- **Topics**: Politics, daily struggles, traffic, cost of living
- **LLM**: Primarily Grok (edgy/street energy)

### Wanjiku Njeri (@WanjikuSage)
> "Rĩrĩa mwagĩrĩru, my dear ones! 🌸"

- **Tone**: Warm, wise, nurturing
- **Topics**: Culture, heritage, family, wisdom
- **LLM**: Routes to Claude for proverbs/cultural content

## 🔄 MVP Loop

Every 4-12 hours:
1. **Retrieve** fresh posts from seed accounts
2. **Store** in Pinecone RAG for style reference
3. **Find** engaging content for quotes (likes≥20, RTs≥5)
4. **Generate** 1-2 original posts per persona
5. **Quote** top engaging content with commentary
6. **Reply** to mentions

## 📊 Monitoring Dashboard

A real-time React dashboard to monitor your bots:

| Feature | Description |
|---------|-------------|
| **Overview** | Total posts, engagement stats, LLM usage pie chart |
| **Posts** | Filterable timeline of all posts by persona |
| **RAG Activity** | Fetch/store/retrieval logs with vector counts |
| **LLM Routing** | Grok vs Claude decision tracker |
| **Errors** | Filterable error log with tracebacks |

### Access Dashboard
```bash
# Run all services
docker-compose up -d

# Dashboard: http://localhost:3000
# Default login: admin / kikuyu2024
```

## 🔒 Security Features

- **JWT Authentication**: Secure login with token-based auth
- **Rate Limiting**: 100 requests/minute per IP
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, HSTS
- **Request Logging**: All requests logged for auditing
- **Production Mode**: Disable API docs, enforce strict CORS

### Production Checklist
1. Change `DASHBOARD_PASSWORD` to a strong password
2. Generate a secure `DASHBOARD_SECRET_KEY` (32+ chars)
3. Set `PRODUCTION=true` in environment
4. Configure `CORS_ORIGINS` to your domain only

## ☁️ Cloud Deployment

### Railway
```bash
railway init
railway up
```

### Render
1. Create new Web Service
2. Connect GitHub repo
3. Set environment variables from `.env`
4. Deploy

### AWS ECS / Fargate
1. Push image to ECR
2. Create ECS task definition
3. Run as scheduled task or always-on service

## ⚠️ Safety Guidelines

- **Balanced politics**: Fair critique, no hate/incitement
- **No misinformation**: Factual content only
- **Rate limits**: Respects X API limits
- **Deduplication**: Won't quote same tweet twice

## 📄 License

MIT
