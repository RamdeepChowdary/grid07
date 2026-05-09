"""
main.py
-------
Master runner for the Grid07 AI assignment.
Runs all three phases and writes execution_logs.md.

Usage:
  python main.py
"""

import sys, os, io
from datetime import datetime


class Tee:
    """Writes to both stdout and a string buffer simultaneously."""
    def __init__(self):
        self.buf     = io.StringIO()
        self._stdout = sys.stdout

    def write(self, msg):
        self._stdout.write(msg)
        self.buf.write(msg)

    def flush(self):
        self._stdout.flush()

    def getvalue(self):
        return self.buf.getvalue()


def run_all():
    tee = Tee()
    sys.stdout = tee

    print("=" * 70)
    print("  GRID07 AI ASSIGNMENT — Full Execution")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Phase 1
    try:
        from phase1.router import demo as phase1_demo
        phase1_demo()
    except Exception as e:
        print(f"\n[ERROR Phase 1]: {e}")
        import traceback; traceback.print_exc()

    # Phase 2
    try:
        from phase2.content_engine import demo as phase2_demo
        phase2_demo()
    except Exception as e:
        print(f"\n[ERROR Phase 2]: {e}")
        import traceback; traceback.print_exc()

    # Phase 3
    try:
        from phase3.combat_engine import demo as phase3_demo
        phase3_demo()
    except Exception as e:
        print(f"\n[ERROR Phase 3]: {e}")
        import traceback; traceback.print_exc()

    sys.stdout = tee._stdout
    logs = tee.getvalue()

    log_path = os.path.join(os.path.dirname(__file__), "execution_logs.md")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("# Grid07 — Execution Logs\n\n")
        f.write(f"**Run date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("```\n")
        f.write(logs)
        f.write("\n```\n")

    print(f"\n✅ Execution logs saved to: {log_path}")


if __name__ == "__main__":
    run_all()