#!/usr/bin/env python3
"""
Main entrypoint for deploying the REDACTED AI Swarm worker on Railway.
"""
import os
import subprocess
import sys

# --- Configuration ---
DEFAULT_AGENT_PATH = "agents/RedactedIntern.character.json"
WORKER_SCRIPT = "python/summon_agent.py"

def main():
    """
    Builds and executes the command to run the swarm worker.
    """
    repo_root = os.path.dirname(os.path.abspath(__file__))
    agent_path = os.getenv("AGENT_PATH", DEFAULT_AGENT_PATH)
    script_path = os.path.join(repo_root, WORKER_SCRIPT)
    full_agent_path = os.path.join(repo_root, agent_path)

    # --- Validation ---
    if not os.path.exists(script_path):
        print(f"Error: Worker script not found at '{script_path}'")
        sys.exit(1)

    if not os.path.exists(full_agent_path):
        print(f"Error: Agent file not found at '{full_agent_path}'")
        sys.exit(1)

    # --- Build Command ---
    # Base command to run the agent in persistent mode
    cmd = [sys.executable, script_path, "--agent", agent_path, "--mode", "persistent"]

    # --- Create a custom environment for the subprocess ---
    # We will explicitly disable the Ollama check to force the LLM fallback.
    env = os.environ.copy()
    env["OLLAMA_HOST"] = "disable"  # This non-host string will cause the Ollama check to fail immediately.
    print(f"[main.py] Forcing Ollama check to fail to trigger LLM fallback.")

    # --- Execution ---
    print(f"[main.py] Starting swarm worker...")
    print(f"[main.py] Executing command: {' '.join(cmd)}")

    try:
        # Pass the custom 'env' to subprocess.run
        result = subprocess.run(cmd, check=True, env=env)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"[main.py] Worker script exited with error: {e}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"[main.py] Error: The script '{script_path}' was not found or is not executable.")
        sys.exit(1)


if __name__ == "__main__":
    main()
