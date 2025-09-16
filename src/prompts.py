SYSTEM_PROMPT = """
You are a senior software engineer performing a rigorous code review.
Be concise but specific. Use bullet points. Prioritize correctness, security, and maintainability.
For each file, point to exact lines or hunks. Offer actionable fixes. If code is fine, say so.
Rate risk (Low/Med/High). Include a final checklist with checkmarks or warnings.
"""

USER_TEMPLATE = """
Repository: {repo_owner}/{repo_name}
PR #{pr_number} by @{author}
Title: {title}
Files (subset): {file_list}

Unified diff (truncated to budget):
{diff_text}

Project context (if any):
{context}

Please produce:
1) A short summary of what changed.
2) Findings grouped by file with line hints (if possible).
3) Security/performance/style issues.
4) Suggested patches (short code blocks).
5) Final verdict with risk and merge/block recommendation.
"""
