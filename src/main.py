import os, hmac, hashlib
from fastapi import FastAPI, Header, HTTPException, Request
from .review import run_review

app = FastAPI(title="AI Code Review Bot")

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

def verify_signature(secret: str, signature: str, payload: bytes) -> bool:
    if not secret:
        return True
    if not signature:
        return False
    sha_name, signature = signature.split("=")
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/webhook/github")
async def github_webhook(request: Request, x_hub_signature_256: str | None = Header(default=None), x_github_event: str | None = Header(default=None)):
    body = await request.body()
    if not verify_signature(WEBHOOK_SECRET, x_hub_signature_256 or "", body):
        raise HTTPException(status_code=401, detail="Invalid signature")
    event = await request.json()
    if x_github_event == "pull_request" and event.get("action") in {"opened","synchronize","reopened","edited"}:
        repo = event["repository"]; owner = repo["owner"]["login"]; name = repo["name"]
        pr_number = event["pull_request"]["number"]
        await run_review(owner, name, pr_number)
    return {"received": True}
