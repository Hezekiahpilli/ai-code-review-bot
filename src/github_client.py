import os
from typing import Dict, List
import httpx

GITHUB_API = os.getenv("GITHUB_API", "https://api.github.com")

class GitHub:
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("Missing GITHUB_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"}

    async def pr_details(self, owner: str, repo: str, pr: int) -> Dict:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr}", headers=self.headers)
            r.raise_for_status()
            return r.json()

    async def pr_files(self, owner: str, repo: str, pr: int) -> List[Dict]:
        files = []
        page = 1
        async with httpx.AsyncClient(timeout=60) as client:
            while True:
                r = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr}/files?page={page}&per_page=100", headers=self.headers)
                r.raise_for_status()
                batch = r.json()
                files.extend(batch)
                if len(batch) < 100:
                    break
                page += 1
        return files

    async def create_review(self, owner: str, repo: str, pr: int, body: str, event: str = "COMMENT"):
        async with httpx.AsyncClient(timeout=60) as client:
            payload = {"body": body, "event": event}
            r = await client.post(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr}/reviews", headers=self.headers, json=payload)
            r.raise_for_status()
            return r.json()
