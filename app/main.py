"""Aplicación FastAPI: una web pública de solo lectura y un admin con Basic Auth."""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from app import db, market, views

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
security = HTTPBasic()


def check_auth(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    import secrets

    user = os.getenv("ADMIN_USER", "admin")
    password = os.getenv("ADMIN_PASSWORD", "")
    valid = secrets.compare_digest(credentials.username, user) and secrets.compare_digest(credentials.password, password)
    if not valid:
        raise HTTPException(401, "No autorizado", headers={"WWW-Authenticate": "Basic"})


def create_app(conn: sqlite3.Connection | None = None, refresh_fn=None, scheduler: bool | None = None) -> FastAPI:
    if conn is None:
        db_path = Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "stocks.db")))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        db.init_db(conn)

    refresh = refresh_fn or (lambda c: market.refresh(c))

    if scheduler is None:
        scheduler = conn is None and os.getenv("ENABLE_SCHEDULER", "1") != "0"

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        task = None
        if scheduler:
            async def loop():
                interval = int(os.getenv("REFRESH_INTERVAL_SECONDS", "3600"))
                await asyncio.sleep(5)
                while True:
                    try:
                        await asyncio.to_thread(refresh, conn)
                    except Exception:
                        logging.exception("Fallo en la actualización programada")
                    await asyncio.sleep(interval)

            task = asyncio.create_task(loop())
        yield
        if task:
            task.cancel()

    def get_conn():
        return conn

    app = FastAPI(title="Stocks Dashboard", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.state.conn = conn

    @app.get("/healthz")
    @app.get("/health")
    def healthz():
        return {"status": "ok"}

    @app.get("/", response_class=FileResponse)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/admin", response_class=FileResponse)
    def admin(_=Depends(check_auth)):
        return FileResponse(STATIC_DIR / "admin.html")

    @app.get("/api/public/dashboard")
    def public_dashboard(c: sqlite3.Connection = Depends(get_conn)):
        return views.public_dashboard(c)

    @app.get("/api/admin/dashboard")
    def admin_dashboard(_=Depends(check_auth), c: sqlite3.Connection = Depends(get_conn)):
        return views.admin_dashboard(c)

    @app.post("/api/admin/assets")
    async def save_asset(payload: dict, _=Depends(check_auth), c: sqlite3.Connection = Depends(get_conn)):
        ticker = str(payload.get("ticker", "")).strip().lower()
        if not ticker:
            raise HTTPException(400, "Falta el ticker")
        db.upsert_asset(
            c,
            {
                "ticker": ticker,
                "name": str(payload.get("name", "")).strip(),
                "kind": payload.get("kind") if payload.get("kind") in ("stock", "etf") else "stock",
                "quantity": float(payload.get("quantity") or 0),
                "avg_buy": float(payload.get("avg_buy") or 0),
                "override_price": float(payload["override_price"]) if payload.get("override_price") not in (None, "") else None,
            },
        )
        return {"ok": True, "ticker": ticker}

    @app.delete("/api/admin/assets/{ticker}")
    def remove_asset(ticker: str, _=Depends(check_auth), c: sqlite3.Connection = Depends(get_conn)):
        db.delete_asset(c, ticker.lower())
        return {"ok": True}

    @app.post("/api/admin/refresh")
    def refresh_now(_=Depends(check_auth), c: sqlite3.Connection = Depends(get_conn)):
        result = refresh(c) or {}
        return {"ok": True, **result}

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
