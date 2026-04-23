# config.py
# ══════════════════════════════════════════════════════
# All project configurations in one place
# If you want to change anything, change it here
# ══════════════════════════════════════════════════════

import os

# ── Ollama ─────────────────────────────────────────────
# Ollama runs locally on port 11434 — doesn't require a strong GPU
# Run the model first: ollama pull qwen2.5-coder:7b
#
# If running on Colab + ngrok, set the URL in PowerShell:
#   $env:OLLAMA_NGROK_URL = "https://xxxx-xx-xx.ngrok-free.app"
#   python main.py
#
# If running locally, leave it as is
# Reads from env var OLLAMA_NGROK_URL first, falls back to local
OLLAMA_BASE_URL = os.getenv("OLLAMA_NGROK_URL", "http://localhost:11434")
OLLAMA_MODEL    = "qwen2.5-coder:7b"   # lightweight model — runs on 8 GB RAM
OLLAMA_API_KEY  = "ollama"   # Local Ollama doesn't require a real API key

LLM_TEMPERATURE = 0.2   # Lower means more consistent and less creative responses
                         # Suitable for code since we want specific, non-random results

# ── Agent ──────────────────────────────────────────────
MAX_RETRIES = 5
# If Critic says RETRY more than this, we stop and consider it a success
# to avoid infinite loops

RESEARCHER_MAX_ROUNDS = 6
# Researcher can read files up to a maximum of 6 rounds
# Each round = one tool call (e.g. read a file or list a directory)

# ── Docker Sandbox ─────────────────────────────────────
SANDBOX_IMAGE   = "python:3.12-slim"
# The image where the code will be executed
# python:3.12-slim = lightweight version of Python without extra bloat

SANDBOX_MEMORY  = "512m"   # RAM limit for the container
SANDBOX_CPUS    = "1.0"    # CPU limit
SANDBOX_TIMEOUT = 120      # seconds — if a command takes longer, we stop it

# ── Workspace ──────────────────────────────────────────
WORKSPACE_IN_CONTAINER = "/workspace"
# The directory seen by the container
# The container will run in /workspace
# which maps to the directory you have open on your machine