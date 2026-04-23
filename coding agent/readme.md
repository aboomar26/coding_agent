# 🤖 Multi-Agent Coding Assistant

> LangGraph + Ollama + Docker Sandbox  
> You give it a request, it thinks, writes code, asks for your approval, and executes it — all automatically.

---

## Project Structure

```
coding agent/
│
├── main.py                 ← Entry point — run this
├── config.py               ← All configurations are here
├── Requirements.txt        ← Required libraries
│
├── agent/
│   ├── __init__.py
│   ├── nodes.py            ← Every node in the pipeline
│   │                         (Planner, Researcher, Writer, Executor, Critic, Finalizer)
│   ├── graph.py            ← Assembling the nodes in LangGraph
│   └── tools.py            ← Tools (edit_file, run_command, read_file, list_directory)
│
├── sandbx/
│   ├── __init__.py
│   └── docker_runner.py    ← Running commands inside Docker (isolated)
│
└── llm/
    └── vllm_ngrok.ipynb    ← Running Ollama on Colab GPU and exposing it via ngrok
```

---

## Step-by-Step Flow

```
You write a request
      ↓
  Planner        → Creates a numbered plan
      ↓
  Researcher     → Reads your existing files
      ↓
  Writer         → Writes a JSON list of commands
      ↓
  Executor       → Shows each command and asks [y/n]
      ↓
  Critic         → SUCCESS or RETRY?
   ↙    ↘
Writer  Finalizer → Final summary
(retry)
```

---

## Setup and Execution

### 1. Install Libraries

```powershell
pip install -r Requirements.txt
```

### 2. Run Ollama

**Method 1 — Locally on your machine (without GPU):**

```powershell
# Install Ollama from: https://ollama.com/download

# Download the model (~4.7 GB)
ollama pull qwen2.5-coder:7b

# Run the server (in a separate terminal)
ollama serve
```

**Method 2 — On Colab GPU via ngrok (faster):**

1. Open `llm/vllm_ngrok.ipynb` in VS Code and connect to Colab.
2. Get a free ngrok token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Paste the token in Cell 2 and run all cells.
4. Cell 5 will print a URL — paste it into PowerShell:

```powershell
$env:OLLAMA_NGROK_URL = "https://xxxx-xx-xx.ngrok-free.app"
```

### 3. Install Docker (for Sandbox)

```powershell
# Windows: Download Docker Desktop from https://www.docker.com/products/docker-desktop
# Run it and make sure it's running before starting the agent
```

### 4. Run the Agent

```powershell
# Normal run (with Docker sandbox)
python main.py

# Specify directory directly
python main.py --workspace ./my-project

# Without Docker — for quick testing
python main.py --workspace ./my-project --no-sandbox
```

---

## Approval Gate Options

When the agent proposes a modification or command, you'll see:

```
  [1/2] edit_file
  📄 File    : app.py
  ✏️  Replace : 'def hello(): ...'

  Do you approve modifying this file? (y/n):
```

| Option | Meaning |
|--------|---------|
| `y`  | Approve and execute |
| `n`  | Skip (won't be executed) |

---

## Configuration (config.py)

```python
# Ollama
OLLAMA_BASE_URL = "http://localhost:11434"       # or OLLAMA_NGROK_URL for Colab
OLLAMA_MODEL    = "qwen2.5-coder:7b"             # change to any other model

# Docker Sandbox
SANDBOX_IMAGE   = "python:3.12-slim"
SANDBOX_MEMORY  = "512m"
SANDBOX_TIMEOUT = 120                            # seconds

# Agent
MAX_RETRIES           = 5
RESEARCHER_MAX_ROUNDS = 6
```

**To change the model:**
```powershell
ollama pull codellama:13b     # for example
# Then in config.py:
# OLLAMA_MODEL = "codellama:13b"
```

---

## Usage Examples

```
❯ create a Python script that reads a CSV and draws a bar chart

❯ create a FastAPI app with /health and /predict endpoints

❯ create a utils folder with helpers.py containing date manipulation functions

❯ fix the bug in app.py — the function calculate_total returns wrong value

❯ write unit tests for all functions in utils/helpers.py
```

---

## Docker Sandbox

```
Your machine               Docker Container
─────────────────           ─────────────────────
./my-project/    ←────────→  /workspace/
  app.py                       app.py
  requirements.txt             requirements.txt

Modifications to files      Commands are executed here
happen directly via Python  (pip install, python, ...)
                            If an error occurs, it
                            only affects the container
```

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Ollama | Any version |
| Docker Desktop | (Optional — for sandbox) |
| `langchain-ollama` | ≥ 0.1.0 |
| `langgraph` | ≥ 0.1.0 |

---

## Important Notes

- **Files are created in the directory you selected** — not in the project directory itself.
- **Commands run inside Docker** — isolated from your system (if using sandbox).
- **Ollama must be running** before executing `main.py`.
- **Without your approval** no file will be modified or command executed.