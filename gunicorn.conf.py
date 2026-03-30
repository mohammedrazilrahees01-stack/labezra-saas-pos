# Labezra POS — Gunicorn Configuration for Render
import os
import multiprocessing

# Render provides PORT env var
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Workers: 2 is safe for free tier, scale up for paid
workers = 2
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging to stdout/stderr (Render captures these)
accesslog = "-"
errorlog = "-"
loglevel = "info"
