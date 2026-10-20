# 🍗 निशु चिकन कॉर्नर — AI Order Management System

> An intelligent restaurant order management prototype powered by **LangGraph-style workflows**, **Groq LLM**, and a premium dark-themed web UI.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq%20Mixtral%208x7B-orange?logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Running the App](#-running-the-app)
- [How It Works](#-how-it-works)
- [Menu](#-menu)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration)
- [Test Scenarios](#-test-scenarios)
- [Future Improvements](#-future-improvements)

---

## 🌟 Overview

This project is an **AI-powered restaurant order management system** built for **निशु चिकन कॉर्नर** (Nishu Chicken Corner). Users place orders in natural language (e.g., *"I want 2 Butter Chicken"*), and the system:

1. Uses **Groq's free Mixtral-8x7B LLM** to parse the order.
2. Checks availability against a **menu extracted from the restaurant's PDF**.
3. Simulates a full **cook → serve** pipeline with probabilistic success/failure.
4. Enforces **retry limits** at every stage (order, cook, serve).
5. Returns a structured, color-coded result in a **premium web UI**.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **LLM Order Parsing** | Extracts dish name & quantity from free-form text using Groq API |
| 📄 **PDF Menu Extraction** | Automatically reads the menu from `निशु चिकन कॉर्नर.pdf` using `pdfplumber` |
| 🔍 **Fuzzy Dish Matching** | Case-insensitive + substring matching so "chowmein" finds "Chowmein" |
| 🔄 **Retry Logic** | Order retries (3), Cook retries (2), Serve retries (2) — all tracked in state |
| 🎲 **Probabilistic Simulation** | 60% success / 40% failure for cooking and serving stages |
| 🚫 **Non-Food Filtering** | Rejects requests unrelated to food ordering |
| 🎨 **Premium Dark UI** | Glassmorphism cards, animated blobs, categorized menu, color-coded responses |
| 🛡️ **Graceful Fallback** | If the LLM API fails, a regex-based parser takes over seamlessly |

---

## 🏗 Architecture

The system follows a **LangGraph-inspired state machine** workflow:

```
┌─────────────┐
│  User Input  │
└──────┬──────┘
       │
       ▼
┌──────────────┐     ┌──────────────────┐
│  LLM Parser  │────▶│  Regex Fallback  │  (if API fails)
│  (Groq API)  │     └──────────────────┘
└──────┬───────┘
       │  { dish_name, quantity, is_food }
       ▼
┌──────────────────┐
│  Order Confirm   │  ← Checks menu availability
│  (Fuzzy Match)   │
└──────┬───────────┘
       │
       ├── confirmed ──────────────────────────────┐
       │                                           ▼
       ├── partial ──▶ Prompt user to retry   ┌─────────┐
       │               (order_retry -= 1)     │  Cook   │
       │                                      │ (60/40) │
       └── unavailable ▶ Prompt user / End    └────┬────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    │ success      │ failure      │
                                    ▼              ▼              │
                              ┌──────────┐   cook_retry -= 1     │
                              │  Serve   │   (retry or end)      │
                              │ (60/40)  │                       │
                              └────┬─────┘                       │
                                   │                             │
                    ┌──────────────┼──────────────┐              │
                    │ success      │ failure      │              │
                    ▼              ▼              │              │
              ┌──────────┐  serve_retry -= 1     │              │
              │ COMPLETE │  (retry cook or end)  │              │
              │  🎉      │                       │              │
              └──────────┘                       │              │
                                                 ▼              ▼
                                           ┌───────────────────────┐
                                           │  APOLOGY & END 😞    │
                                           └───────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11 | Core runtime |
| **Web Framework** | FastAPI + Uvicorn | Async HTTP server |
| **LLM** | Groq API (Mixtral 8x7B 32768) | Natural language order parsing |
| **PDF Parsing** | pdfplumber | Extract menu from restaurant PDF |
| **State Management** | Pydantic `BaseModel` | LangGraph-style `OrderState` |
| **HTTP Client** | httpx | Async calls to Groq API |
| **Templating** | Jinja2 | Server-side HTML rendering |
| **Styling** | Vanilla CSS | Premium dark-themed UI |
| **Package Manager** | uv | Fast dependency resolution |
| **Env Management** | python-dotenv | Load API keys from `.env` |

---

## 📁 Project Structure

```
restaurantagent/
├── .env                        # API keys (GROQ_API_KEY)
├── .gitignore                  # Git ignore rules
├── .python-version             # Python version pin (3.11)
├── pyproject.toml              # Project metadata & dependencies
├── uv.lock                     # Locked dependency versions
├── app.py                      # 🧠 Main application (FastAPI + workflow logic)
├── main.py                     # Original placeholder (unused)
├── prompt.md                   # Design specification document
├── README.md                   # 📖 This file
├── निशु चिकन कॉर्नर.pdf       # 📄 Restaurant menu PDF (source of truth)
├── static/
│   └── style.css               # 🎨 Premium dark-themed stylesheet
└── templates/
    └── index.html              # 🖥️ Jinja2 UI template
```

---

## ⚙️ Setup & Installation

### Prerequisites

- **Python 3.11+**
- **uv** package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Groq API key** (free at [console.groq.com](https://console.groq.com))

### Step-by-step

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd restaurantagent

# 2. Create and activate a virtual environment (uv does this automatically)
uv venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# 3. Install all dependencies
uv pip install -e .

# 4. Set up your environment variables
# Create a .env file in the project root with:
echo GROQ_API_KEY=your_groq_api_key_here > .env
```

---

## 🚀 Running the App

```bash
uv run uvicorn app:app --reload
```

Open your browser at **http://127.0.0.1:8000** 🎉

You'll see:
- 🍗 The restaurant header with branding & contact info
- 📋 The full menu organized into **Main Dishes**, **Crunchy Snacks**, and **Essentials**
- 🛒 An order input textarea
- 📦 A structured, color-coded order result card after submission

---

## 🔧 How It Works

### 1. LLM Order Parsing

When a user submits an order, the text is sent to **Groq's Mixtral-8x7B** model with a system prompt that instructs it to extract:

```json
{
    "dish_name": "Butter Chicken",
    "quantity": 2,
    "is_food": true
}
```

If `is_food` is `false`, the system rejects the request immediately.

### 2. Order Confirmation

The `confirm_order` node checks the extracted dish against the menu using **fuzzy matching**:
- **Exact match** → `"Chowmein"` == `"Chowmein"` ✅
- **Case-insensitive** → `"chowmein"` matches `"Chowmein"` ✅
- **Substring** → `"butter"` matches `"Butter Chicken"` ✅

Then sets the status:

| Condition | Status |
|-----------|--------|
| Dish found, enough quantity | `confirmed` |
| Dish found, partial quantity | `partial` |
| Dish not found or qty = 0 | `unavailable` |

### 3. Cook & Serve Simulation

Both stages use a **random probability function**:
- **60% chance of success** → proceed to next stage
- **40% chance of failure** → decrement retry counter

### 4. Retry Logic

| Stage | Max Retries | On Exhaustion |
|-------|-------------|---------------|
| **Order** | 3 | System ends with apology |
| **Cook** | 2 | System ends with apology |
| **Serve** | 2 | Retries cook (if cook retries remain), else apology |

All counters are stored in the `OrderState` and decremented on each failure.

### 5. State Model

```python
class OrderState(BaseModel):
    dish_name: str = ""          # Extracted dish name
    required_qty: int = 0        # Quantity requested by user
    available_qty: int = 0       # Quantity available in menu
    status: str = ""             # Current workflow status
    order_retry: int = 3         # Remaining order retries
    cook_retry: int = 2          # Remaining cook retries
    serve_retry: int = 2         # Remaining serve retries
    message: str = ""            # Final message to user
```

---

## 🍽 Menu

The menu is **automatically extracted** from `निशु चिकन कॉर्नर.pdf` on startup. Each dish has a default **available quantity of 3**.

### 🍛 Main Dishes

| Dish | Price (₹) |
|------|-----------|
| Tari Chicken | 500 |
| Half Tari Chicken | 280 |
| Chilli Chicken | 500 |
| Half Chilli Chicken | 280 |
| Butter Chicken | 500 |
| Half Butter Chicken | 280 |
| Lemon Chicken | 500 |
| Half Lemon Chicken | 280 |
| Punjabi Chicken | 500 |
| Half Punjabi Chicken | 280 |

### 🍿 Crunchy Snacks

| Dish | Price (₹) |
|------|-----------|
| Chicken Pakore | 500 |
| Half Chicken Pakore | 280 |
| Tari Palate | 100 |
| Half Tari Palate | 50 |
| Egg Bhurji | 100 |
| Pasta | 100 |
| Chowmein | 100 |
| Chana Chaat | 60 |

### 🫓 Essentials & Sides

| Dish | Price (₹) |
|------|-----------|
| Simple Roti | 10 |
| Missi Roti | 20 |
| Dahi | 30 |
| Dahi Raita | 60 |
| Salad | 50 |
| Half Salad | 30 |

---

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Renders the main UI with menu & order form |
| `POST` | `/process_order` | Processes an order (form field: `order_text`) |
| `GET` | `/api/menu` | Returns the full menu as JSON (debug endpoint) |

### Example: POST `/process_order`

**Request:**
```
Content-Type: application/x-www-form-urlencoded

order_text=I+would+like+2+Chowmein
```

**Response:**
```json
{
    "dish_name": "Chowmein",
    "required_qty": 2,
    "available_qty": 2,
    "status": "served",
    "order_retry": 3,
    "cook_retry": 2,
    "serve_retry": 2,
    "message": "Your Chowmein is ready! Enjoy your meal."
}
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Your Groq API key for LLM access |

### Tunable Constants (in `app.py`)

| Constant | Default | Description |
|----------|---------|-------------|
| `GROQ_MODEL` | `mixtral-8x7b-32768` | Groq model to use |
| `OrderState.order_retry` | `3` | Max order retries |
| `OrderState.cook_retry` | `2` | Max cook retries |
| `OrderState.serve_retry` | `2` | Max serve retries |
| Cook success probability | `0.6` (60%) | In `simulate_cook()` |
| Serve success probability | `0.6` (60%) | In `simulate_serve()` |
| Default available qty | `3` | In `load_menu_from_pdf()` |

---

## 🧪 Test Scenarios

Try these orders in the UI to verify different workflow paths:

| # | Input | Expected Outcome |
|---|-------|-----------------|
| 1 | `I want 2 Butter Chicken` | ✅ Order confirmed → cook → serve → success |
| 2 | `Give me 1 Chowmein` | ✅ Order confirmed → cook → serve → success |
| 3 | `5 Butter Chicken please` | ⚠️ Partial availability (only 3 available) |
| 4 | `1 Pizza` | ❌ Unavailable — not on the menu |
| 5 | `What is the weather?` | 🚫 Rejected — not a food order |
| 6 | `2 chowmein` | ✅ Fuzzy match works (lowercase) |
| 7 | `I want 1 butter` | ✅ Substring match finds "Butter Chicken" |

> **Note:** Since cook/serve use random probability (60/40), results may vary. Run the same order multiple times to see retry logic in action.

---

## 🔮 Future Improvements

- [ ] **Full LangGraph integration** — replace the manual workflow loop with actual LangGraph nodes & edges
- [ ] **Multi-item orders** — support ordering multiple dishes in one request
- [ ] **Order history** — persist orders in SQLite with timestamps
- [ ] **Real-time updates** — use WebSockets for live cook/serve status
- [ ] **Hindi language support** — parse orders written in Hindi
- [ ] **Dark/Light mode toggle** — CSS theme switcher
- [ ] **Automated test suite** — `pytest` + FastAPI `TestClient`
- [ ] **Docker support** — containerize the app for easy deployment
- [ ] **Admin panel** — update menu items and quantities from the UI

---

## 📜 License

This project is for educational purposes as part of an AI course.

---

<p align="center">
  Made with ❤️ for <strong>निशु चिकन कॉर्नर</strong> — Taste You'll Love 🔥
</p>
