# Deploying QuizCat

QuizCat is a terminal UI. It's made shareable on the web with
[`textual-serve`](https://github.com/Textualize/textual-serve), which runs the
real `main.py` in a subprocess and streams it to a browser terminal. The same
app you run locally is what visitors see — no separate web frontend.

## Run it as a web app locally

```bash
uv run python serve.py        # then open http://localhost:8000
```

## Run the production container locally

```bash
docker build -t quizcat .
docker run --rm -p 8000:8000 quizcat   # open http://localhost:8000
```

## Deploy to render.com

The repo ships a `Dockerfile` and a `render.yaml` Blueprint.

1. Push this repo to GitHub.
2. In render: **New → Blueprint**, select the repo, and apply. render reads
   `render.yaml`, builds the `Dockerfile`, and binds the app to its `$PORT`.
   (Or **New → Web Service → Docker** and accept the defaults.)
3. *(Optional)* In the service's **Environment** tab, set `OPENAI_API_KEY`.
   This is only needed for the in-app AI "generate test" feature; the bundled
   400-question bank works without it.

The container's health check hits `/`, which `textual-serve` serves.

### Notes

- The SQLite DB lives at `var/quizcat.sqlite3` and is recreated from the
  bundled CSV on each boot. It's ephemeral on render's free plan, which is fine
  for a demo — generated tests and attempt history reset when the instance
  restarts.
- The free plan spins the service down when idle, so the first request after a
  pause takes a few seconds to cold-start.
