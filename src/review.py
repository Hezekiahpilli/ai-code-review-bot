import os
from typing import List, Tuple
from fnmatch import fnmatch
from .llm import LLMClient
from .github_client import GitHub
from .prompts import SYSTEM_PROMPT, USER_TEMPLATE

MAX_TOTAL_BYTES = int(os.getenv("MAX_TOTAL_BYTES", "250000"))
ALLOW_GLOBS = [g.strip() for g in os.getenv("ALLOW_GLOBS", "**/*.py,**/*.js,**/*.ts,**/*.tsx").split(",") if g.strip()]
DENY_GLOBS = [g.strip() for g in os.getenv("DENY_GLOBS", "").split(",") if g.strip()]
POST_INLINE_COMMENTS = os.getenv("POST_INLINE_COMMENTS", "false").lower() == "true"
REVIEW_TITLE = os.getenv("REVIEW_TITLE", "AI Review")

def _include(path: str) -> bool:
    if any(fnmatch(path, pat) for pat in DENY_GLOBS):
        return False
    if not ALLOW_GLOBS:
        return True
    return any(fnmatch(path, pat) for pat in ALLOW_GLOBS)

async def build_diff_text(files: List[dict]) -> Tuple[str, List[str]]:
    included = []
    diff_parts = []
    total = 0
    for f in files:
        filename = f.get("filename","")
        if not _include(filename):
            continue
        patch = f.get("patch")
        if not patch:
            continue
        b = len(patch.encode("utf-8"))
        if total + b > MAX_TOTAL_BYTES:
            break
        diff_parts.append(f"--- {filename}\n{patch}\n")
        included.append(filename)
        total += b
    return "\n".join(diff_parts), included

async def run_review(owner: str, repo: str, pr_number: int, github_token: str = None) -> str:
    gh = GitHub(github_token)
    details = await gh.pr_details(owner, repo, pr_number)
    files = await gh.pr_files(owner, repo, pr_number)
    diff_text, file_list = await build_diff_text(files)

    llm = LLMClient()
    user = USER_TEMPLATE.format(
        repo_owner=owner,
        repo_name=repo,
        pr_number=pr_number,
        author=details.get("user",{}).get("login","unknown"),
        title=details.get("title",""),
        file_list="\n".join(file_list) or "(none included; diff too large)",
        diff_text=diff_text or "(no diff content available within budget)",
        context="",
    )
    review_text = await llm.complete(SYSTEM_PROMPT, user)
    await gh.create_review(owner, repo, pr_number, f"## {REVIEW_TITLE}\n\n" + review_text)
    return review_text
