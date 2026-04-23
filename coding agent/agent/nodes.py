# agent/nodes.py  — fully rewritten, English only, stronger prompts
import json
import re
import time
from pathlib import Path
from typing import List, Literal

from langchain_core.messages import (
    AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage,
)
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict

from agent.tools import (
    tool_edit_file, tool_list_directory, tool_read_file, tool_run_command,
)
from config import (
    LLM_TEMPERATURE, MAX_RETRIES, RESEARCHER_MAX_ROUNDS,
    OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL,
)
from sandbx.docker_runner import DockerSandbox

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL,
    api_key=OLLAMA_API_KEY, temperature=LLM_TEMPERATURE,
)

# ── LLM call with retry ───────────────────────────────────────────────────────
def _llm_invoke(messages: List[BaseMessage], max_attempts: int = 3) -> BaseMessage:
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return llm.invoke(messages)
        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            if any(k in msg for k in ("502","ngrok","connection","timeout","reset")):
                if attempt < max_attempts - 1:
                    wait = 2 ** attempt
                    print(f"\n  [llm] retrying in {wait}s: {exc}")
                    time.sleep(wait)
                    continue
            raise
    raise last_exc

# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    user_request : str
    workspace    : str
    plan         : str
    context      : str
    code_action  : str
    last_result  : str
    status       : str
    retry_count  : int
    messages     : List[BaseMessage]
    final_answer : str

# ── Helpers ───────────────────────────────────────────────────────────────────
def _text(msg: BaseMessage) -> str:
    if isinstance(msg.content, str):
        return msg.content
    return " ".join(b.get("text","") if isinstance(b,dict) else str(b) for b in msg.content)

def _repair_json(raw: str) -> list:
    """4-stage JSON repair. Always returns a list (never raises)."""
    # Stage 1 — raw parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Stage 2 — strip markdown fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    cleaned = cleaned.strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Stage 3 — remove inline comments (# and //)
    no_comments = re.sub(r'(?m)\s*#[^\n"\']*$', '', cleaned)
    no_comments = re.sub(r'(?m)\s*//[^\n"\']*$', '', no_comments)
    try:
        return json.loads(no_comments)
    except json.JSONDecodeError:
        pass
    # Stage 4 — extract first [...] block
    m = re.search(r'\[.*\]', no_comments, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    # Unrecoverable
    return [{"tool": "__json_error__", "args": {
        "error": "Writer produced JSON that could not be repaired.",
        "raw": raw[:400]
    }}]

# ── PLANNER ───────────────────────────────────────────────────────────────────
def node_planner(state: AgentState) -> AgentState:
    print("\n" + "═"*60 + "\n  📋  PLANNER\n" + "═"*60)
    response = _llm_invoke([
        SystemMessage(content=(
            "You are a senior software engineer acting as a Planner.\n"
            "Your ONLY job: read the request and output a concise numbered plan.\n\n"
            "RULES:\n"
            "- Do NOT write any code.\n"
            "- Do NOT suggest virtual environments (venv) — the sandbox already has Python.\n"
            "- Do NOT suggest Windows commands. Execution environment is Linux (Docker).\n"
            "- Maximum 6 steps. Each step = one concrete action.\n"
            "- For web frameworks: just create files and pip install. No venv needed."
        )),
        HumanMessage(content=(
            f"Request:\n{state['user_request']}\n\n"
            f"Workspace: {state['workspace']}\n\n"
            "Write the plan:"
        )),
    ])
    plan = _text(response)
    print(f"\n{plan}")
    return {**state, "plan": plan, "status": "running",
            "messages": state["messages"] + [AIMessage(content=f"[PLAN]\n{plan}")]}

# ── RESEARCHER ────────────────────────────────────────────────────────────────
def node_researcher(state: AgentState) -> AgentState:
    print("\n" + "═"*60 + "\n  🔍  RESEARCHER\n" + "═"*60)
    workspace = Path(state["workspace"])
    safe_tools = [
        {"name": "list_directory",
         "description": "List directory contents inside the workspace.",
         "parameters": {"type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"]}},
        {"name": "read_file_content",
         "description": "Read a file's text content.",
         "parameters": {"type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"]}},
    ]
    safe_llm = llm.bind_tools(safe_tools)
    messages: List[BaseMessage] = [
        SystemMessage(content=(
            "You are a Researcher. Explore the workspace and write a CONTEXT SUMMARY.\n"
            "- Start with list_directory on '.'.\n"
            "- Read relevant existing files.\n"
            "- Do NOT modify any files.\n"
            "- End with a CONTEXT SUMMARY listing: existing structure, relevant content, "
            "what the Writer must create vs modify."
        )),
        HumanMessage(content=f"Plan:\n{state['plan']}\n\nBegin exploring."),
    ]
    context = ""
    for _ in range(RESEARCHER_MAX_ROUNDS):
        response = safe_llm.invoke(messages)
        messages.append(response)
        calls = getattr(response, "tool_calls", [])
        if not calls:
            context = _text(response)
            break
        for tc in calls:
            name, args = tc["name"], tc["args"]
            print(f"  → {name}({args})")
            if name == "list_directory":
                result = tool_list_directory(workspace, args.get("path", "."))
            elif name == "read_file_content":
                result = tool_read_file(workspace, args.get("path", ""))
            else:
                result = f"[ERROR] Tool '{name}' not available in Researcher."
            messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    context = context or "Workspace appears empty — start fresh."
    print(f"\n{context}")
    return {**state, "context": context,
            "messages": state["messages"] + [AIMessage(content=f"[CONTEXT]\n{context}")]}

# ── WRITER ────────────────────────────────────────────────────────────────────
_WRITER_SYSTEM = """\
You are a Writer agent. Output ONLY a valid JSON array of tool actions.

═══════════════════════════════════════════════
ABSOLUTE JSON RULES — any violation breaks parsing:
═══════════════════════════════════════════════
1. Output ONLY the JSON array. Zero text before or after it.
2. NO markdown fences (no ```json, no ```).
3. NO comments whatsoever — not # and not //. Comments are ILLEGAL in JSON.
4. All strings must use double quotes. Never single quotes.
5. working_dir must be a simple relative name like "." or "myapp".
   NEVER use absolute paths like C:\\Users\\... or /home/user/...
6. Keep every replace_str under 800 characters.
   For long content, split into multiple edit_file actions.
7. NEVER use venv, virtualenv, or .\\venv\\Scripts\\activate.
   The container already has pip and Python globally.
8. NEVER run "cd someDir" as its own run_command.
   Use working_dir field instead.

═══════════════════════════════════════════════
TOOLS:
═══════════════════════════════════════════════
edit_file       {"filename": "app.py", "find_str": "", "replace_str": "...content..."}
                find_str="" → create/overwrite file
                find_str="old text" → replace first occurrence

run_command     {"command": "pip install fastapi uvicorn", "working_dir": "."}
                Runs in Linux Docker. Use linux commands only.

list_directory  {"path": "."}
read_file_content {"path": "app.py"}

═══════════════════════════════════════════════
VALID EXAMPLE:
═══════════════════════════════════════════════
[
  {"tool": "edit_file", "args": {"filename": "app.py", "find_str": "", "replace_str": "from fastapi import FastAPI\\napp = FastAPI()\\n\\n@app.get(\\"/\\")\\ndef root():\\n    return {\\"message\\": \\"hello\\"}\\n"}},
  {"tool": "run_command", "args": {"command": "pip install fastapi uvicorn", "working_dir": "."}}
]
"""

def node_writer(state: AgentState) -> AgentState:
    print("\n" + "═"*60 + "\n  ✍️   WRITER\n" + "═"*60)
    retry_section = ""
    if state.get("retry_count", 0) > 0:
        retry_section = (
            f"\n\nPREVIOUS ATTEMPT #{state['retry_count']} FAILED:\n"
            f"{state.get('last_result','unknown')}\n\n"
            "FIX CHECKLIST:\n"
            "- If 'invalid JSON': remove all # comments and // comments from your output.\n"
            "- If 'exit_code=1': the command failed — change it.\n"
            "- If 'not found': use find_str='' to create the file first.\n"
            "- Do NOT use venv, Windows paths, or absolute paths.\n"
            "- Do NOT repeat the same failing actions.\n"
        )
    response = _llm_invoke([
        SystemMessage(content=_WRITER_SYSTEM),
        HumanMessage(content=(
            f"Plan:\n{state['plan']}\n\n"
            f"Context:\n{state['context']}"
            f"{retry_section}\n\n"
            "Output the JSON array now. Nothing else."
        )),
    ])
    raw = _text(response).strip()
    print(f"\n{raw[:700]}{'...' if len(raw)>700 else ''}")
    return {**state, "code_action": raw,
            "messages": state["messages"] + [AIMessage(content=f"[WRITER]\n{raw}")]}

# ── EXECUTOR ──────────────────────────────────────────────────────────────────
def node_executor(state: AgentState, sandbox: DockerSandbox) -> AgentState:
    print("\n" + "═"*60 + "\n  ⚡  EXECUTOR\n" + "═"*60)
    workspace = Path(state["workspace"])
    actions   = _repair_json(state.get("code_action", "[]"))
    results: List[str] = []

    for i, action in enumerate(actions, 1):
        tool_name = action.get("tool", "")
        args      = action.get("args", {})

        if tool_name == "__json_error__":
            msg = f"[JSON_PARSE_ERROR] {args.get('error','')} | Raw: {args.get('raw','')}"
            print(f"\n  {msg}")
            results.append(msg)
            continue

        print(f"\n  [{i}/{len(actions)}] {tool_name}")

        if tool_name == "edit_file":
            fn  = args.get("filename", "")
            fs  = args.get("find_str", "")
            rs  = args.get("replace_str", "")
            print(f"  File   : {fn}")
            if fs: print(f"  Find   : {fs[:100]!r}")
            print(f"  Replace: {rs[:100]!r}")
            answer = input("\n  Approve file edit? (y/n): ").strip().lower()
            result = ("Skipped by user. [exit_code=0]" if answer != "y"
                      else tool_edit_file(workspace, fn, fs, rs))

        elif tool_name == "run_command":
            cmd = args.get("command", "")
            wd  = args.get("working_dir", ".")
            print(f"  Command  : {cmd}")
            print(f"  Directory: {wd}  (inside Docker)")
            answer = input("\n  Approve command? (y/n): ").strip().lower()
            result = ("Skipped by user. [exit_code=0]" if answer != "y"
                      else tool_run_command(sandbox, cmd, wd))

        elif tool_name == "list_directory":
            result = tool_list_directory(workspace, args.get("path", "."))

        elif tool_name == "read_file_content":
            result = tool_read_file(workspace, args.get("path", ""))

        else:
            result = f"[ERROR] Unknown tool: '{tool_name}'"

        print(f"\n  Result:\n{result}")
        results.append(f"[{tool_name}] {result}")

    combined = "\n\n".join(results) if results else "[INFO] No actions executed."
    return {**state, "last_result": combined,
            "messages": state["messages"] + [AIMessage(content=f"[EXECUTOR]\n{combined}")]}

# ── CRITIC ────────────────────────────────────────────────────────────────────
_CRITIC_SYSTEM = """\
You are a strict Critic. Evaluate execution results.

Rules:
- [exit_code=<non-zero>]       → RETRY
- [ERROR] or [JSON_PARSE_ERROR] → RETRY
- "Skipped by user" on important action → RETRY
- All [OK] and [exit_code=0]   → SUCCESS
- Files created with [OK]      → SUCCESS (even if no run_command)

Output format:
Line 1: SUCCESS or RETRY  (one word only)
Line 2: one sentence explanation.
"""

def node_critic(state: AgentState) -> AgentState:
    print("\n" + "═"*60 + "\n  🧐  CRITIC\n" + "═"*60)
    retry_count = state.get("retry_count", 0)
    if retry_count >= MAX_RETRIES:
        print(f"  ⚠️  Max retries ({MAX_RETRIES}) reached — forcing success.")
        return {**state, "status": "success"}
    response = _llm_invoke([
        SystemMessage(content=_CRITIC_SYSTEM),
        HumanMessage(content=(
            f"Plan:\n{state['plan']}\n\nExecution results:\n{state['last_result']}"
        )),
    ])
    verdict = _text(response).strip()
    first   = verdict.split()[0].upper() if verdict else "RETRY"
    status  = "success" if first == "SUCCESS" else "retry"
    print(f"\n  {'✅' if status=='success' else '🔄'}  {verdict}")
    return {**state, "status": status,
            "retry_count": retry_count + (1 if status == "retry" else 0),
            "messages": state["messages"] + [AIMessage(content=f"[CRITIC] {verdict}")]}

# ── FINALIZER ─────────────────────────────────────────────────────────────────
def node_finalizer(state: AgentState) -> AgentState:
    print("\n" + "═"*60 + "\n  🏁  FINALIZER\n" + "═"*60)
    response = _llm_invoke([
        SystemMessage(content=(
            "You are the Finalizer. The task is complete.\n"
            "Write a clear summary:\n"
            "1. What was accomplished\n"
            "2. Files created/modified (with paths)\n"
            "3. Commands run and outcomes\n"
            "4. Exact commands to run/test the result\n"
            "5. Next steps if any\n\n"
            "Be specific. Use actual file names and commands."
        )),
        HumanMessage(content=(
            f"Request:\n{state['user_request']}\n\n"
            f"Plan:\n{state['plan']}\n\n"
            f"Results:\n{state['last_result']}"
        )),
    ])
    final = _text(response)
    print("\n" + "═"*60 + "\n  ✅  DONE\n" + "═"*60 + f"\n\n{final}")
    return {**state, "final_answer": final,
            "messages": state["messages"] + [AIMessage(content=final)]}

# ── ROUTING ───────────────────────────────────────────────────────────────────
def route_after_critic(state: AgentState) -> Literal["node_writer", "node_finalizer"]:
    return "node_finalizer" if state["status"] == "success" else "node_writer"