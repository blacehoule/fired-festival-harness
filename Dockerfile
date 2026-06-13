# QuizCat — served in the browser via textual-serve.
# Uses the official uv image so the build matches local `uv sync` exactly.
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

# Install dependencies first against the committed lockfile so this layer is
# cached across code-only changes. --frozen fails loudly if the lock is stale.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Then the application code.
COPY . .

# render.com injects $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["uv", "run", "--frozen", "--no-dev", "python", "serve.py"]
