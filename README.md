#  TechHub E-commerce Platform

A comprehensive, full-featured e-commerce platform built with Django, featuring a **fully agentic AI chatbot** powered by LangChain + Groq (Llama 3.3 70B), a premium dark-themed UI with glassmorphism, secure Stripe payment processing, and real-time analytics.

![Django](https://img.shields.io/badge/Django-4.2.7-green)
![Python](https://img.shields.io/badge/Python-3.9-blue)
![LangChain](https://img.shields.io/badge/LangChain-Agentic-red)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)
![Stripe](https://img.shields.io/badge/Stripe-API-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Table of Contents

1. [Overview](#overview)
2. [🤖 Agentic AI System (Core Feature)](#-agentic-ai-system-core-feature)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Setup Instructions](#setup-instructions)
6. [Database](#database)
7. [API Documentation](#api-documentation)
    - [Products](#products-api)
    - [Cart](#cart-api)
    - [Orders](#orders-api)
    - [Users](#users-api)
    - [Payments](#payments-api)
    - [Wishlist](#wishlist-api)
    - [Analytics](#analytics-api)
8. [Project Structure](#project-structure)
9. [Development Status](#development-status)
10. [Contributing](#contributing)
11. [License](#license)

---

## Overview

TechHub is a professional-grade e-commerce platform built with Django. What sets it apart is a **fully agentic AI assistant** that can autonomously perform multi-step operations — searching products, managing carts, placing orders, and answering questions — all through natural conversation. The platform also features a premium dark-themed UI with glassmorphism, Stripe payment processing, and real-time analytics.

### Project Objectives

- **Agentic AI Commerce**: LLM-driven chatbot that autonomously performs e-commerce operations via tool calling
- **Complete E-commerce Solution**: Full-featured online store with all essential functionalities
- **Premium UI/UX**: Dark theme with glassmorphism, gradient accents, and micro-animations
- **Security First**: Secure authentication, user-scoped AI operations, and encrypted payments
- **Analytics Integration**: Google Analytics, Facebook Pixel, and Twitter Pixel
- **SEO Optimized**: Search engine friendly with proper meta tags and structure

### Key Achievements

- ✅ **Fully Agentic AI Chatbot** — LLM autonomously selects and chains tools using ReAct reasoning
- ✅ **12 Database Tools** — Cart, wishlist, orders, products, profile operations via natural language
- ✅ **RAG Knowledge Base** — FAISS vector store for store-specific Q&A
- ✅ **Premium Dark UI** — Glassmorphism, gradient accents, scroll-reveal animations
- ✅ **Secure Payment Processing** with Stripe integration
- ✅ **Comprehensive Analytics** and reporting dashboard
- ✅ **Responsive Design** optimized for all devices

---

## Agentic AI System (Core Feature)

The crown jewel of TechHub is its **fully agentic AI chatbot** — not a simple intent-matching bot, but a ReAct-based agent that autonomously reasons, selects tools, and chains multi-step operations to fulfill user requests.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER MESSAGE                                │
│                    "Find Samsung phones                             │
│                     and add the cheapest                            │
│                     to my cart"                                     │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DJANGO VIEW (chatbot/views.py)                   │
│  • Authenticates user (login_required)                             │
│  • Loads session chat history (last 10 turns)                      │
│  • Creates ChatbotAgent(user_id)                                   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CHATBOT AGENT (AI/agent.py)                      │
│                                                                     │
│  1. RAG Retrieval                                                  │
│     └─ FAISS vector search on speech.txt → context snippets        │
│                                                                     │
│  2. Prompt Assembly                                                │
│     └─ System prompt + RAG context + user_id + chat_history        │
│                                                                     │
│  3. ReAct Agent Loop (LangChain AgentExecutor)                     │
│     ┌──────────────────────────────────────────────┐               │
│     │  Thought → Action → Observation → Thought... │               │
│     │                                              │  max 6 iters  │
│     │  LLM: Groq / llama-3.3-70b-versatile        │               │
│     │  Temperature: 0.3 (deterministic)            │               │
│     └──────────────────────────────────────────────┘               │
│                                                                     │
│  4. Retry & Resilience                                             │
│     └─ Exponential backoff for 429 rate limits (15s/30s)           │
│     └─ Auto-retry on tool-call validation errors                   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   12 DATABASE TOOLS (AI/tools.py)                   │
│                                                                     │
│  All tools return JSON. All user-scoped operations require user_id │
│                                                                     │
│  📦 Product Tools          🛒 Cart Tools                           │
│   • search_products         • get_user_cart                        │
│   • get_product_details     • add_to_cart                          │
│                              • remove_from_cart                     │
│  📋 Order Tools              • update_cart_item_quantity            │
│   • get_user_orders                                                │
│   • place_order             ❤️ Wishlist Tools                      │
│                              • get_user_wishlist                    │
│  👤 User Tools               • add_to_wishlist                     │
│   • get_user_profile         • remove_from_wishlist                │
└─────────────────────────────────────────────────────────────────────┘
```

### How the Agent Works

**1. ReAct Reasoning Loop**

The agent uses LangChain's `create_tool_calling_agent` + `AgentExecutor` to implement a ReAct (Reason + Act) loop. For a request like *"find Samsung phones and add the cheapest to my cart"*, the agent:

| Step | Thought | Action | Observation |
|------|---------|--------|-------------|
| 1 | User wants Samsung phones | `search_products(query="samsung phone")` | Returns 3 products with IDs and prices |
| 2 | Galaxy A15 is cheapest at $299 | `add_to_cart(user_id=5, product_id=8)` | Successfully added |
| 3 | Task complete | Return final answer | *"I found 3 Samsung phones. The cheapest is the Galaxy A15 at $299, and I've added it to your cart!"* |

The LLM autonomously decides which tools to call, in what order, and how to interpret results — no hardcoded intent routing.

**2. RAG (Retrieval Augmented Generation)**

| Component | Detail |
|-----------|--------|
| **Knowledge Base** | `AI/speech.txt` — TechHub company info, policies, FAQs |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) |
| **Vector Store** | FAISS — Facebook AI Similarity Search |
| **Chunking** | `RecursiveCharacterTextSplitter` (1000 chars, 200 overlap) |
| **Retrieval** | Top-3 relevant chunks injected into system prompt |

When a user asks *"What is TechHub's return policy?"*, the RAG pipeline retrieves relevant chunks from the knowledge base and injects them into the system prompt — no tool call needed.

**3. Conversational Memory**

Chat history is stored in the Django session (last 10 turns) and passed to the agent as `MessagesPlaceholder("chat_history")`. This enables multi-turn conversations:

```
User: "Show me laptops"
Bot:  [calls search_products] → "Here are 3 laptops: Dell XPS 13 ($1299), MacBook Pro ($1999)..."
User: "Add the first one to my cart"
Bot:  [calls add_to_cart(product_id=2)] → "Done! Dell XPS 13 added to your cart."
```

**4. Resilience & Error Handling**

- **Rate Limit Backoff**: Groq's free tier has rate limits. The agent retries with exponential backoff (15s, 30s) on HTTP 429 errors.
- **Tool Validation Recovery**: If the LLM generates malformed tool arguments, the agent retries up to 2 times with a corrective error message.
- **Graceful Degradation**: On unrecoverable errors, returns a user-friendly message instead of a stack trace.

**5. Security Model**

- **Authentication Gate**: Chatbot widget only renders for `{% if user.is_authenticated %}`
- **User Scoping**: Every tool receives `user_id` from the authenticated session — users can only access their own data
- **CSRF Protection**: All API calls go through Django's CSRF middleware
- **Session Isolation**: Chat history is per-user, stored in Django's session backend

### All 12 Agent Tools

| # | Tool | Args | Description |
|---|------|------|-------------|
| 1 | `search_products` | `query: str` | Full-text search across product names, descriptions, and categories. Returns up to 10 results sorted by availability. |
| 2 | `get_product_details` | `product_id: int` | Retrieves full product info including price, stock, specs, SKU, and discount status. |
| 3 | `get_user_cart` | `user_id: int` | Returns all cart items with product names, quantities, prices, and cart total. |
| 4 | `add_to_cart` | `user_id, product_id, quantity` | Adds a product to the user's cart. Checks stock availability. Increments quantity if already in cart. |
| 5 | `remove_from_cart` | `user_id, product_id` | Removes a specific product from the user's cart. |
| 6 | `update_cart_item_quantity` | `user_id, product_id, quantity` | Updates the quantity of an existing cart item. Validates against stock levels. |
| 7 | `get_user_wishlist` | `user_id: int` | Returns all wishlist items with product details and timestamps. |
| 8 | `add_to_wishlist` | `user_id, product_id` | Adds a product to the user's wishlist. Prevents duplicates. |
| 9 | `remove_from_wishlist` | `user_id, product_id` | Removes a product from the user's wishlist. |
| 10 | `get_user_orders` | `user_id: int` | Returns all orders with order numbers, statuses, amounts, and item counts. |
| 11 | `place_order` | `user_id: int` | Converts all cart items into a new order, generates an order number, and clears the cart. |
| 12 | `get_user_profile` | `user_id: int` | Returns username, email, join date, and total order count. |

### File Structure — AI Module

```
AI/
├── agent.py              # ReAct agent: prompt, AgentExecutor, retry logic
├── tools.py              # 12 @tool-decorated Django ORM database tools
├── config.py             # Dataclass configs: LLMConfig, RAGConfig, ChatbotConfig
├── speech.txt            # RAG knowledge base (company info, policies)
└── services/
    └── rag_service.py    # FAISS vector store init, document retrieval
```

### Example Conversations

```
User: "Hello! Good morning"
Bot:  "Good morning! 👋 Welcome to TechHub. How can I help you today?"
      (No tools called — greeting detected by system prompt)

User: "Search for headphones under $300"
Bot:  [calls search_products(query="headphones")] → filters results
      "I found 2 headphones: AirPods Pro 3 ($225) and Sony WH-1000XM5 ($279)."

User: "Add the AirPods to my cart and show me my wishlist"
Bot:  [calls add_to_cart(user_id=5, product_id=1, quantity=1)]
      [calls get_user_wishlist(user_id=5)]
      "Done! AirPods Pro 3 added to your cart. Your wishlist has 2 items: ..."

User: "Place my order"
Bot:  [calls place_order(user_id=5)]
      "Order placed! 🎉 Your order number is A3B8D1B60B3B. Total: $225.00."
```

---

## Features

### Core E-commerce Features

#### Product Management
- **Product Catalog**: Complete product listing with categories and search
- **Advanced Search**: Filter by category, price, availability, and keywords
- **Product Details**: Comprehensive product information with image galleries
- **Stock Management**: Real-time inventory tracking and availability status
- **Category System**: Organized product categorization with custom descriptions
- **SKU Management**: Automatic SKU generation and tracking

#### Shopping Experience
- **Shopping Cart**: Dynamic cart management with session persistence
- **Wishlist**: Personal product wishlists for registered users
- **Product Reviews**: User-generated ratings and comments system
- **Featured Products**: Highlighted products for promotional purposes
- **Product Images**: Multiple image support with primary image selection

#### Order Processing
- **Checkout Workflow**: Multi-step order completion process
- **Order Management**: Complete order tracking and history
- **Order Confirmation**: Email notifications and order status updates
- **Shipping Information**: Address management and delivery tracking
- **Order Status**: Real-time status updates and tracking

### User Management

#### Authentication System
- **User Registration**: Secure account creation with validation
- **Login/Logout**: Session-based authentication system
- **Profile Management**: User profile customization and preferences
- **Password Security**: Django's built-in password hashing and validation
- **Session Management**: Secure session handling with expiration

#### User Roles & Permissions
- **Anonymous Users**: Browse products and view categories
- **Registered Users**: Full shopping experience with wishlists + AI chatbot access
- **Admin Users**: Complete system management and analytics access

### Payment System

#### Stripe Integration
- **Secure Payments**: PCI-compliant payment processing
- **Multiple Payment Methods**: Credit cards, debit cards support
- **Payment Security**: Encrypted payment data transmission
- **Transaction Tracking**: Complete payment history and status
- **Webhook Handling**: Real-time payment status updates

### Analytics & Reporting

- **Sales Metrics**: Revenue tracking and financial reporting
- **Order Analytics**: Order volume and status analysis
- **Product Performance**: Best-selling products and category statistics
- **Google Analytics 4 / Facebook Pixel / Twitter Pixel**: Third-party tracking

### Premium UI/UX

- **Dark Theme**: Deep navy background with glassmorphism cards and backdrop-blur
- **Gradient Accents**: Electric indigo (#6C63FF) → mint (#00D4AA) gradient system
- **Micro-Animations**: Scroll-reveal (IntersectionObserver), hover glow, card lift, image zoom
- **Typography**: Inter font family (Google Fonts) with weight hierarchy
- **Custom Scrollbar**: Themed scrollbar matching the dark palette
- **Responsive**: Mobile-first with breakpoint optimizations
- **AI Chat Widget**: Dark-themed floating chatbot with matching gradient header

### SEO & Marketing

- **Meta Tags**: Dynamic title, description, and keywords
- **Open Graph / Twitter Cards**: Social media sharing optimization
- **Structured Data**: Product schema markup for search engines
- **Clean URLs**: SEO-friendly slug-based URL structure

---

## Tech Stack

### Backend Framework
- **Django 4.2.7**: High-level Python web framework
- **Python 3.9**: Modern Python programming language
- **SQLite3**: Lightweight database for development
- **Django ORM**: Object-relational mapping system
- **Celery & Redis**: Background asynchronous task queues

### Frontend Technologies
- **HTML5 / CSS3 / JavaScript**: Core web technologies
- **Bootstrap 5.3**: Responsive CSS framework (dark mode via `data-bs-theme`)
- **Inter (Google Fonts)**: Modern sans-serif typography
- **Font Awesome 6**: Icon library
- **Custom CSS**: 880+ lines — glassmorphism, gradients, scroll-reveal animations

### AI & Agentic System
- **LangChain**: Framework for building agentic LLM applications
- **Groq API**: Ultra-fast LLM inference (Llama 3.3 70B Versatile)
- **FAISS**: Facebook AI Similarity Search — vector database for RAG
- **HuggingFace Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` for text embeddings
- **ReAct Pattern**: Reason + Act loop via `AgentExecutor` + `create_tool_calling_agent`

### Payment & External Services
- **Stripe API**: Payment processing gateway
- **Google Analytics 4**: Website analytics
- **Facebook Pixel / Twitter Pixel**: Conversion tracking

### Development Tools
- **Virtual Environment**: Isolated Python environment
- **Git**: Version control system
- **Django Admin**: Built-in administration interface
- **Crispy Forms**: Enhanced form rendering

---

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- pip (Python package installer)
- Git (for version control)

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/techhub-ecommerce.git
   cd techhub-ecommerce
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install & Start Redis (Required for Celery)**
   ```bash
   # On macOS
   brew install redis
   brew services start redis
   
   # On Ubuntu/Debian
   sudo apt install redis-server
   sudo systemctl start redis
   ```

5. **Environment Configuration**
   ```bash
   # Create .env file in the project root
   touch .env
   
   # Edit .env file with your configuration
   nano .env
   ```
   
   Add the following to your `.env` file:
   ```env
   # GROQ API Key for Chatbot
   GROQ_API_KEY=your_groq_api_key_here
   
   # Django Secret Key (for production)
   SECRET_KEY=your-secret-key-here
   ```
   
   **Getting GROQ API Key:**
   - Visit https://console.groq.com/
   - Sign up or log in
   - Navigate to API Keys section
   - Create a new API key
   - Copy and paste it into your `.env` file

6. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

9. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

10. **Run Celery Worker (In a separate terminal)**
    ```bash
    source venv/bin/activate
    celery -A techhub worker --loglevel=info
    ```

11. **Access the Application**
    - Website: http://127.0.0.1:8000/
    - Admin Panel: http://127.0.0.1:8000/admin/

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Analytics
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
FACEBOOK_PIXEL_ID=123456789012345
TWITTER_PIXEL_ID=o1234

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## Database

TechHub E-commerce utilizes **SQLite3** for development and can be configured to use **PostgreSQL** or **MySQL** for production. The database includes comprehensive models for products, orders, payments, users, and analytics.

Run `python manage.py migrate` to set up the necessary tables for all models.

### Core Models
- **User**: Django built-in user model with profiles
- **Category**: Product categories with descriptions
- **Product**: Products with SKU, pricing, stock management
- **ProductImage**: Multiple product images with primary selection
- **ProductReview**: User reviews and ratings
- **Order**: Order management with status tracking
- **OrderItem**: Individual items within orders
- **Payment**: Payment processing with Stripe integration
- **Wishlist**: User wishlist functionality
- **CartItem**: Shopping cart items

---

## API Documentation

### <a name="products-api"></a>Products API

#### Model Fields
- `name` (string, required) - Product name
- `slug` (string, required, unique) - URL-friendly identifier
- `sku` (string, unique) - Stock Keeping Unit
- `category` (foreign key, required) - Product category
- `description` (text) - Product description
- `price` (decimal, required) - Product price
- `discount_price` (decimal, optional) - Discounted price
- `stock_quantity` (integer, default: 0) - Available stock
- `availability` (choices) - In stock, out of stock, pre-order
- `featured` (boolean, default: false) - Featured product flag
- `specifications` (text, optional) - Technical specifications

#### Endpoints
- **GET `/products/`** — List all products (supports filtering and pagination)
- **GET `/product/<slug>/`** — Retrieve product details by slug
- **GET `/category/<slug>/`** — List products in specific category
- **GET `/search/`** — Search products by name or description
- **GET `/`** — Homepage with featured products

**Filterable fields:**
- `category`, `availability`, `featured`, `min_price`, `max_price`, `search`

**Sorting options:**
- `name`, `price`, `created_at`, `rating`

#### Example Requests
```bash
# List all products
curl http://127.0.0.1:8000/products/

# Filter by category
curl "http://127.0.0.1:8000/products/?category=electronics"

# Search products
curl "http://127.0.0.1:8000/search/?q=smartphone"

# Get product details
curl http://127.0.0.1:8000/product/smartphone-x/

# Get category products
curl http://127.0.0.1:8000/category/electronics/
```

---

### <a name="cart-api"></a>Cart API

#### Model Fields
- `user` (foreign key, optional) - Associated user
- `session_key` (string, optional) - Session identifier
- `created_at` (datetime, auto-set) - Cart creation time
- `updated_at` (datetime, auto-set) - Last update time

#### Endpoints
- **GET `/cart/`** — Display shopping cart contents
- **POST `/cart/add/<product_id>/`** — Add product to cart
- **POST `/cart/remove/<item_id>/`** — Remove item from cart
- **POST `/cart/update/<item_id>/`** — Update item quantity
- **POST `/cart/clear/`** — Clear entire cart

#### Example Requests
```bash
# View cart
curl http://127.0.0.1:8000/cart/

# Add product to cart
curl -X POST http://127.0.0.1:8000/cart/add/1/ \
  -H "Content-Type: application/json" \
  -d '{"quantity": 2}'

# Remove item from cart
curl -X POST http://127.0.0.1:8000/cart/remove/1/

# Update item quantity
curl -X POST http://127.0.0.1:8000/cart/update/1/ \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3}'
```

---

### <a name="orders-api"></a>Orders API

#### Model Fields
- `order_number` (string, required, unique) - Unique order identifier
- `user` (foreign key, required) - Order owner
- `total_amount` (decimal, required) - Order total
- `status` (choices) - Pending, paid, shipped, delivered, cancelled
- `shipping_address` (text, required) - Delivery address
- `billing_address` (text, required) - Billing address
- `created_at` (datetime, auto-set) - Order creation time
- `updated_at` (datetime, auto-set) - Last update time

#### Endpoints
- **GET `/orders/checkout/`** — Checkout page (authentication required)
- **POST `/orders/checkout/`** — Process checkout and create order
- **GET `/orders/order/<order_number>/confirm/`** — Order confirmation page
- **GET `/orders/order/<order_number>/`** — Order details
- **GET `/orders/history/`** — User order history

#### Example Requests
```bash
# Access checkout (requires login)
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/orders/checkout/

# Process checkout
curl -X POST http://127.0.0.1:8000/orders/checkout/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": "123 Main St, City, Country",
    "billing_address": "123 Main St, City, Country"
  }'

# View order details
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/orders/order/ORD-12345/

# View order history
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/orders/history/
```

---

### <a name="users-api"></a>Users API

#### Model Fields
- `username` (string, required, unique) - Username
- `email` (string, required, unique) - Email address
- `first_name` (string, optional) - First name
- `last_name` (string, optional) - Last name
- `is_active` (boolean, default: true) - Account status
- `date_joined` (datetime, auto-set) - Registration date
- `last_login` (datetime, auto-set) - Last login time

#### Endpoints
- **GET `/accounts/register/`** — User registration page
- **POST `/accounts/register/`** — Process user registration
- **GET `/accounts/login/`** — User login page
- **POST `/accounts/login/`** — Process user login
- **GET `/accounts/profile/`** — User profile (authentication required)
- **GET `/accounts/logout/`** — User logout

#### Example Requests
```bash
# User registration
curl -X POST http://127.0.0.1:8000/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password1": "securepassword123",
    "password2": "securepassword123"
  }'

# User login
curl -X POST http://127.0.0.1:8000/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "securepassword123"
  }'

# View profile (requires authentication)
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/accounts/profile/
```

---

### <a name="payments-api"></a>Payments API

#### Model Fields
- `order` (foreign key, required) - Associated order
- `user` (foreign key, required) - Payment owner
- `amount` (decimal, required) - Payment amount
- `currency` (string, default: USD) - Payment currency
- `payment_method` (choices) - Stripe, PayPal, Cash on Delivery
- `status` (choices) - Pending, processing, completed, failed, cancelled
- `stripe_payment_intent_id` (string, optional) - Stripe payment intent
- `transaction_id` (string, optional) - Transaction identifier
- `created_at` (datetime, auto-set) - Payment creation time

#### Endpoints
- **GET `/payments/payment/<order_id>/`** — Payment page (authentication required)
- **GET `/payments/payment/<order_id>/success/`** — Payment success redirect
- **GET `/payments/payment/<order_id>/cancel/`** — Payment cancel redirect
- **POST `/payments/webhook/stripe/`** — Stripe webhook handler
- **GET `/payments/history/`** — Payment history (authentication required)

#### Example Requests
```bash
# Access payment page (requires authentication)
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/payments/payment/1/

# View payment history (requires authentication)
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/payments/history/

# Stripe webhook (no authentication required)
curl -X POST http://127.0.0.1:8000/payments/webhook/stripe/ \
  -H "Content-Type: application/json" \
  -d '{"type": "payment_intent.succeeded", "data": {...}}'
```

---

### <a name="wishlist-api"></a>Wishlist API

#### Model Fields
- `user` (foreign key, required) - Wishlist owner
- `product` (foreign key, required) - Wishlisted product
- `created_at` (datetime, auto-set) - Wishlist addition time

#### Endpoints
- **GET `/wishlist/`** — User wishlist (authentication required)
- **POST `/wishlist/add/<product_id>/`** — Add product to wishlist
- **POST `/wishlist/remove/<item_id>/`** — Remove item from wishlist

#### Example Requests
```bash
# View wishlist (requires authentication)
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/wishlist/

# Add to wishlist
curl -X POST http://127.0.0.1:8000/wishlist/add/1/ \
  -H "Authorization: Bearer <token>"

# Remove from wishlist
curl -X POST http://127.0.0.1:8000/wishlist/remove/1/ \
  -H "Authorization: Bearer <token>"
```

---

### <a name="analytics-api"></a>Analytics API

#### Endpoints
- **GET `/analytics/`** — Analytics dashboard (admin only)

#### Features
- **Sales Metrics**: Total revenue, order counts, payment statistics
- **Product Analytics**: Best-selling products, category performance
- **User Insights**: Customer behavior, order patterns
- **Performance Tracking**: System performance and user engagement

---

## Project Structure

```
techhub-ecommerce/
├── 📁 techhub/                    # Main project configuration
│   ├── __init__.py               # Python package initialization
│   ├── settings.py               # Django settings configuration
│   ├── urls.py                   # Main URL routing
│   ├── wsgi.py                   # WSGI application entry point
│   ├── asgi.py                   # ASGI application entry point
│   └── context_processors.py     # Custom context processors
│
├── 📁 products/                   # Product management application
│   ├── models.py                 # Product, Category, ProductImage models
│   ├── views.py                  # Product views and logic
│   ├── urls.py                   # Product URL patterns
│   ├── admin.py                  # Django admin configuration
│   ├── forms.py                  # Product forms
│   └── templatetags/             # Custom template tags
│
├── 📁 cart/                       # Shopping cart functionality
│   ├── models.py                 # Cart models
│   ├── views.py                  # Cart views
│   ├── urls.py                   # Cart URL patterns
│   └── context_processors.py     # Cart context processor
│
├── 📁 orders/                     # Order processing application
│   ├── models.py                 # Order and OrderItem models
│   ├── views.py                  # Order views
│   ├── urls.py                   # Order URL patterns
│   └── admin.py                  # Order admin configuration
│
├── 📁 users/                      # User authentication application
│   ├── models.py                 # User profile models
│   ├── views.py                  # Authentication views
│   ├── urls.py                   # User URL patterns
│   ├── forms.py                  # User forms
│   └── admin.py                  # User admin configuration
│
├── 📁 wishlist/                   # Wishlist functionality
│   ├── models.py                 # Wishlist models
│   ├── views.py                  # Wishlist views
│   ├── urls.py                   # Wishlist URL patterns
│   └── admin.py                  # Wishlist admin configuration
│
├── 📁 payment_processing/         # Payment integration
│   ├── models.py                 # Payment models
│   ├── views.py                  # Payment views
│   ├── urls.py                   # Payment URL patterns
│   └── admin.py                  # Payment admin configuration
│
├── 📁 chatbot/                    # AI Chatbot application
│   ├── views.py                  # Chatbot API views
│   ├── urls.py                   # Chatbot URL patterns
│   └── apps.py                   # Chatbot app configuration
│
├── 📁 AI/                         # Agentic AI System
│   ├── agent.py                  # ReAct agent: ChatbotAgent, AgentExecutor, retry logic
│   ├── tools.py                  # 12 @tool-decorated Django ORM database tools
│   ├── config.py                 # Dataclass configs: LLMConfig, RAGConfig, ChatbotConfig
│   ├── speech.txt                # RAG knowledge base (company info, policies)
│   └── services/
│       └── rag_service.py        # FAISS vector store init, document retrieval
│
├── 📁 templates/                  # HTML templates
│   ├── base.html                 # Base template with navigation
│   ├── products/                 # Product-related templates
│   ├── cart/                     # Shopping cart templates
│   ├── orders/                   # Order processing templates
│   ├── users/                    # User authentication templates
│   ├── wishlist/                 # Wishlist templates
│   ├── payment_processing/       # Payment templates
│   └── chatbot/                  # Chatbot widget template
│
├── 📁 static/                     # Static files (CSS, JS, images)
│   ├── css/                      # Stylesheets
│   ├── js/                       # JavaScript files
│   └── images/                   # Static images
│
├── 📁 media/                      # User uploaded files
│   ├── products/                 # Product images
│   ├── categories/               # Category images
│   └── users/                    # User profile images
│
├── 📁 venv/                       # Virtual environment
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── requirements_diagrams.txt      # Diagram generation dependencies
├── generate_diagrams.py           # Diagram generation script
├── LAB_REPORT.md                  # Comprehensive lab report
└── README.md                      # This file
```

---

## Development Status

### ✅ Completed Features
- **Fully Agentic AI Chatbot**: ReAct agent with 12 tools, RAG, retry logic
- **Premium Dark UI**: Glassmorphism, gradient accents, micro-animations
- **Core E-commerce Platform**: Product management, shopping cart, orders
- **User Authentication**: Registration, login, profiles, wishlists
- **Payment Integration**: Stripe payment processing with webhooks
- **Analytics Dashboard**: Sales metrics, order analytics, reporting
- **SEO Optimization**: Meta tags, Open Graph, Twitter Cards
- **Responsive Design**: Bootstrap 5.3 dark mode with mobile-first approach

### 🚧 In Progress
- **Advanced Analytics**: Enhanced reporting and insights
- **Performance Optimization**: Caching and query optimization
- **Testing Coverage**: Comprehensive test suite development

### 📋 Planned Features
- **Multi-language Support**: Internationalization (i18n)
- **Advanced Search**: Elasticsearch integration
- **Mobile App**: Native mobile application
- **AI Integration**: Product recommendations
- **Marketing Tools**: Email campaigns and automation

---

## Contributing

### Contribution Guidelines

1. **Fork the Repository**
2. **Create a Feature Branch**
3. **Make Your Changes**
4. **Add Tests**
5. **Submit a Pull Request**

### Development Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/techhub-ecommerce.git
cd techhub-ecommerce

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### Code Style

- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write comprehensive tests
- Update documentation

---

## Documentation

### Additional Resources

- **Lab Report**: `LAB_REPORT.md` - Comprehensive laboratory work documentation
- **Diagram Generation**: `generate_diagrams.py` - Creates ER diagrams, DFD, Gantt charts
- **Requirements**: `requirements.txt` - Python dependencies

### Generate Diagrams

The project includes a diagram generation script:

```bash
# Install diagram dependencies
pip install -r requirements_diagrams.txt

# Generate all diagrams
python generate_diagrams.py
```

This creates:
- **ER_Diagram.jpeg**: Database entity relationship diagram
- **DFD.jpeg**: Data flow diagram
- **Gantt_Chart.jpeg**: Project timeline chart
- **System_Architecture.jpeg**: System architecture diagram

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Django Community**: For the excellent web framework
- **Stripe**: For secure payment processing
- **Bootstrap Team**: For responsive CSS framework
- **Open Source Contributors**: For various libraries and tools

---

## 📞 Support

### Getting Help

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions
- **Documentation**: Check comprehensive documentation
- **Email**: Contact project maintainers

### Community

- **GitHub**: [Project Repository](https://github.com/yourusername/techhub-ecommerce)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/techhub-ecommerce/discussions)
- **Wiki**: [Project Wiki](https://github.com/yourusername/techhub-ecommerce/wiki)

---

**Star this repository if you find it helpful!**

** Share with your network to help others discover this project!**

** We welcome your feedback and contributions!**


