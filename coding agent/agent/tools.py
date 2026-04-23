# agent/tools.py
# =============================================================================
# Tool implementations called by the Executor node.
#
# Design:
#   edit_file        → writes directly to real workspace (Python I/O).
#                      Docker container sees the same files via bind-mount.
#   run_command      → executes inside the Docker sandbox (isolated).
#   list_directory   → reads real workspace (read-only, no side-effects).
#   read_file        → reads real workspace (read-only, no side-effects).
#
# Every function returns a plain string. Never raises to the caller.
# The Critic reads that string to decide SUCCESS / RETRY.
# =============================================================================

from pathlib import Path

from sandbx.docker_runner import DockerSandbox

_MAX_OUTPUT_CHARS = 4000


# =============================================================================
# Internal helpers
# =============================================================================

def _safe_path(workspace: Path, requested: str) -> Path:
    """
    Resolve `requested` relative to `workspace` and verify it stays inside.

    Prevents path-traversal attacks:
        "../../etc/passwd"  →  resolves outside workspace  →  PermissionError

    Also strips Windows drive letters and normalises backslashes so the
    agent works correctly regardless of the OS the LLM was trained on.
    """
    if not requested or not requested.strip():
        raise ValueError("Path argument must not be empty.")

    # Normalise: backslashes → forward slashes, strip leading slashes
    normalised = requested.replace("\\", "/")
    # Strip Windows drive letters (C:/, D:/, etc.)
    if len(normalised) >= 2 and normalised[1] == ":":
        normalised = normalised[2:]
    normalised = normalised.strip("/")

    target = (workspace / normalised).resolve()

    try:
        target.relative_to(workspace.resolve())
    except ValueError:
        raise PermissionError(
            f"[SECURITY] '{requested}' resolves outside the workspace "
            f"boundary ({workspace}). Denied."
        )
    return target


def _clip(text: str, label: str = "output") -> str:
    """Clip long strings to avoid flooding the LLM context window."""
    if len(text) <= _MAX_OUTPUT_CHARS:
        return text
    half = _MAX_OUTPUT_CHARS // 2
    return (
        text[:half]
        + f"\n\n[... {label} clipped — {len(text):,} chars total ...]\n\n"
        + text[-half:]
    )


# =============================================================================
# tool_edit_file
# =============================================================================

def tool_edit_file(workspace: Path, filename: str, find_str: str, replace_str: str) -> str:
    """
    Create or patch a file inside the workspace.

    find_str == ""  → create / overwrite entire file with replace_str.
    find_str != ""  → replace only the FIRST occurrence.

    Always returns a string. Never raises.
    """
    try:
        target = _safe_path(workspace, filename)
    except (PermissionError, ValueError) as exc:
        return f"[ERROR] {exc}"

    try:
        if find_str == "":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(replace_str, encoding="utf-8")
            return f"[OK] Created/overwritten: {filename} ({len(replace_str):,} chars)"

        if not target.exists():
            return (
                f"[ERROR] File not found: {filename}. "
                "Hint: use find_str='' to create it first."
            )
        if not target.is_file():
            return f"[ERROR] '{filename}' is a directory, not a file."

        content = target.read_text(encoding="utf-8")
        if find_str not in content:
            preview = content[:200].replace("\n", "\\n")
            return (
                f"[ERROR] find_str not found in '{filename}'. "
                f"File starts with: {preview!r}"
            )

        count = content.count(find_str)
        target.write_text(content.replace(find_str, replace_str, 1), encoding="utf-8")
        note = f" ({count} occurrences; only first replaced)" if count > 1 else ""
        return f"[OK] Edited: {filename}{note}"

    except PermissionError:
        return f"[ERROR] Permission denied: {filename}"
    except OSError as exc:
        return f"[ERROR] OS error on '{filename}': {exc}"


# =============================================================================
# tool_run_command
# =============================================================================

def tool_run_command(sandbox: DockerSandbox, command: str, working_dir: str = ".") -> str:
    """
    Run a shell command inside the Docker sandbox.

    working_dir is relative to /workspace inside the container.
    Absolute paths and Windows-style paths are normalised automatically.
    """
    if not command or not command.strip():
        return "[ERROR] Empty command. [exit_code=1]"

    # Normalise working_dir: strip absolute path prefixes so it is always
    # relative to /workspace inside the container.
    wd = working_dir.strip().replace("\\", "/")
    if wd in (".", "", "/workspace", "/workspace/"):
        full_cmd = command
    else:
        # Strip Windows drive letters
        if len(wd) >= 2 and wd[1] == ":":
            wd = wd[2:]
        # If LLM gave full path containing /workspace, extract the tail
        if "/workspace/" in wd:
            wd = wd.split("/workspace/", 1)[-1]
        wd = wd.strip("/")
        full_cmd = f"cd /workspace/{wd} && {command}" if wd else command

    output, exit_code = sandbox.run(full_cmd)
    output = _clip(output, label="command output")
    return f"{output}\n[exit_code={exit_code}]"


# =============================================================================
# tool_list_directory
# =============================================================================

def tool_list_directory(workspace: Path, path: str = ".") -> str:
    """List directory contents. Dirs before files, both sorted."""
    try:
        target = _safe_path(workspace, path)
    except (PermissionError, ValueError) as exc:
        return f"[ERROR] {exc}"

    if not target.exists():
        return f"[ERROR] Directory not found: '{path}'"
    if not target.is_dir():
        return f"[ERROR] '{path}' is a file, not a directory."

    try:
        items = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return f"[ERROR] Permission denied reading: '{path}'"

    if not items:
        return f"[OK] '{path}' is empty."

    lines = [f"[OK] Contents of '{path}':"]
    for item in items:
        if item.is_dir():
            lines.append(f"  DIR   {item.name}/")
        else:
            lines.append(f"  FILE  {item.name}  ({item.stat().st_size:,} bytes)")
    return "\n".join(lines)


# =============================================================================
# tool_read_file
# =============================================================================

def tool_read_file(workspace: Path, path: str) -> str:
    """Read a file's text content. Clips large files. Returns error strings on failure."""
    try:
        target = _safe_path(workspace, path)
    except (PermissionError, ValueError) as exc:
        return f"[ERROR] {exc}"

    if not target.exists():
        return f"[ERROR] File not found: '{path}'"
    if not target.is_file():
        return f"[ERROR] '{path}' is a directory."

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return (
            f"[ERROR] '{path}' is binary (not UTF-8 text). "
            "Use run_command with 'file' or 'xxd' to inspect."
        )
    except PermissionError:
        return f"[ERROR] Permission denied: '{path}'"
    except OSError as exc:
        return f"[ERROR] OS error reading '{path}': {exc}"

    header = f"[OK] {path} ({len(content):,} chars)\n{'─'*40}\n"
    return header + _clip(content, label=f"{path} content")