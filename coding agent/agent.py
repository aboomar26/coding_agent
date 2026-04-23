#!/usr/bin/env python3
# agent.py
# ══════════════════════════════════════════════════════
# نقطة الدخول — اللي بتشغّله من الترمينال
#
# الاستخدام:
#   python agent.py                        ← يسألك عن المجلد
#   python agent.py --workspace ./myapp    ← مجلد محدد مباشرة
#   python agent.py --workspace ./myapp --no-sandbox  ← بدون Docker
# ══════════════════════════════════════════════════════

import argparse
import signal
import sys
import uuid
from pathlib import Path

from agent.graph import run_agent
from sandbx.docker_runner import DockerSandbox


# ══════════════════════════════════════════════════════
# إعداد الـ CLI arguments
# ══════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="🤖 Multi-Agent Coding Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  python agent.py
  python agent.py --workspace ./my-project
  python agent.py --workspace ./my-project --no-sandbox
        """,
    )
    parser.add_argument(
        "--workspace", "-w",
        type=str,
        default=None,
        help="المجلد اللي تشتغل عليه (default: يسألك)",
    )
    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="شغّل الأوامر على جهازك مباشرة بدون Docker (⚠️ أقل أمان)",
    )
    return parser.parse_args()


# ══════════════════════════════════════════════════════
# Sandbox بدون Docker (للتطوير والاختبار)
# ══════════════════════════════════════════════════════

class LocalRunner:
    """
    نفس واجهة DockerSandbox بس بينفّذ على الجهاز مباشرة.
    استخدم ده بس للاختبار — مفيش عزل.
    """
    import subprocess as _sp
    
    def __init__(self, workspace: Path):
        self.workspace = workspace

    def start(self):
        print("  [local] ⚠️  بدون Docker — الأوامر بتتنفذ مباشرة على جهازك")

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
# الـ Main Loop
# ══════════════════════════════════════════════════════

def main():
    args = parse_args()

    # ── Header ──
    print("\n" + "═" * 55)
    print("  🤖 Multi-Agent Coding Assistant")
    print("  Model: vLLM → qwen2.5-coder")
    print("═" * 55)

    # ── تحديد الـ Workspace ──
    if args.workspace:
        workspace_path = Path(args.workspace).resolve()
    else:
        print("\n📁 أدخل مسار المجلد اللي تبي تشتغل عليه:")
        print("   (اضغط Enter للمجلد الحالي)")
        user_input = input("   > ").strip()
        workspace_path = Path(user_input).resolve() if user_input else Path(".").resolve()

    # تأكد إن المجلد موجود
    if not workspace_path.exists():
        print(f"\n  ⚠️  المجلد مش موجود: {workspace_path}")
        print("  هل تبي أنشئه؟ (y/n): ", end="")
        if input().strip().lower() == "y":
            workspace_path.mkdir(parents=True)
            print(f"  ✓ تم إنشاء: {workspace_path}")
        else:
            sys.exit(1)

    print(f"\n  📁 Workspace: {workspace_path}")

    # ── إعداد الـ Sandbox ──
    if args.no_sandbox:
        runner = LocalRunner(workspace_path)
    else:
        # اسم فريد للـ container عشان محدش يتعارض مع تاني
        container_name = f"coding-agent-{uuid.uuid4().hex[:8]}"
        runner = DockerSandbox(workspace_path, container_name)

    runner.start()

    # ── Cleanup عند الخروج ──
    # لو الUser ضغط Ctrl+C، نوقف الـ container بشكل نظيف
    def cleanup(sig=None, frame=None):
        print("\n\n  جاري الإغلاق...")
        runner.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("\n  اكتب طلبك أو 'exit' للخروج")
    print("  ─" * 27)

    # ── Loop المحادثة ──
    while True:
        print()
        try:
            user_input = input("  أنت: ").strip()
        except EOFError:
            cleanup()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "خروج"):
            cleanup()

        # شغّل الأيجنت
        run_agent(
            user_request   = user_input,
            workspace_path = str(workspace_path),
            sandbox        = runner,
        )


if __name__ == "__main__":
    main()