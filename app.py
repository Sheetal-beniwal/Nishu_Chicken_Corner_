import os
import random
import json
from pathlib import Path
from typing import Dict, Any

import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables (Groq API key)
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Use free Groq model (Mixtral 8x7b 32768)
GROQ_MODEL = "mixtral-8x7b-32768"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------------------
# Utility: load menu from the provided PDF (simple heuristic)
# ---------------------------------------------------------------------------
def load_menu_from_pdf(pdf_path: str) -> Dict[str, Dict[str, Any]]:
    """Extract the menu from the PDF.
    The PDF has two formats mixed together:
      1. English lines like 'Chowmein 100' (dish name + price on one line)
      2. Hindi lines where dish name and price are on alternating lines
    We parse the English section for a cleaner result. Default qty = 3.
    """
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber is required to extract the menu from PDF. Install it via pip.")
    import re

    menu: Dict[str, Dict[str, Any]] = {}
    # Section headers to skip
    skip_keywords = {
        "nishu hotel", "veg and non-veg", "taste", "main dishes",
        "crunchy snacks", "essentials", "cold drinks", "upto",
        "9466", "mrp",
    }
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Skip section headers / phone numbers
                if any(kw in line.lower() for kw in skip_keywords):
                    continue
                # Try to match "Dish Name <price>" where price is an integer at end
                m = re.match(r"^(.+?)\s+(\d+)$", line)
                if m:
                    dish = m.group(1).strip()
                    price = float(m.group(2))
                    # Skip lines that are just a bare number
                    if dish:
                        menu[dish] = {"price": price, "available_qty": 3}
    return menu

# Load menu on startup
MENU_PDF_PATH = Path(__file__).parent / "निशु चिकन कॉर्नर.pdf"
MENU = load_menu_from_pdf(str(MENU_PDF_PATH))
print("[DEBUG] Loaded MENU keys:", list(MENU.keys()))


def find_menu_match(dish_name: str) -> str | None:
    """Find the best matching key in MENU for the given dish name.
    Tries: exact match → case-insensitive match → substring match.
    Returns the actual MENU key or None.
    """
    # 1. Exact match
    if dish_name in MENU:
        return dish_name
    # 2. Case-insensitive match
    lower = dish_name.lower().strip()
    for key in MENU:
        if key.lower().strip() == lower:
            return key
    # 3. Substring / partial match (user typed part of the name)
    for key in MENU:
        if lower in key.lower() or key.lower() in lower:
            return key
    return None

# ---------------------------------------------------------------------------
# LangGraph‑style state (simplified for this prototype)
# ---------------------------------------------------------------------------
class OrderState(BaseModel):
    dish_name: str = ""
    required_qty: int = 0
    available_qty: int = 0
    status: str = ""
    order_retry: int = 3
    cook_retry: int = 2
    serve_retry: int = 2
    message: str = ""

# ---------------------------------------------------------------------------
# LLM helper – ask Groq to parse the raw user text
# ---------------------------------------------------------------------------
async def llm_parse_order(user_input: str) -> Dict[str, Any]:
    """Parse the user input.
    First tries the Groq LLM; if the request fails (e.g., missing API key or 400),
    falls back to a simple regex parser that extracts a dish name and quantity.
    Returns a dict with keys: `dish_name`, `quantity`, `is_food`.
    """
    system_prompt = (
        "You are a helpful assistant that extracts a restaurant order from free‑form text. "
        "If the text is not related to food ordering, set \"is_food\" to false. "
        "If it is a food order, return a JSON object with the dish name (string) and quantity (int). "
        "Only output the JSON, nothing else."
    )
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.0,
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"} if GROQ_API_KEY else {}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GROQ_ENDPOINT, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            try:
                order_info = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                order_info = json.loads(json_match.group()) if json_match else {}
            return order_info
    except Exception as exc:
        # Simple fallback parsing when the LLM call fails
        print(f"Groq request failed ({exc}), using regex fallback.")
        import re
        qty_match = re.search(r"(\d+)", user_input)
        quantity = int(qty_match.group(1)) if qty_match else 1
        # Remove quantity from the string to approximate dish name
        dish_name = re.sub(r"\d+", "", user_input).strip()
        is_food = bool(dish_name)
        return {"dish_name": dish_name, "quantity": quantity, "is_food": is_food}

# ---------------------------------------------------------------------------
# Core workflow functions
# ---------------------------------------------------------------------------
def confirm_order(state: OrderState) -> None:
    """Check availability against MENU and update state accordingly."""
    matched_key = find_menu_match(state.dish_name)
    print(f"[DEBUG] User dish='{state.dish_name}' → matched_key='{matched_key}'")
    if matched_key is None:
        state.available_qty = 0
        state.status = "unavailable"
        return
    # Normalise the dish name to the canonical menu key
    state.dish_name = matched_key
    available = MENU[matched_key]["available_qty"]
    state.available_qty = min(available, state.required_qty)
    if state.available_qty == state.required_qty:
        state.status = "confirmed"
    elif state.available_qty == 0:
        state.status = "unavailable"
    else:
        state.status = "partial"

def decide_next(state: OrderState) -> str:
    """Return the next node name based on current status."""
    if state.status == "confirmed":
        return "cook"
    # partial or unavailable – ask user if they want to retry
    if state.order_retry > 0:
        state.order_retry -= 1
        return "retry_order"
    return "end"

def simulate_cook(state: OrderState) -> None:
    """Randomly succeed/fail. Decrement retry counter on failure."""
    if random.random() < 0.6:  # 60% success
        state.status = "cooked"
    else:
        state.cook_retry -= 1
        if state.cook_retry <= 0:
            state.status = "cook_failed_final"
        else:
            state.status = "cook_failed_retry"

def simulate_serve(state: OrderState) -> None:
    """Randomly succeed/fail. Decrement retry counter on failure."""
    if random.random() < 0.6:
        state.status = "served"
    else:
        state.serve_retry -= 1
        if state.serve_retry <= 0:
            state.status = "serve_failed_final"
        else:
            state.status = "serve_failed_retry"

# ---------------------------------------------------------------------------
# FastAPI routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Render the UI with the menu information
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "menu": MENU,
        },
    )

@app.get("/api/menu")
async def api_menu():
    """Debug endpoint – returns the full menu dict so we can inspect keys."""
    return JSONResponse({k: v for k, v in MENU.items()})

@app.post("/process_order")
async def process_order(order_text: str = Form(...)):
    # Initialise state
    state = OrderState()
    # 1️⃣ Parse order via LLM
    order_info = await llm_parse_order(order_text)
    if not order_info.get("is_food", True):
        return JSONResponse({"message": "Sorry, I can only handle food orders."})
    state.dish_name = order_info.get("dish_name", "").strip()
    state.required_qty = int(order_info.get("quantity", 1))
    # 2️⃣ Confirm availability
    confirm_order(state)
    # 3️⃣ Decision loop (very simplified – we run a single pass for prototype)
    next_node = decide_next(state)
    while True:
        if next_node == "cook":
            simulate_cook(state)
            if state.status == "cooked":
                next_node = "serve"
                continue
            elif state.status == "cook_failed_final":
                state.message = "We are sorry, the kitchen could not prepare your dish after multiple attempts."
                break
            else:  # retry
                simulate_cook(state)
                continue
        if next_node == "serve":
            simulate_serve(state)
            if state.status == "served":
                state.message = f"Your {state.dish_name} is ready! Enjoy your meal."
                break
            elif state.status == "serve_failed_final":
                state.message = "We apologize, the serving failed after multiple attempts."
                break
            else:
                # retry serve
                simulate_serve(state)
                continue
        if next_node == "retry_order":
            # For the prototype we just return a message asking the user to retry manually.
            state.message = (
                f"Only {state.available_qty} of {state.dish_name} is available. "
                f"You have {state.order_retry} order attempts left. Please modify your order."
            )
            break
        if next_node == "end":
            state.message = "Unable to fulfill the order. Thank you for trying."
            break
        # safety net
        break
    return JSONResponse(state.dict())

# ---------------------------------------------------------------------------
# Run with: uvicorn app:app --reload
# ---------------------------------------------------------------------------
