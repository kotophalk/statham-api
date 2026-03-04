from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import random
import os

app = FastAPI(
    title="Statham Quotes API",
    description="API пацанских мемов-цитат Джейсона Стэтхэма",
    version="1.0.0"
)

# Разрешаем CORS (чтобы запросы проходили с любых сайтов/фронтендов)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Загрузка базы в память
DB_PATH = os.path.join(os.path.dirname(__file__), "statham_quotes.json") if '__file__' in globals() else "statham_quotes.json"
quotes_db = []

@app.on_event("startup")
def load_db():
    global quotes_db
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            quotes_db = json.load(f)
    except FileNotFoundError:
        print(f"Error: Database file not found at {DB_PATH}")
        quotes_db = []

@app.get("/")
def root():
    return {
        "status": "ok", 
        "message": "Welcome to the Statham Quotes API", 
        "docs": "/docs",
        "total_quotes": len(quotes_db)
    }

@app.get("/api/v1/quote/random")
def get_random_quote(count: int = Query(1, ge=1, le=50, description="Количество случайных цитат (от 1 до 50)")):
    """Возвращает одну или несколько случайных цитат."""
    if not quotes_db:
        raise HTTPException(status_code=500, detail="База данных пуста")
    
    count = min(count, len(quotes_db))
    if count == 1:
        return random.choice(quotes_db)
    return random.sample(quotes_db, count)

@app.get("/api/v1/quote/{quote_id}")
def get_quote_by_id(quote_id: int):
    """Возвращает конкретную цитату по её ID."""
    for quote in quotes_db:
        if quote.get("id") == quote_id:
            return quote
    raise HTTPException(status_code=404, detail="Цитата не найдена")

@app.get("/api/v1/quotes")
def get_all_quotes(
    limit: int = Query(50, ge=1, le=100, description="Лимит вывода (макс 100)"),
    offset: int = Query(0, ge=0, description="Смещение (для пагинации)")
):
    """Возвращает список цитат с пагинацией."""
    return {
        "total": len(quotes_db),
        "limit": limit,
        "offset": offset,
        "data": quotes_db[offset: offset + limit]
    }
