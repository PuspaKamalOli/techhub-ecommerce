# TechHub E-commerce Platform

A production-grade **agentic AI system** where an LLM autonomously performs multi-step e-commerce operations — search, compare, cart, checkout — using ReAct reasoning, tool-calling, and persistent memory.

Built with Django, LangChain, pgvector, Redis, and Stripe.

> Designed to simulate real-world AI systems with autonomous decision-making, secure execution boundaries, and production-ready infrastructure.

![Django](https://img.shields.io/badge/Django-5.0+-green) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![LangChain](https://img.shields.io/badge/LangChain-Agentic-red) ![pgvector](https://img.shields.io/badge/pgvector-Semantic_Search-purple) ![Redis](https://img.shields.io/badge/Redis-Cache_%26_Memory-red) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎥 Demo (Agent in Action)

▶️ Watch the AI autonomously reason, select tools, and execute real backend actions in real-time:
**[https://drive.google.com/file/d/1UV7knubOIa0xRY46Qf_rH71ZC86-E8N7/view?usp=drive_link](https://drive.google.com/file/d/1UV7knubOIa0xRY46Qf_rH71ZC86-E8N7/view?usp=drive_link)**

---

## ⚡ Example Capability

> **User:** "Find the cheapest Samsung phone and add it to my cart"
> **Agent Flow:** `search_products` → compare prices → select optimal → `add_to_cart`
> **Result:** Product added successfully via autonomous tool execution

---

## 🧠 Core Architecture

```
User → Django API → LangChain ReAct Agent → Tool Calls → Database/Stripe → Response
```

---

## What Makes This Different

Most e-commerce chatbots rely on predefined intents.

TechHub uses a **ReAct-based LLM agent** that:
- reasons step-by-step about what the user needs
- dynamically selects from 13 backend tools
- executes real database actions with retry/resilience logic

No hardcoded workflows — the LLM dynamically plans and executes actions based on context.

---

## 🚀 Why This Matters

This project demonstrates how LLMs can move beyond chat interfaces into **autonomous systems that interact with real-world APIs and databases** — a key direction for modern AI applications in production.

---

## Key Features

**🤖 Agentic AI System**
- 13 tools: cart, wishlist, orders, products, profile — all via natural language
- RAG (FAISS + HuggingFace embeddings) for company policy/FAQ answers
- Persistent memory via `RedisChatMessageHistory` — survives logouts
- `pgvector` semantic search for contextual queries ("waterproof gym headphones")
- Human-in-the-Loop checkout — agent generates a verification link instead of placing orders directly
- Jailbreak/injection heuristic filter runs before any LLM API call
- Failure handling, retry logic, and rate-limit resilience for all LLM/tool interactions

**⚙️ Production-Grade Backend**
- NeonDB (serverless Postgres) + `pgvector`
- Redis for caching and agent memory
- JWT/RBAC for stateless API auth
- Celery for async task queues
- SSE/WebSocket-ready streaming pipeline
- Stateless + stateful hybrid design (JWT auth + Redis-backed conversational memory)

**🛒 Full E-commerce**
- Product catalog with search, filters, categories, reviews
- Cart, wishlist, order management with Stripe payments
- Bayesian + time-decay recommendation engine (not basic "highest sales" sorting)
- Analytics dashboard with sales metrics and product performance

**🎨 UI**
- Dark theme with glassmorphism, gradient accents, micro-animations
- Bootstrap 5.3 dark mode, Inter font, fully responsive

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Django 5+, Python 3.9+, Celery |
| Database | NeonDB (Postgres), pgvector, Redis |
| AI | LangChain, Ollama (`qwen2.5:3b`) / Groq, FAISS, HuggingFace |
| Frontend | Bootstrap 5.3, HTML/CSS/JS, WebSockets/SSE |
| Payments | Stripe API |
| Auth | Django sessions + JWT/RBAC |

---

## Quick Start

```bash
# 1. Clone & set up environment
git clone https://github.com/yourusername/techhub-ecommerce.git
cd techhub-ecommerce
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Install & start Redis
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt install redis-server && sudo systemctl start redis

# 3. Configure environment
cp .env.example .env  # then edit .env with your keys
```

**Minimum `.env` to get started:**
```env
DATABASE_URL = 'api key from neon for postgresql'
SECRET_KEY=your-django-secret-key
GROQ_API_KEY=your-groq-key  # get free key at console.groq.com
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

```bash
# 4. Database & run
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# 5. In a separate terminal — start Celery
celery -A techhub worker --loglevel=info
```

**Access:** `http://127.0.0.1:8000` · Admin: `http://127.0.0.1:8000/admin`

---

## Agent Tools Reference

| Tool | Description |
|------|-------------|
| `search_products` | Full-text search across names, descriptions, categories |
| `semantic_search_products` | pgvector cosine similarity search |
| `get_product_details` | Price, stock, specs, SKU, discount status |
| `get/add/remove/update` cart | Full cart management with stock validation |
| `get/add/remove` wishlist | Wishlist management with duplicate prevention |
| `get_user_orders` | Order history with statuses and amounts |
| `generate_checkout_link` | HITL-safe checkout verification link |
| `get_user_profile` | Username, email, join date, order count |

---

## Project Structure

```
techhub-ecommerce/
├── AI/                    # Agentic system
│   ├── agent.py           # ReAct agent, AgentExecutor, retry logic
│   ├── tools.py           # 13 @tool-decorated ORM tools
│   ├── config.py          # LLMConfig, RAGConfig, ChatbotConfig
│   ├── speech.txt         # RAG knowledge base
│   └── services/rag_service.py
├── products/ cart/ orders/ users/ wishlist/
├── payment_processing/
├── chatbot/               # API views + URLs
├── techhub/               # Django project config
├── templates/ static/ media/
└── manage.py
```

---

## API Endpoints (Summary)

| Resource | Endpoints |
|----------|-----------|
| Products | `GET /products/`, `GET /product/<slug>/`, `GET /search/` |
| Cart | `GET /cart/`, `POST /cart/add/<id>/`, `POST /cart/update/<id>/` |
| Orders | `GET /orders/history/`, `POST /orders/checkout/` |
| Wishlist | `GET /wishlist/`, `POST /wishlist/add/<id>/` |
| Payments | `GET /payments/payment/<id>/`, `POST /payments/webhook/stripe/` |
| Analytics | `GET /analytics/` (admin only) |

Full API docs with request/response examples in [`API_DOCS.md`](API_DOCS.md).

---

## Recommendation Engine

Products are ranked using a **Bayesian average** (prevents single-review outliers) combined with a **time-decay factor** `score / (age_days + 2)^1.5`. New products get a visibility boost; established ones with strong reviews stay competitive. Powers the homepage, related products, and default catalog sort.

---

## Contributing

```bash
git checkout -b feature/your-feature
# make changes
git commit -m "feat: describe your change"
git push origin feature/your-feature
# open a pull request
```

Follow PEP 8, write tests, update docs.

---

## License

MIT — see [LICENSE](LICENSE).
