#!/usr/bin/env python3
# main.py
# ══════════════════════════════════════════════════════
# Entry point — this is what you run from the terminal
#
# Usage:
#   python main.py                        ← prompts for directory
#   python main.py --workspace ./myapp    ← specifies directory directly
#   python main.py --workspace ./myapp --no-sandbox  ← runs without Docker
# ══════════════════════════════════════════════════════

import argparse
import io
import signal
import sys
import uuid
from pathlib import Path

# ── Fix Windows terminal encoding (box-drawing chars) ──
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from agent.graph import run_agent
from sandbx.docker_runner import DockerSandbox


# ══════════════════════════════════════════════════════
# CLI Arguments Setup
# ══════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="🤖 Multi-Agent Coding Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --workspace ./my-project
  python main.py --workspace ./my-project --no-sandbox
        """,
    )
    parser.add_argument(
        "--workspace", "-w",
        type=str,
        default=None,
        help="The directory to work in (default: prompts you)",
    )
    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="Run commands directly on your machine without Docker (⚠️ less secure)",
    )
    return parser.parse_args()


# ══════════════════════════════════════════════════════
# Sandbox without Docker (for development and testing)
# ══════════════════════════════════════════════════════

class LocalRunner:
    """
    Same interface as DockerSandbox but executes directly on the machine.
    Use this only for testing — no isolation.
    """
    import subprocess as _sp

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def start(self):
        print("  [local] ⚠️  No Docker — commands will be executed directly on your machine")

    def run(self, command: str) -> tuple[str, int]:
        import subprocess
        proc = subprocess.run(
            command, shell=True,
            capture_output=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(self.workspace),
        )
        return proc.stdout, proc.returncode

    def stop(self):
        pass


# ══════════════════════════════════════════════════════
# Main Loop
# ══════════════════════════════════════════════════════

def main():
    args = parse_args()

    # ── Header ──
    print("\n" + "═" * 55)
    print("  🤖 Multi-Agent Coding Assistant")
    print("  Model: Ollama → qwen2.5-coder:7b")
    print("═" * 55)

    # ── Set Workspace ──
    if args.workspace:
        workspace_path = Path(args.workspace).resolve()
    else:
        print("\n📁 Enter the path of the directory you want to work in:")
        print("   (Press Enter for the current directory)")
        user_input = input("   > ").strip()
        workspace_path = Path(user_input).resolve() if user_input else Path(".").resolve()

    # Ensure directory exists
    if not workspace_path.exists():
        print(f"\n  ⚠️  Directory does not exist: {workspace_path}")
        print("  Do you want to create it? (y/n): ", end="")
        if input().strip().lower() == "y":
            workspace_path.mkdir(parents=True)
            print(f"  ✓ Created: {workspace_path}")
        else:
            sys.exit(1)

    print(f"\n  📁 Workspace: {workspace_path}")

    # ── Setup Sandbox ──
    if args.no_sandbox:
        runner = LocalRunner(workspace_path)
    else:
        # Unique name for the container to avoid conflicts
        container_name = f"coding-agent-{uuid.uuid4().hex[:8]}"
        runner = DockerSandbox(workspace_path, container_name)

    runner.start()

    # ── Cleanup on exit ──
    def cleanup(sig=None, frame=None):
        print("\n\n  Shutting down...")
        runner.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("\n  Type your request or 'exit' to quit")
    print("  ─" * 27)

    # ── Chat Loop ──
    while True:
        print()
        try:
            user_input = input("  You: ").strip()
        except EOFError:
            cleanup()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            cleanup()

        # Run the agent
        run_agent(
            user_request   = user_input,
            workspace_path = str(workspace_path),
            sandbox        = runner,
        )


if __name__ == "__main__":
    main()
