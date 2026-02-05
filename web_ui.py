"""
ACE Songwriter Web UI
======================
A beautiful web interface for the autonomous songwriting agent.

Run with: python web_ui.py
Then open: http://localhost:5000
"""

import os
import sys
import json
import threading
import queue
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ace_framework import ACEAgent, NorthboundBus, SouthboundBus, LayerID
from layers import (
    AspirationalLayer, GlobalStrategyLayer, AgentModelLayer,
    ExecutiveFunctionLayer, CognitiveControlLayer, TaskProsecutionLayer
)
from oversight_board import create_songwriter_sob, Verdict

# Try to import Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

app = Flask(__name__)

# Global state for progress tracking
progress_queue = queue.Queue()
current_job = None


class WebACESongwriter(ACEAgent):
    """ACE Songwriter with web UI progress reporting."""
    
    def __init__(self, api_key: str = None, enable_oversight: bool = True):
        super().__init__(api_key=api_key, verbose=True, output_dir=None)
        self.enable_oversight = enable_oversight
        self.oversight_board = create_songwriter_sob(llm_model=self.llm, verbose=True) if enable_oversight else None
        self._setup_layers()
        
    def _setup_layers(self):
        """Initialize all 6 cognitive layers."""
        layers_config = [
            (AspirationalLayer, "Aspirational"),
            (GlobalStrategyLayer, "Global Strategy"),
            (AgentModelLayer, "Agent Model"),
            (ExecutiveFunctionLayer, "Executive Function"),
            (CognitiveControlLayer, "Cognitive Control"),
            (TaskProsecutionLayer, "Task Prosecution"),
        ]
        
        for LayerClass, name in layers_config:
            kwargs = {
                "northbound_bus": self.northbound,
                "southbound_bus": self.southbound,
                "llm_model": self.llm,
                "verbose": True
            }
            if LayerClass == TaskProsecutionLayer:
                kwargs["output_dir"] = str(self.output_dir)
            
            self.register_layer(LayerClass(**kwargs))
            progress_queue.put({
                "type": "layer_init",
                "layer": name,
                "message": f"✅ Initialized {name} layer"
            })


def generate_song_async(transcription: str, circumstance: str, api_key: str, enable_oversight: bool, max_cycles: int):
    """Generate song in background thread."""
    global current_job
    
    try:
        progress_queue.put({"type": "status", "message": "🚀 Starting ACE Songwriter..."})
        
        # Create agent
        agent = WebACESongwriter(api_key=api_key, enable_oversight=enable_oversight)
        
        progress_queue.put({
            "type": "status", 
            "message": f"🧠 Agent ready with {len(agent.layers)} layers"
        })
        
        # Prepare input
        input_data = {
            "transcription": transcription,
            "circumstance": circumstance,
            "description": f"Write a song based on: {(transcription or circumstance or 'general theme')[:100]}..."
        }
        
        progress_queue.put({
            "type": "input",
            "message": f"📝 Input received: {input_data['description'][:80]}..."
        })
        
        # Run the agent
        progress_queue.put({"type": "status", "message": f"🔄 Starting {max_cycles} cognitive cycles..."})
        
        result = agent.run(input_data, max_cycles=max_cycles)
        
        # SOB Review
        if agent.oversight_board and result.get("song_parts"):
            progress_queue.put({"type": "status", "message": "⚖️ Running Supreme Oversight Board review..."})
            song_content = "\n\n".join([f"{k.upper()}:\n{v}" for k, v in result["song_parts"].items()])
            review = agent.oversight_board.review(song_content, context={})
            result["sob_review"] = {
                "verdict": review["overall_verdict"].value,
                "approved": review["approved_count"],
                "total": review["total_personas"]
            }
            progress_queue.put({
                "type": "sob_review",
                "verdict": review["overall_verdict"].value,
                "approved": review["approved_count"],
                "total": review["total_personas"]
            })
        
        # Send completion
        progress_queue.put({
            "type": "complete",
            "result": {
                "status": result.get("status", "unknown"),
                "output_file": result.get("output_file", ""),
                "song_parts": result.get("song_parts", {}),
                "sob_review": result.get("sob_review", {})
            }
        })
        
    except Exception as e:
        progress_queue.put({
            "type": "error",
            "message": f"❌ Error: {str(e)}"
        })
    finally:
        current_job = None


@app.route('/')
def index():
    """Render the main UI."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Start song generation."""
    global current_job
    
    if current_job is not None:
        return jsonify({"error": "A job is already running"}), 400
    
    data = request.json
    transcription = data.get('transcription', '')
    circumstance = data.get('circumstance', '')
    api_key = data.get('api_key', '') or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    enable_oversight = data.get('enable_oversight', True)
    max_cycles = int(data.get('max_cycles', 12))
    
    if not api_key:
        return jsonify({"error": "No API key provided"}), 400
    
    if not transcription and not circumstance:
        return jsonify({"error": "Please provide transcription or circumstance"}), 400
    
    # Clear queue
    while not progress_queue.empty():
        progress_queue.get()
    
    # Start background thread
    current_job = threading.Thread(
        target=generate_song_async,
        args=(transcription, circumstance, api_key, enable_oversight, max_cycles)
    )
    current_job.start()
    
    return jsonify({"status": "started"})


@app.route('/progress')
def progress():
    """SSE endpoint for real-time progress updates."""
    def generate():
        while True:
            try:
                msg = progress_queue.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") in ["complete", "error"]:
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/status')
def status():
    """Check if a job is running."""
    return jsonify({
        "running": current_job is not None and current_job.is_alive(),
        "has_gemini": HAS_GEMINI
    })


# Create templates directory and HTML
def create_templates():
    """Create the HTML template."""
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACE Songwriter</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.3);
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
            --border: #27272a;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Animated background */
        .bg-glow {
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 40%);
            animation: rotate 30s linear infinite;
            z-index: -1;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        h1 {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .frameworks {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        
        .badge {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            padding: 0.4rem 1rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 900px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: var(--accent);
            box-shadow: 0 0 30px var(--accent-glow);
        }
        
        .card-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .form-group {
            margin-bottom: 1.25rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        input, textarea, select {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 1rem;
            transition: all 0.2s;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .checkbox-group label {
            margin: 0;
            cursor: pointer;
        }
        
        .btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, var(--accent), #8b5cf6);
            border: none;
            border-radius: 8px;
            color: white;
            font-family: inherit;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 40px var(--accent-glow);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .progress-log {
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1rem;
            height: 300px;
            overflow-y: auto;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.85rem;
            line-height: 1.6;
        }
        
        .log-entry {
            padding: 0.25rem 0;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .log-entry.error { color: var(--error); }
        .log-entry.success { color: var(--success); }
        .log-entry.warning { color: var(--warning); }
        
        .output-section {
            margin-top: 2rem;
        }
        
        .song-output {
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1.5rem;
            white-space: pre-wrap;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9rem;
            line-height: 1.8;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .sob-panel {
            margin-top: 1rem;
            padding: 1rem;
            background: var(--bg-tertiary);
            border-radius: 8px;
            border-left: 4px solid var(--accent);
        }
        
        .sob-verdict {
            font-size: 1.2rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .sob-verdict.approved { color: var(--success); }
        .sob-verdict.needs_revision { color: var(--warning); }
        .sob-verdict.rejected { color: var(--error); }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid transparent;
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="bg-glow"></div>
    
    <div class="container">
        <header>
            <h1>🎵 ACE Songwriter</h1>
            <p class="subtitle">Autonomous Cognitive Songwriting Agent</p>
            <div class="frameworks">
                <span class="badge">🧠 ACE Framework</span>
                <span class="badge">⚖️ GATO Imperatives</span>
                <span class="badge">🔧 Agent Swarm</span>
                <span class="badge">✨ Gemini 3.0</span>
            </div>
        </header>
        
        <div class="main-grid">
            <div class="input-panel">
                <div class="card">
                    <h2 class="card-title">📝 Input</h2>
                    
                    <div class="form-group">
                        <label for="apiKey">Gemini API Key</label>
                        <input type="password" id="apiKey" placeholder="Enter your API key...">
                    </div>
                    
                    <div class="form-group">
                        <label for="transcription">Transcription (optional)</label>
                        <textarea id="transcription" placeholder="Paste a transcription to base the song on..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="circumstance">Circumstance / Theme</label>
                        <input type="text" id="circumstance" placeholder="e.g., A love song about distant fandom">
                    </div>
                    
                    <div class="form-group">
                        <label for="maxCycles">Max Cognitive Cycles</label>
                        <select id="maxCycles">
                            <option value="8">8 cycles (Fast)</option>
                            <option value="12" selected>12 cycles (Balanced)</option>
                            <option value="15">15 cycles (Thorough)</option>
                        </select>
                    </div>
                    
                    <div class="form-group checkbox-group">
                        <input type="checkbox" id="enableOversight" checked>
                        <label for="enableOversight">Enable Supreme Oversight Board Review</label>
                    </div>
                    
                    <button class="btn" id="generateBtn" onclick="startGeneration()">
                        <span id="btnText">🎤 Generate Song</span>
                        <span id="btnSpinner" class="loading-spinner hidden"></span>
                    </button>
                </div>
            </div>
            
            <div class="output-panel">
                <div class="card">
                    <h2 class="card-title">🔄 Progress</h2>
                    <div class="progress-log" id="progressLog">
                        <div class="log-entry">Ready to generate...</div>
                    </div>
                </div>
                
                <div class="output-section hidden" id="outputSection">
                    <div class="card">
                        <h2 class="card-title">🎵 Generated Song</h2>
                        <div class="song-output" id="songOutput"></div>
                        
                        <div class="sob-panel hidden" id="sobPanel">
                            <div class="sob-verdict" id="sobVerdict"></div>
                            <div id="sobDetails"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let eventSource = null;
        
        function addLog(message, type = '') {
            const log = document.getElementById('progressLog');
            const entry = document.createElement('div');
            entry.className = 'log-entry ' + type;
            entry.textContent = message;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }
        
        function clearLog() {
            document.getElementById('progressLog').innerHTML = '';
        }
        
        async function startGeneration() {
            const apiKey = document.getElementById('apiKey').value;
            const transcription = document.getElementById('transcription').value;
            const circumstance = document.getElementById('circumstance').value;
            const maxCycles = document.getElementById('maxCycles').value;
            const enableOversight = document.getElementById('enableOversight').checked;
            
            if (!transcription && !circumstance) {
                alert('Please provide either a transcription or a circumstance/theme.');
                return;
            }
            
            // Update UI
            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            document.getElementById('btnText').textContent = 'Generating...';
            document.getElementById('btnSpinner').classList.remove('hidden');
            document.getElementById('outputSection').classList.add('hidden');
            clearLog();
            addLog('Starting generation...');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        transcription,
                        circumstance,
                        api_key: apiKey,
                        enable_oversight: enableOversight,
                        max_cycles: parseInt(maxCycles)
                    })
                });
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'Unknown error');
                }
                
                // Listen for progress updates
                eventSource = new EventSource('/progress');
                
                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'ping') return;
                    
                    if (data.type === 'status' || data.type === 'layer_init' || data.type === 'input') {
                        addLog(data.message);
                    } else if (data.type === 'sob_review') {
                        addLog(`⚖️ SOB Verdict: ${data.verdict.toUpperCase()} (${data.approved}/${data.total} approved)`, 
                            data.verdict === 'approved' ? 'success' : 'warning');
                    } else if (data.type === 'complete') {
                        addLog('✅ Song generation complete!', 'success');
                        showOutput(data.result);
                        eventSource.close();
                        resetButton();
                    } else if (data.type === 'error') {
                        addLog(data.message, 'error');
                        eventSource.close();
                        resetButton();
                    }
                };
                
                eventSource.onerror = () => {
                    addLog('Connection lost', 'error');
                    eventSource.close();
                    resetButton();
                };
                
            } catch (error) {
                addLog('❌ ' + error.message, 'error');
                resetButton();
            }
        }
        
        function resetButton() {
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            document.getElementById('btnText').textContent = '🎤 Generate Song';
            document.getElementById('btnSpinner').classList.add('hidden');
        }
        
        function showOutput(result) {
            document.getElementById('outputSection').classList.remove('hidden');
            
            // Format song parts
            let songText = '';
            const parts = result.song_parts || {};
            const order = ['hook', 'verse1', 'prechorus', 'chorus', 'verse2', 'bridge'];
            
            for (const part of order) {
                if (parts[part]) {
                    songText += `[${part.toUpperCase()}]\\n${parts[part]}\\n\\n`;
                }
            }
            
            document.getElementById('songOutput').textContent = songText || 'No song content generated.';
            
            // SOB Review
            if (result.sob_review && result.sob_review.verdict) {
                const panel = document.getElementById('sobPanel');
                panel.classList.remove('hidden');
                
                const verdict = document.getElementById('sobVerdict');
                verdict.className = 'sob-verdict ' + result.sob_review.verdict;
                verdict.innerHTML = `⚖️ ${result.sob_review.verdict.replace('_', ' ').toUpperCase()}`;
                
                document.getElementById('sobDetails').textContent = 
                    `${result.sob_review.approved}/${result.sob_review.total} personas approved`;
            }
        }
    </script>
</body>
</html>'''
    
    (templates_dir / "index.html").write_text(html_content, encoding='utf-8')


if __name__ == "__main__":
    create_templates()
    print("\n" + "="*50)
    print("🎵 ACE SONGWRITER WEB UI")
    print("="*50)
    print("\n🌐 Open in your browser: http://localhost:5000")
    print("📝 Press Ctrl+C to stop\n")
    app.run(debug=False, port=5000, threaded=True)
