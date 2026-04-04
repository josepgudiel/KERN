# Deployment Guide — Analytic

## Environment Variables

| Variable | Required | Where to get it | Description |
|----------|----------|-----------------|-------------|
| `GROQ_API_KEY` | Yes (for AI features) | [console.groq.com](https://console.groq.com) | Powers AI Brief, AI Advisor, and Summary Reports. Free tier available. |

> **Note:** AI features (AI Brief, AI Advisor, Monthly Summary) are disabled gracefully when no API key is set. All statistical analysis works without it.

## Fastest Path to a Live URL: Streamlit Community Cloud

Streamlit Cloud is the correct deployment target for this app. It's free, requires zero DevOps, auto-deploys from GitHub, and natively understands Streamlit's config format. Here's exactly what to do:

### Steps

1. **Push to GitHub** — Create a public or private repo and push the project.

2. **Go to [share.streamlit.io](https://share.streamlit.io)** — Sign in with GitHub.

3. **Deploy** — Select your repo, set `app.py` as the main file.

4. **Set secrets** — In the Streamlit Cloud dashboard, go to **Settings → Secrets** and add:
   ```toml
   GROQ_API_KEY = "your_groq_key_here"
   ```

5. **Done** — Your app will be live at `https://your-app-name.streamlit.app` within ~3 minutes.

### Why Streamlit Cloud (not Railway, Vercel, or Docker)

- **Zero config**: It reads `.streamlit/config.toml` natively.
- **Free tier**: Generous enough for early customers (1 app, public or private).
- **Auto-deploy**: Pushes to `main` trigger a redeploy automatically.
- **Python-native**: No Dockerfile, no Procfile, no buildpack guessing.
- **Secrets management**: Built-in, no `.env` files to manage.

For paid/private deployment at scale, Railway or a Docker container on Render are good next steps.

## Alternative: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
```

## Alternative: Railway

1. Connect your GitHub repo to Railway.
2. Set the start command: `streamlit run app.py --server.port=$PORT --server.headless=true`
3. Add `GROQ_API_KEY` in the Railway environment variables panel.

## Pre-deployment Checklist

- [ ] `GROQ_API_KEY` is set in your deployment platform's secrets/env vars
- [ ] `.streamlit/config.toml` exists with headless=true
- [ ] `requirements.txt` has pinned versions
- [ ] No `.env` files are committed to the repo
- [ ] Test with demo data after deployment to verify all features work
