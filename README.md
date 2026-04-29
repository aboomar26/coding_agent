# 🤖 Multi-Agent Coding Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

> **Production-ready autonomous AI-powered coding assistant** that autonomously plans, writes, reviews, and executes code in an isolated sandbox environment.  
> Built with **LangGraph**, **LangChain**, **OpenRouter**, and **Docker** for enterprise-grade safety, reliability, and modularity.

---

## ✨ Key Features

- **🧠 Multi-Agent Pipeline**: Orchestrated workflow (Planner → Researcher → Writer → Executor → Critic → Finalizer) for comprehensive code generation
- **🔍 Contextual Code Analysis**: Reads and understands existing codebase structure for informed decision-making
- **✅ Human-in-the-Loop Approval**: Request explicit approval before executing any changes—maintaining full control
- **🐳 Docker Sandbox Execution**: Isolated container execution ensures zero impact on the host system
- **📝 Intelligent Planning**: Creates detailed, step-by-step execution plans before implementation
- **🔄 Robust Retry Logic**: Automatic recovery from transient errors with exponential backoff
- **💾 Precision File Management**: Edit, create, and manage files with granular control
- **⚡ High-Performance LLM Access**: Leverages OpenRouter for access to state-of-the-art models

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
- [Skills](#skills)
- [License](#license)

---

## 🚀 Quick Start

```bash
# 1. Clone repository and navigate to project directory
git clone <repository-url>
cd coding-agent

# 2. Install Python dependencies
pip install -r Requirements.txt

# 3. Configure environment variables
# Create .env file with your OpenRouter API key (see Prerequisites)
echo "OPENROUTER_API_KEY=your-key-here" > .env

# 4. Verify Docker setup (optional but recommended for production)
docker ps

# 5. Launch the agent
python main.py
```

---

## 📦 Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.10+** — [Download](https://www.python.org/) — Required runtime environment
- **Docker Desktop** (optional but recommended) — [Download](https://www.docker.com/products/docker-desktop) — For isolated code execution
- **OpenRouter API Key** (free tier available) — [Get Key](https://openrouter.ai) — For LLM inference

### Environment Configuration

Create a `.env` file in the project root directory with your API credentials:

```env
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

---

## 📥 Installation

### Step 1: Install Python Dependencies

```bash
pip install -r Requirements.txt
```

All required packages will be installed with compatible versions.

### Step 2: Configure API Key

1. Sign up for a free account at [OpenRouter.ai](https://openrouter.ai)
2. Navigate to **Settings → API Keys**
3. Create a new API key
4. Add the key to your `.env` file:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### Step 3: Set Up Docker (Optional but Recommended)

For production environments, Docker provides isolated execution:

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

Edit `config.py` to customize system behavior for your specific requirements:

```python
# LLM Model Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
LLM_TEMPERATURE = 0.2  # Lower values = more deterministic output

# Agent Pipeline Configuration
MAX_RETRIES = 10  # Maximum retry attempts for failed operations
RESEARCHER_MAX_ROUNDS = 6  # Maximum research iterations

# Docker Sandbox Configuration
SANDBOX_IMAGE = "python:3.12-slim"  # Base container image
SANDBOX_MEMORY = "512m"  # Memory limit per container
SANDBOX_CPUS = "1.0"  # CPU allocation
SANDBOX_TIMEOUT = 120  # Execution timeout in seconds
```

### Available Models

Browse [OpenRouter's model catalog](https://openrouter.ai/docs#models) for alternative models. Free-tier options include:
- `nvidia/nemotron-3-super-120b-a12b:free` (recommended)
- `meta-llama/llama-2-7b:free`

---

## 💻 Usage

### Running the Agent

```bash
# Interactive mode (prompts for workspace directory)
python main.py

# Direct mode (specify workspace)
python main.py --workspace ./my-project

# Development mode (without Docker sandbox)
python main.py --workspace ./my-project --no-sandbox
```

### Example Requests

The agent accepts natural language requests for code-related tasks:

```
❯ Create a Python script that reads a CSV file and generates a bar chart

❯ Build a FastAPI application with /health and /predict endpoints

❯ Create a utils folder with helpers.py containing date manipulation functions

❯ Debug the bug in app.py where the calculate_total function returns incorrect values

❯ Generate comprehensive unit tests for all functions in utils/helpers.py
```

### Approval Workflow

When the agent proposes changes, you will be prompted for approval before execution:

```
[1/2] edit_file
📄 File    : app.py
✏️  Replace : 'def hello(): ...'

Do you approve? (y/n):
```

| Option | Action |
|--------|--------|
| `y` | ✅ Approve and execute changes |
| `n` | ⏭️ Skip (propose next change) |

---

## 🏗️ Architecture

### Agent Pipeline

The system implements a sophisticated multi-agent orchestration pattern:

```
User Input (Natural Language)
    ↓
┌─────────────────────────────┐
│  🧠 PLANNER                 │ Decomposes task into numbered steps
├─────────────────────────────┤
│  🔍 RESEARCHER              │ Analyzes existing codebase
├─────────────────────────────┤
│  ✍️  WRITER                 │ Generates implementation tasks
├─────────────────────────────┤
│  ⚙️  EXECUTOR               │ Requests approval & executes
├─────────────────────────────┤
│  👨‍⚖️ CRITIC                 │ Validates code quality & correctness
├─────────────────────────────┤
│  📋 FINALIZER               │ Summarizes changes & outcomes
└─────────────────────────────┘
    ↓
   Output Summary
```

### Execution Environment: Docker Sandbox

Code execution is completely isolated from the host system:

```
Host System                    Docker Container
─────────────────────────      ──────────────────────
./my-project/      ↔─────→    /workspace/
  ├─ app.py                  app.py
  ├─ utils/                  utils/
  └─ config.py               config.py

Python code executed here,     Results returned safely
changes proposed to user       (zero risk to host)
```

---

## 📁 Project Structure

```
coding-agent/
│
├── main.py                      Application entry point
├── config.py                    Centralized configuration & constants
├── Requirements.txt             Python package dependencies
├── .env                         API credentials (git-ignored)
├── README.md                    Project documentation
│
├── agent/
│   ├── __init__.py
│   ├── graph.py                LangGraph workflow definition & orchestration
│   ├── nodes.py                Individual agent node implementations
│   └── tools.py                File management & execution tools
│
├── sandbx/
│   ├── __init__.py
│   └── docker_runner.py        Docker container management & execution
│
└── llm/
    └── Ollama_ngrok.ipynb      Optional: Run Ollama on Google Colab
```

---

## 🔧 Troubleshooting

### ❌ Error: "401 - User not found"

**Cause**: Invalid or expired OpenRouter API key

**Solution**:
1. Visit [OpenRouter API Keys](https://openrouter.ai/keys)
2. Revoke the old key and create a new one
3. Update your `.env` file with the new key
4. Restart the application

---

### ❌ Error: "Cannot connect to Docker daemon"

**Cause**: Docker is not running or not properly installed

**Solution**:
```bash
# Windows: Start Docker Desktop from the Start Menu
# Linux: sudo systemctl start docker
# macOS: Open Docker.app

# Verify Docker is running
docker ps
```

---

### ❌ Error: "ModuleNotFoundError: No module named 'langchain'"

**Cause**: Python dependencies not installed

**Solution**:
```bash
pip install -r Requirements.txt --upgrade
```

---

### ❌ Error: "Connection refused" or "timeout"

**Cause**: OpenRouter API unreachable or slow network

**Solution**:
- Verify internet connection
- Check API key validity
- Try an alternative model in `config.py`
- Monitor [OpenRouter status page](https://status.openrouter.ai)
- Check local firewall settings

---

## 📋 Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Runtime environment |
| LangGraph | Latest | Multi-agent orchestration framework |
| LangChain | Latest | LLM integration & chain management |
| Docker | Latest | Containerized code execution |
| OpenRouter API | Free tier available | LLM inference access |

For complete dependency list, see [Requirements.txt](Requirements.txt)

---

## ⚠️ Important Notes

- ✅ **Safe by Default**: All changes require explicit user approval before execution
- 🐳 **Isolated Execution**: Code runs exclusively within Docker containers—zero impact on host system
- 📁 **Workspace-Scoped**: Only creates or modifies files within the specified workspace directory
- 💾 **No Auto-Commit**: Changes are not automatically committed to version control
- 🔑 **Credential Security**: Never share API keys; ensure `.env` is added to `.gitignore`
- 🧪 **Testing**: Always review generated code for correctness before production deployment

---

## 🤝 Contributing

We welcome contributions from the community! To contribute:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-improvement`
3. **Commit** your changes: `git commit -am 'Add your improvement'`
4. **Push** to the branch: `git push origin feature/your-improvement`
5. **Open** a Pull Request with a detailed description of your changes

Please ensure your code follows the existing style and includes appropriate tests.

---

## 📄 License

This project is licensed under the **MIT License**—a permissive open-source license. See the [LICENSE](LICENSE) file for full details.

---

## 📞 Support

For questions, issues, or contributions:

- **Issues**: [Open an issue on GitHub](../../issues) for bug reports or feature requests
- **Discussions**: [GitHub Discussions](../../discussions) for questions and community support
- **Documentation**: See [README.md](README.md) for detailed usage information

---

## 🎓 Disclaimer

**Important**: This tool generates and executes code autonomously. While it includes safety measures and isolation features, please follow these best practices:

- Always review generated code for correctness and security before approval
- Test thoroughly in development environments before production use
- Maintain backups of important files before making changes
- Use Docker sandbox execution for maximum safety
- Monitor LLM output for unexpected behaviors or errors

---

## 🛠️ Skills

`LangGraph` · `LangChain` · `multi-agent systems` · `prompt engineering` · `Docker` · `Python` · `REST APIs` · `async Python` · `file management` · `error handling` · `code analysis` · `LLM reasoning` · `chain-of-thought` · `human-in-the-loop` · `OpenRouter API` · `CLI development`