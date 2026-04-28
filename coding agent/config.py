# config.py
# ══════════════════════════════════════════════════════
# All project configurations in one place
# If you want to change anything, change it here
# ══════════════════════════════════════════════════════

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── OpenRouter ─────────────────────────────────────────────
# Using OpenRouter with a fast, reliable model
# API key stored in .env file
# Model options (all fast/free):
#   - mistral/mistral-7b (FAST, recommended)
#   - mistral/mistral-medium
#   - meta-llama/llama-2-7b
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
OPENROUTER_MODEL_DISPLAY = "NVIDIA Nemotron-3 Super 120B (OpenRouter)"

LLM_TEMPERATURE = 0.2   # Lower means more consistent and less creative responses
                         # Suitable for code since we want specific, non-random results

# ── Agent ──────────────────────────────────────────────
MAX_RETRIES = 10
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