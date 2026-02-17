#!/usr/bin/env python3
"""
REDACTED AI Swarm — unified run entry point.
Run from repo root:  python run.py

Tries, in order:
  1. Cloud terminal (if XAI_API_KEY or OPENAI_API_KEY is set)
  2. Ollama terminal (if Ollama is running on localhost:11434)
  3. Prints setup instructions and exits
"""

import os
import sys
import subprocess

# Ensure we're in repo root (directory containing this script)
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO_ROOT)

# Load .env from repo root
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(REPO_ROOT, ".env"))
except ImportError:
    pass

PYTHON_DIR = os.path.join(REPO_ROOT, "python")
CLOUD_SCRIPT = os.path.join(PYTHON_DIR, "redacted_terminal_cloud.py")
OLLAMA_SCRIPT = os.path.join(PYTHON_DIR, "run_with_ollama.py")
DEFAULT_AGENT = "agents/RedactedIntern.character.json"


def _ollama_available():
    """Return True if Ollama is running and reachable."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _run_cloud():
    """Run the cloud LLM terminal (Grok/xAI or OpenAI)."""
    return subprocess.run(
        [sys.executable, CLOUD_SCRIPT],
        cwd=REPO_ROOT,
    ).returncode


def _run_ollama():
    """Run the Ollama terminal."""
    agent = DEFAULT_AGENT
    if not os.path.exists(os.path.join(REPO_ROOT, agent)):
        agent = "agents/default.character.json"
    return subprocess.run(
        [sys.executable, OLLAMA_SCRIPT, "--agent", agent],
        cwd=REPO_ROOT,
    ).returncode


def main():
    # 1. Prefer cloud if any supported key is set
    llm_provider = (os.getenv("LLM_PROVIDER") or "grok").lower()
    if llm_provider in ("grok", "xai") and os.getenv("XAI_API_KEY"):
        sys.exit(_run_cloud())
    if os.getenv("OPENAI_API_KEY"):
        sys.exit(_run_cloud())
    if os.getenv("GROQ_API_KEY") and llm_provider == "groq":
        sys.exit(_run_cloud())
    if os.getenv("ANTHROPIC_API_KEY") and llm_provider == "anthropic":
        sys.exit(_run_cloud())

    # 2. Fallback to Ollama if running
    if _ollama_available():
        print("[run.py] Using Ollama (cloud API keys not set).\n")
        sys.exit(_run_ollama())

    # 3. Nothing available
    print("REDACTED Terminal — no backend available.")
    print()
    print("Choose one:")
    print("  • Cloud: Set XAI_API_KEY (or OPENAI_API_KEY) in .env or environment, then run again.")
    print("  • Local: Install and start Ollama (https://ollama.com), then run again.")
    print()
    print("Or run explicitly:")
    print("  python python/redacted_terminal_cloud.py   # needs XAI_API_KEY or OPENAI_API_KEY")
    print("  python python/run_with_ollama.py --agent agents/RedactedIntern.character.json   # needs Ollama")
    sys.exit(1)


if __name__ == "__main__":
    main()
