# 🤖 Multi-Agent Coding Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

> **Autonomous AI-powered coding assistant** that plans, writes, reviews, and executes code in an isolated sandbox environment.  
> Built with **LangGraph**, **LangChain**, **OpenRouter**, and **Docker** for safety and modularity.

---

## ✨ Features

- 🧠 **Multi-Agent Pipeline**: Planner → Researcher → Writer → Executor → Critic → Finalizer
- 🔍 **Code Analysis**: Reads existing files and understands project context
- ✅ **Human-in-the-Loop**: Ask for approval before executing any changes
- 🐳 **Docker Sandbox**: Execute code safely in isolated containers
- 📝 **Intelligent Planning**: Creates step-by-step execution plans
- 🔄 **Retry Logic**: Automatically recovers from transient errors
- 💾 **File Management**: Edit, create, and manage files with git-like precision
- ⚡ **Fast Models**: Uses OpenRouter for access to high-performance LLMs

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [License](#license)

---

## 🚀 Quick Start

```bash
# 1. Clone and navigate to project
git clone <repo-url>
cd coding-agent

# 2. Install dependencies
pip install -r Requirements.txt

# 3. Set up environment variables
# Create a .env file with your OpenRouter API key
echo "OPENROUTER_API_KEY=your-key-here" > .env

# 4. Ensure Docker is running (optional but recommended)
docker ps

# 5. Run the agent
python main.py
```

---

## 📦 Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/)
- **Docker Desktop** (optional but recommended) — [Download](https://www.docker.com/products/docker-desktop)
- **OpenRouter API Key** (free tier available) — [Get Key](https://openrouter.ai)

### Environment Variables

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

---

## 📥 Installation

### Step 1: Install Python Dependencies

```bash
pip install -r Requirements.txt
```

### Step 2: Configure API Key

1. Sign up for free at [OpenRouter.ai](https://openrouter.ai)
2. Navigate to **Settings → API Keys**
3. Create a new API key
4. Add to `.env` file:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### Step 3: Set Up Docker (Optional)

```bash
# Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop

# Linux
sudo apt-get install docker.io
sudo usermod -aG docker $USER

# Verify installation
docker --version
```

---

## ⚙️ Configuration

Edit `config.py` to customize behavior:

```python
# LLM Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
LLM_TEMPERATURE = 0.2

# Agent Settings
MAX_RETRIES = 10
RESEARCHER_MAX_ROUNDS = 6

# Docker Sandbox
SANDBOX_IMAGE = "python:3.12-slim"
SANDBOX_MEMORY = "512m"
SANDBOX_CPUS = "1.0"
SANDBOX_TIMEOUT = 120
```

### Changing the LLM Model

Available free models on OpenRouter:
- `nvidia/nemotron-3-super-120b-a12b:free`
- `meta-llama/llama-2-7b:free`

---

## 💻 Usage

### Run the Agent

```bash
# Interactive mode (prompts for directory)
python main.py

# Specify directory directly
python main.py --workspace ./my-project

# Without Docker sandbox (quick testing)
python main.py --workspace ./my-project --no-sandbox

```

### Example Requests

```
❯ create a Python script that reads a CSV and draws a bar chart

❯ create a FastAPI app with /health and /predict endpoints

❯ create a utils folder with helpers.py containing date manipulation functions

❯ fix the bug in app.py — the function calculate_total returns wrong value

❯ write unit tests for all functions in utils/helpers.py
```

### Approval Gate

When the agent proposes changes, you'll be asked for approval:

```
[1/2] edit_file
📄 File    : app.py
✏️  Replace : 'def hello(): ...'

Do you approve? (y/n):
```

| Option | Action |
|--------|--------|
| `y` | ✅ Approve and execute |
| `n` | ⏭️ Skip (won't execute) |

---

## 🏗️ Architecture

### Agent Pipeline

```
User Input
    ↓
┌─────────────────────────────┐
│  🧠 PLANNER                 │ Creates numbered plan
├─────────────────────────────┤
│  🔍 RESEARCHER              │ Reads existing files
├─────────────────────────────┤
│  ✍️  WRITER                 │ Generates execution tasks
├─────────────────────────────┤
│  ⚙️  EXECUTOR               │ Asks for approval & executes
├─────────────────────────────┤
│  👨‍⚖️ CRITIC                 │ Validates results
├─────────────────────────────┤
│  📋 FINALIZER               │ Summarizes changes
└─────────────────────────────┘
    ↓
   Done
```

### Docker Sandbox Isolation

```
Your Machine                Docker Container
─────────────────          ─────────────────────
./my-project/   ↔─────→   /workspace/
  ├─ app.py              app.py
  ├─ utils/              utils/
  └─ config.py           config.py

File editing happens    Code execution happens here
directly via Python     (isolated, safe environment)
```

---

## 📁 Project Structure

```
coding-agent/
│
├── main.py                      Entry point
├── config.py                    All configuration settings
├── Requirements.txt             Python dependencies
├── .env                         API keys (don't commit!)
├── README.md                    This file
│
├── agent/
│   ├── __init__.py
│   ├── graph.py                LangGraph workflow definition
│   ├── nodes.py                Agent nodes (Planner, Researcher, Writer, etc.)
│   └── tools.py                Tools for file & code management
│
├── sandbx/
│   ├── __init__.py
│   └── docker_runner.py        Docker sandbox execution
│
└── llm/
    └── Ollama_ngrok.ipynb      (Optional) Run Ollama on Google Colab
```

---

## 🔧 Troubleshooting

### ❌ "Error code: 401 - User not found"

**Problem**: API key is invalid or expired.

**Solution**:
1. Visit [OpenRouter.ai](https://openrouter.ai/keys)
2. Delete old key and create a new one
3. Update `.env` file with new key
4. Restart the agent

### ❌ "Cannot connect to Docker daemon"

**Problem**: Docker isn't running or not installed.

**Solution**:
```bash
# Windows: Start Docker Desktop from Start Menu
# Linux: sudo systemctl start docker
docker ps  # Verify it's running
```

### ❌ "ModuleNotFoundError: No module named 'langchain'"

**Problem**: Dependencies not installed.

**Solution**:
```bash
pip install -r Requirements.txt --upgrade
```

### ❌ "Connection refused" or "timeout"

**Problem**: OpenRouter API is unreachable or too slow.

**Solution**:
- Check internet connection
- Verify API key is valid
- Try a different model in `config.py`
- Check [OpenRouter status page](https://status.openrouter.ai)

---

## 📋 Requirements

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| LangGraph | Latest | Agent orchestration |
| LangChain | Latest | LLM integration |
| Docker | Latest | Sandbox execution |
| OpenRouter API Key | (free) | LLM inference |

---

## ⚠️ Important Notes

- ✅ **Safe by Default**: All changes require your approval before execution
- 🐳 **Isolated Execution**: Code runs in Docker containers, never on your machine
- 📁 **Directory-Specific**: Creates/modifies files only in your selected workspace
- 💾 **No Auto-Commit**: Changes are not automatically committed to git
- 🔑 **Never Share Keys**: Keep API keys secret; add `.env` to `.gitignore`

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Issues**: [Open an issue on GitHub](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)
- **Documentation**: See [README.md](README.md)

---

## 🎓 Disclaimer

This tool generates and executes code automatically. While it includes safety measures:
- Always review generated code before approval
- Use in isolated environments when possible
- Test thoroughly before production use
- Keep backups of important files