# sandbox/docker_runner.py
# ══════════════════════════════════════════════════════
# Responsible for executing commands inside an isolated Docker container
#
# Concept:
#   - We have one container per session
#   - All commands run inside it
#   - Your real directory is bound (bind mount) to /workspace inside the container
#   - Meaning: modifications to files appear immediately on your machine
#   - But if a command breaks something, it only affects the container, not your machine
# ══════════════════════════════════════════════════════

import subprocess
import threading
from pathlib import Path

from config import (
    SANDBOX_CPUS,
    SANDBOX_IMAGE,
    SANDBOX_MEMORY,
    SANDBOX_TIMEOUT,
    WORKSPACE_IN_CONTAINER,
)


class DockerSandbox:
    """
    Represents a single Docker container tied to a specific workspace.

    The container is created once and stays running for the duration of the session.
    Every command executes inside it via `docker exec`.
    """

    def __init__(self, workspace_path: Path, container_name: str):
        """
        workspace_path  : Real folder on your machine
        container_name  : Unique name for the container (used for docker exec)
        """
        self.workspace    = workspace_path.resolve()
        self.name         = container_name
        self._started     = False

    # ─────────────────────────────────────────────────
    # Container Start
    # ─────────────────────────────────────────────────
    def start(self):
        """
        Start the container if it's not running.
        We use `docker run -d` to run it in the background.
        """
        if self._is_running():
            self._started = True
            return

        cmd = [
            "docker", "run",
            "--detach",                    # Run in the background
            "--name", self.name,
            "--rm",                        # Remove automatically when stopped
            "--memory", SANDBOX_MEMORY,    # RAM limit
            "--cpus",   SANDBOX_CPUS,      # CPU limit
            "--network", "bridge",         # Limited network — can download packages
                                           # If you write "none" it will be completely isolated
            # ── The important part: binding your folder to the container ──
            "--volume", f"{self.workspace}:{WORKSPACE_IN_CONTAINER}",
            #            ↑ Your real folder   ↑ Its name inside the container
            "--workdir", WORKSPACE_IN_CONTAINER,
            SANDBOX_IMAGE,
            "sleep", "infinity",           # Keep it awake waiting for commands
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to start container:\n{result.stderr}"
            )

        self._started = True
        print(f"  [sandbox] ✓ Container '{self.name}' is running")

    # ─────────────────────────────────────────────────
    # Execute Command
    # ─────────────────────────────────────────────────
    def run(self, command: str) -> tuple[str, int]:
        """
        Execute a shell command inside the container.
        Returns (output, exit_code).

        `docker exec` = "execute command inside a running container"
        """
        if not self._started:
            self.start()

        cmd = [
            "docker", "exec",
            self.name,          # Container name
            "sh", "-c", command # The command itself
        ]

        # We use threading.Timer to stop the command if it takes too long
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr with stdout to see errors
            text=True,
        )

        timed_out = False

        def _kill():
            nonlocal timed_out
            timed_out = True
            proc.kill()

        timer = threading.Timer(SANDBOX_TIMEOUT, _kill)
        timer.start()
        try:
            output, _ = proc.communicate()
        finally:
            timer.cancel()

        if timed_out:
            return f"[timeout] Command took more than {SANDBOX_TIMEOUT} seconds", 1

        # If output is too large, truncate it
        if len(output) > 3000:
            output = output[:1500] + "\n\n[...truncated...]\n\n" + output[-1500:]

        return output, proc.returncode

    # ─────────────────────────────────────────────────
    # Container Stop
    # ─────────────────────────────────────────────────
    def stop(self):
        """Stop the container (it will be deleted automatically due to --rm)."""
        subprocess.run(
            ["docker", "stop", self.name],
            capture_output=True,
        )
        self._started = False
        print(f"  [sandbox] Container '{self.name}' stopped")

    # ─────────────────────────────────────────────────
    # Helper
    # ─────────────────────────────────────────────────
    def _is_running(self) -> bool:
        """Check if the container is actually running."""
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", self.name],
            capture_output=True, text=True,
        )
        return result.stdout.strip() == "true"