# CS50 Finance (Flask)

A small Flask app that simulates buying and selling stocks with real-time quotes. Built as part of the course CS50 offerred by Prof. David J Malan of Harvard University(via EdX).

## Features
- Register/login with hashed passwords and session-backed auth
- Lookup live quotes via yfinance
- Buy/sell flows with cash balance updates and portfolio totals
- Transaction history with per-symbol PnL math
- Add funds and change password

## Stack
- Flask, Jinja, Flask-Session
- CS50 SQL wrapper over SQLite (local) or Postgres (e.g., Neon)
- yfinance for quotes

## Prerequisites
- Python 3.10+ and pip
- Optional: `python-dotenv` if you want `.env` auto-loading when running `flask run`

## Setup (local)
1) Create and activate a venv (Windows PowerShell):
```
python -m venv .venv
.\.venv\Scripts\activate
```
2) Install deps:
```
pip install -r requirements.txt
```
3) Environment variables (create `.env`):
```
DATABASE_URL=  # Leave empty for local SQLite; set to Postgres URL for Neon (add sslmode=require if missing)
SECRET_KEY=    # Any random string for session signing
```

## Database
- Local dev: falls back to `sqlite:///finance.db` when `DATABASE_URL` is empty.
- Postgres (Neon): set `DATABASE_URL` to your pooled connection string. If it lacks `sslmode`, the app appends `sslmode=require` automatically.

Run this schema on your Postgres/Neon database before using register/buy/sell:
```sql
CREATE TABLE IF NOT EXISTS users (
	id SERIAL PRIMARY KEY,
	username TEXT NOT NULL UNIQUE,
	hash TEXT NOT NULL,
	cash NUMERIC(12,2) NOT NULL DEFAULT 10000
);

CREATE TABLE IF NOT EXISTS transactions (
	id SERIAL PRIMARY KEY,
	user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	symbol TEXT NOT NULL,
	shares INTEGER NOT NULL,
	price NUMERIC(12,2) NOT NULL,
	transaction_type TEXT NOT NULL CHECK (transaction_type IN ('bought','sold')),
	timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Run
```
flask run
```
Ensure `FLASK_APP=app.py` if Flask cannot find the app.
