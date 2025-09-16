# AI Code Review Bot

An automated code review bot that runs as a GitHub Action on pull requests and/or as a self-hosted FastAPI webhook service. It fetches the PR details and changed files, summarizes the diff within a byte budget, asks an LLM for a structured review, and posts the review back to the PR.

## Features

- LLM providers: OpenAI and Anthropic (auto-selects based on available keys)
- Byte-budgeted diff ingestion to control token usage
- Allow/Deny file globs to control which files are reviewed
- GitHub Action workflow for zero-infra usage
- Optional FastAPI server with GitHub webhook verification

## Repository Structure

- `src/main.py`: FastAPI app with `/health` and `POST /webhook/github`
- `src/review.py`: Core review flow: fetch PR, build diff text, call LLM, create review
- `src/github_client.py`: Minimal GitHub API client
- `src/llm.py`: Provider-agnostic LLM client (OpenAI/Anthropic)
- `src/prompts.py`: System and user prompts
- `.github/workflows/review.yml`: GitHub Action that runs on pull_request events
- `Dockerfile`: Container entrypoint for FastAPI server
- `tests/test_globs.py`: Basic test for file-inclusion logic

## Requirements

- Python 3.11+
- Packages in `requirements.txt`

```
fastapi==0.115.2
uvicorn==0.30.6
httpx==0.27.2
pydantic==2.9.2
python-dotenv==1.0.1
tiktoken==0.7.0
anyio==4.4.0
```

## Environment Variables

Set at least one LLM API key.

- `OPENAI_API_KEY`: OpenAI API key (enables OpenAI)
- `OPENAI_MODEL`: Default `gpt-4o-mini`
- `ANTHROPIC_API_KEY`: Anthropic API key (enables Anthropic)
- `ANTHROPIC_MODEL`: Default `claude-3-5-sonnet-latest`
- `MAX_TOTAL_BYTES`: Byte budget for diff text, default `250000`
- `POST_INLINE_COMMENTS`: `true|false` (currently posts a single review body; inline comments reserved)
- `REVIEW_TITLE`: Title prefix for the PR review comment, default `AI Review`
- `ALLOW_GLOBS`: Comma-separated allowlist (default `**/*.py,**/*.js,**/*.ts,**/*.tsx`)
- `DENY_GLOBS`: Comma-separated denylist (takes precedence)
- `GITHUB_API`: Optional GitHub API base (default `https://api.github.com`)
- `GITHUB_TOKEN`: Required in workflows/server to call GitHub API
- `GITHUB_WEBHOOK_SECRET`: Optional HMAC secret for webhook verification

Tip: Create an `.env` locally for the server using `.env.example` as a reference.

## Using the GitHub Action

The included workflow `.github/workflows/review.yml` runs on pull request events.

1) Add repository secrets:
   - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (one is required)
   - Optionally both to allow fallback
2) Commit the workflow (already present here). It will:
   - Check out the repo
   - Set up Python 3.11
   - Install `requirements.txt`
   - Run the review for the PR number from the event payload

The bot posts a single review comment on the PR titled with `REVIEW_TITLE`.

## Running the Server (FastAPI)

Start a local server listening on `0.0.0.0:8000`:

```
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Health check:

```
curl http://localhost:8000/health
```

### Webhook Endpoint

- `POST /webhook/github`
- Verifies `X-Hub-Signature-256` if `GITHUB_WEBHOOK_SECRET` is set
- Expects GitHub pull request events with actions: `opened`, `synchronize`, `reopened`, `edited`

On valid events, the server fetches PR details/files and posts an AI review.

## Docker

Build and run the API server in Docker:

```
docker build -t ai-code-review-bot .
docker run --rm -p 8000:8000 \
  -e GITHUB_TOKEN=ghp_xxx \
  -e OPENAI_API_KEY=sk-xxx \
  -e GITHUB_WEBHOOK_SECRET=your_secret \
  ai-code-review-bot
```

## How It Works

1. `src/github_client.py` fetches PR metadata and changed files (paginated) via GitHub API
2. `src/review.py` filters files using `ALLOW_GLOBS`/`DENY_GLOBS`, constructs a byte-limited unified diff blob
3. `src/llm.py` selects OpenAI or Anthropic and produces a structured review using `src/prompts.py`
4. The review is posted back via GitHub Reviews API as a single comment

## Configuration Tips

- To review additional file types, extend `ALLOW_GLOBS` (e.g., add `**/*.go,**/*.rs`)
- To skip vendored or generated code, populate `DENY_GLOBS` (e.g., `**/dist/**,**/vendor/**`)
- Increase `MAX_TOTAL_BYTES` for larger PRs (at higher token use)

## Testing

Run tests:

```
python -m pytest -q
```

## Troubleshooting

- Windows line endings: Git may warn about CRLF ↔ LF conversions; these are informational by default.
- Git push errors like `src refspec main does not match any` usually mean there are no commits yet; run `git add . && git commit -m "msg"` first.
- Ensure `GITHUB_TOKEN` is available in the environment (Actions provides `${{ secrets.GITHUB_TOKEN }}` automatically in the workflow).
- LLM provider errors: Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set and the model names are valid.

## Security

- If hosting the server, set `GITHUB_WEBHOOK_SECRET` and configure the same secret in your GitHub webhook to prevent spoofed requests.
- Never commit API keys. Use repository or organization secrets.

## License

See `LICENSE` for details.