import os
import re
from typing import Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

# =========================
# ENV obligatorias (Render)
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

POSTGREST_URL = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""

# =========================
# FastAPI
# =========================
app = FastAPI(title="CCNUTRICIONAPP Prelogin")

class PreloginRequest(BaseModel):
    email: str

class PreloginResponse(BaseModel):
    eligible: bool
    reason: str  # ok | no_user | inactive_profile | invalid_email | server_error

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

async def fetch_profile_by_email(email: str) -> Optional[dict]:
    """Devuelve el primer perfil que coincida por email o None si no hay."""
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Accept": "application/json",
    }
    params = {"select": "id,email,is_active", "email": f"eq.{email}", "limit": 1}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{POSTGREST_URL}/profiles", headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None

@app.post("/prelogin-check", response_model=PreloginResponse)
async def prelogin_check(req: PreloginRequest):
    email = (req.email or "").strip().lower()
    if not EMAIL_RE.match(email):
        return PreloginResponse(eligible=False, reason="invalid_email")

    if not SUPABASE_URL or not SERVICE_ROLE_KEY:
        return PreloginResponse(eligible=False, reason="server_error")

    try:
        profile = await fetch_profile_by_email(email)
    except Exception:
        return PreloginResponse(eligible=False, reason="server_error")

    if profile is None:
        return PreloginResponse(eligible=False, reason="no_user")

    if not bool(profile.get("is_active")):
        return PreloginResponse(eligible=False, reason="inactive_profile")

    return PreloginResponse(eligible=True, reason="ok")

@app.get("/healthz")
def healthz():
    return {"ok": True}

# ----- (Opcional) CORS si FF Preview bloquea -----
try:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # o reduzca a su dominio de FF Preview
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except Exception:
    pass
