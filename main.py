from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PreloginRequest(BaseModel):
    email: str

@app.post("/prelogin-check")
async def prelogin_check(req: PreloginRequest):
    if req.email.endswith("@inactive.com"):
        return {"eligible": False, "reason": "inactive_profile"}
    elif req.email.endswith("@nouser.com"):
        return {"eligible": False, "reason": "no_user"}
    else:
        return {"eligible": True, "reason": "ok"}
