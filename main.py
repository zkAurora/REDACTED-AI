#!/usr/bin/env python3
"""
Main entrypoint for deploying the REDACTED AI Swarm worker on Railway.

This script serves as the start command for a single-service deployment.
It executes the `summon_agent.py` script in persistent mode, using a
default agent and an optional Ollama host.

Railway will automatically detect and run this file.
"""
import os
import subprocess
import sys

# --- Configuration ---
# The agent to run by default. Can be overridden with the AGENT_PATH env var.
DEFAULT_AGENT_PATH = "agents/RedactedIntern.character.json"
# The Python script that runs the agent
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

    # Add Ollama host if specified (e.g., in Railway dashboard or railway.toml)
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        cmd.extend(["--ollama-host", ollama_host])
        print(f"[main.py] OLLAMA_HOST detected: {ollama_host}")

    # --- Execution ---
    print(f"[main.py] Starting swarm worker...")
    print(f"[main.py] Executing command: {' '.join(cmd)}")

    # Use subprocess to run the target script.
    # This ensures the Railway process is correctly attached.
    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"[main.py] Worker script exited with error: {e}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"[main.py] Error: The script '{script_path}' was not found or is not executable.")
        print("Please ensure the repository structure is correct.")
        sys.exit(1)


if __name__ == "__main__":
    main()
