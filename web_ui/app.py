from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import subprocess
import os
import threading
import sys

app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app)

# Load system prompt
SYSTEM_PROMPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'terminal', 'system.prompt.md'))
if os.path.exists(SYSTEM_PROMPT_PATH):
    with open(SYSTEM_PROMPT_PATH, 'r') as f:
        SYSTEM_PROMPT = f.read()
else:
    SYSTEM_PROMPT = "Default REDACTED Swarm prompt."

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('output', {'data': 'Welcome to REDACTED Swarm Web Terminal.'})

# Repo root (parent of web_ui) so run_with_ollama sees terminal/ and agents/
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RUN_WITH_OLLAMA = os.path.join(REPO_ROOT, 'python', 'run_with_ollama.py')
DEFAULT_AGENT = os.path.join(REPO_ROOT, 'agents', 'RedactedIntern.character.json')

@socketio.on('command')
def handle_command(data):
    cmd = data.get('cmd', '').strip()
    if not cmd:
        return

    args = cmd.split()
    full_cmd = [sys.executable, RUN_WITH_OLLAMA, '--agent', DEFAULT_AGENT]
    if args and not args[0].startswith('-'):
        full_cmd.extend(args)  # e.g. extra --model qwen:2.5

    def run_process():
        try:
            process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=REPO_ROOT)
            for line in iter(process.stdout.readline, ''):
                emit('output', {'data': line.strip()})
            process.stdout.close()
            stderr = process.stderr.read().strip()
            if stderr:
                emit('output', {'data': f"Error: {stderr}"})
            process.wait()
        except Exception as e:
            emit('output', {'data': f"Error: {str(e)}"})

    threading.Thread(target=run_process).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
