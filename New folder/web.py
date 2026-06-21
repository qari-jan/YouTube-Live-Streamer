from flask import Flask, request, render_template_string, redirect, jsonify
import os
import subprocess
import threading
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

stream_process = None
stream_start_time = None
stream_video_name = None

HOME_PAGE = '''
<!DOCTYPE html>
<html lang="ur">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamForge — 24/7 YouTube Live</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg:        #080c10;
            --surface:   #0e1318;
            --card:      #131920;
            --border:    #1e2832;
            --accent:    #e63946;
            --accent2:   #ff6b6b;
            --gold:      #f4a261;
            --green:     #2ec4b6;
            --text:      #e8edf2;
            --muted:     #6b7a8d;
            --tag-bg:    #1a2230;
            --radius:    12px;
            --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        html { scroll-behavior: smooth; }

        body {
            font-family: 'Space Grotesk', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ── Ambient glow background ── */
        body::before {
            content: '';
            position: fixed;
            top: -30%;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            height: 500px;
            background: radial-gradient(ellipse, rgba(230,57,70,0.08) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }

        /* ── Layout ── */
        .shell {
            position: relative;
            z-index: 1;
            max-width: 860px;
            margin: 0 auto;
            padding: 40px 24px 80px;
        }

        /* ── Header ── */
        header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 48px;
        }

        .logo-mark {
            width: 44px;
            height: 44px;
            background: var(--accent);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 0 24px rgba(230,57,70,0.4);
        }

        .logo-mark svg { width: 24px; height: 24px; fill: white; }

        .brand h1 {
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text);
        }

        .brand p {
            font-size: 0.75rem;
            color: var(--muted);
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .status-pill {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: var(--surface);
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--muted);
            cursor: pointer;
            transition: var(--transition);
        }

        .status-pill:hover { border-color: var(--accent); color: var(--text); }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--muted);
            transition: var(--transition);
        }

        .dot.live {
            background: var(--accent);
            box-shadow: 0 0 8px var(--accent);
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        /* ── Step cards ── */
        .steps { display: flex; flex-direction: column; gap: 20px; }

        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            transition: border-color var(--transition);
        }

        .card:hover { border-color: #2d3d50; }

        .card-header {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
        }

        .step-num {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: var(--tag-bg);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--muted);
            flex-shrink: 0;
        }

        .card-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text);
        }

        .card-body { padding: 24px; }

        /* ── Upload zone ── */
        .upload-zone {
            border: 1.5px dashed var(--border);
            border-radius: 10px;
            padding: 36px 24px;
            text-align: center;
            cursor: pointer;
            transition: var(--transition);
            position: relative;
        }

        .upload-zone:hover,
        .upload-zone.drag-over {
            border-color: var(--accent);
            background: rgba(230,57,70,0.04);
        }

        .upload-zone input[type="file"] {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
            width: 100%;
            height: 100%;
        }

        .upload-icon {
            width: 48px;
            height: 48px;
            margin: 0 auto 12px;
            background: var(--tag-bg);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .upload-icon svg { width: 22px; height: 22px; stroke: var(--muted); fill: none; }

        .upload-zone h3 {
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .upload-zone p {
            font-size: 0.78rem;
            color: var(--muted);
        }

        .file-name-display {
            margin-top: 14px;
            padding: 8px 14px;
            background: var(--tag-bg);
            border-radius: 8px;
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--green);
            display: none;
        }

        /* ── Form fields ── */
        .field { margin-bottom: 16px; }

        .field label {
            display: block;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--muted);
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .field input {
            width: 100%;
            padding: 11px 14px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            outline: none;
            transition: border-color var(--transition), box-shadow var(--transition);
        }

        .field input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(230,57,70,0.12);
        }

        .field input::placeholder { color: #3a4a5a; }

        .hint {
            margin-top: 6px;
            font-size: 0.72rem;
            color: var(--muted);
        }

        /* ── Buttons ── */
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 11px 22px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            font-family: 'Space Grotesk', sans-serif;
            border: none;
            cursor: pointer;
            transition: var(--transition);
            text-decoration: none;
        }

        .btn-primary {
            background: var(--accent);
            color: white;
            box-shadow: 0 4px 16px rgba(230,57,70,0.3);
        }

        .btn-primary:hover {
            background: var(--accent2);
            box-shadow: 0 4px 24px rgba(230,57,70,0.5);
            transform: translateY(-1px);
        }

        .btn-primary:active { transform: translateY(0); }

        .btn-secondary {
            background: var(--tag-bg);
            color: var(--text);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            border-color: var(--accent);
            color: var(--accent);
        }

        .btn-danger {
            background: transparent;
            color: var(--accent);
            border: 1px solid rgba(230,57,70,0.4);
        }

        .btn-danger:hover {
            background: rgba(230,57,70,0.08);
            border-color: var(--accent);
        }

        .btn svg { width: 16px; height: 16px; fill: currentColor; }

        /* ── Live status card ── */
        .live-card {
            background: linear-gradient(135deg, rgba(230,57,70,0.06), rgba(230,57,70,0.02));
            border: 1px solid rgba(230,57,70,0.25);
            border-radius: var(--radius);
            padding: 24px;
            display: none;
        }

        .live-card.visible { display: block; }

        .live-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .live-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--accent);
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .live-meta {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }

        .meta-box {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
        }

        .meta-box .label {
            font-size: 0.68rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 4px;
        }

        .meta-box .value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--text);
        }

        .meta-box .value.green { color: var(--green); }

        /* ── Progress bar on upload ── */
        .progress-wrap {
            margin-top: 14px;
            background: var(--tag-bg);
            border-radius: 999px;
            height: 4px;
            overflow: hidden;
            display: none;
        }

        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--gold));
            width: 0%;
            transition: width 0.3s;
            border-radius: 999px;
        }

        /* ── Toast ── */
        #toast {
            position: fixed;
            bottom: 28px;
            right: 28px;
            padding: 14px 20px;
            border-radius: 10px;
            font-size: 0.85rem;
            font-weight: 500;
            color: white;
            z-index: 1000;
            transform: translateY(80px);
            opacity: 0;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            max-width: 320px;
        }

        #toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        #toast.success { background: #1a3a2a; border: 1px solid #2ec4b6; color: var(--green); }
        #toast.error   { background: #3a1a1a; border: 1px solid var(--accent); color: var(--accent2); }
        #toast.info    { background: #1a2430; border: 1px solid #4a6080; color: #8ab4d4; }

        /* ── Uploaded files list ── */
        .files-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 16px;
        }

        .file-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.8rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
            cursor: pointer;
            transition: var(--transition);
        }

        .file-item:hover { border-color: var(--accent); color: var(--accent); }

        .file-item svg { width: 14px; height: 14px; fill: var(--muted); flex-shrink: 0; }

        /* ── Responsive ── */
        @media (max-width: 600px) {
            .live-meta { grid-template-columns: 1fr 1fr; }
            header { flex-wrap: wrap; }
            .status-pill { margin-left: 0; }
        }

        /* ── Spinner ── */
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            display: none;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .btn.loading .spinner { display: inline-block; }
        .btn.loading .btn-text { display: none; }
    </style>
</head>
<body>
<div class="shell">
    <header>
        <div class="logo-mark">
            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </div>
        <div class="brand">
            <h1>StreamForge</h1>
            <p>24/7 YouTube Live Engine</p>
        </div>
        <div class="status-pill" onclick="checkStatus()">
            <div class="dot" id="status-dot"></div>
            <span id="status-text">Idle</span>
        </div>
    </header>

    <!-- Live status card -->
    <div class="live-card" id="live-card">
        <div class="live-top">
            <div class="live-badge">
                <div class="dot live"></div>
                Live Now
            </div>
            <button class="btn btn-danger" onclick="stopStream()">
                <svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12"/></svg>
                Stop Stream
            </button>
        </div>
        <div class="live-meta">
            <div class="meta-box">
                <div class="label">Video</div>
                <div class="value" id="live-video-name">—</div>
            </div>
            <div class="meta-box">
                <div class="label">Duration</div>
                <div class="value green" id="live-duration">00:00:00</div>
            </div>
            <div class="meta-box">
                <div class="label">Mode</div>
                <div class="value">∞ Loop</div>
            </div>
        </div>
    </div>

    <div class="steps">
        <!-- Step 1: Upload -->
        <div class="card">
            <div class="card-header">
                <div class="step-num">01</div>
                <div class="card-title">Upload Video</div>
            </div>
            <div class="card-body">
                <div class="upload-zone" id="upload-zone">
                    <input type="file" id="video-file" name="video" accept="video/*" onchange="handleFileSelect(this)">
                    <div class="upload-icon">
                        <svg viewBox="0 0 24 24" stroke-width="1.5"><path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                    <h3>Drop your video here</h3>
                    <p>MP4, MKV, MOV, AVI — any format ffmpeg supports</p>
                    <div class="file-name-display" id="file-name-display"></div>
                </div>
                <div class="progress-wrap" id="progress-wrap">
                    <div class="progress-bar" id="progress-bar"></div>
                </div>
                <div style="margin-top: 16px; display: flex; gap: 10px; align-items: center;">
                    <button class="btn btn-primary" onclick="uploadFile()" id="upload-btn">
                        <svg viewBox="0 0 24 24"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                        <span class="btn-text">Upload</span>
                        <div class="spinner"></div>
                    </button>
                    <span id="upload-status" style="font-size:0.78rem; color: var(--muted);"></span>
                </div>

                <!-- Uploaded files -->
                <div class="files-list" id="files-list"></div>
            </div>
        </div>

        <!-- Step 2: Configure & Start -->
        <div class="card">
            <div class="card-header">
                <div class="step-num">02</div>
                <div class="card-title">Configure & Start Stream</div>
            </div>
            <div class="card-body">
                <div class="field">
                    <label>Video filename</label>
                    <input type="text" id="video-name" placeholder="e.g. stream.mp4">
                    <div class="hint">Exact name of the uploaded video file.</div>
                </div>
                <div class="field">
                    <label>YouTube Stream Key</label>
                    <input type="password" id="stream-key" placeholder="xxxx-xxxx-xxxx-xxxx-xxxx">
                    <div class="hint">Found in YouTube Studio → Go Live → Stream Settings.</div>
                </div>
                <button class="btn btn-primary" onclick="startStream()" id="start-btn">
                    <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    <span class="btn-text">Go Live</span>
                    <div class="spinner"></div>
                </button>
            </div>
        </div>
    </div>
</div>

<div id="toast"></div>

<script>
    let timerInterval = null;
    let streamStart = null;

    // ── Toast ──
    function showToast(msg, type = 'info') {
        const t = document.getElementById('toast');
        t.textContent = msg;
        t.className = 'show ' + type;
        clearTimeout(t._hide);
        t._hide = setTimeout(() => t.className = '', 3500);
    }

    // ── File select ──
    function handleFileSelect(input) {
        if (!input.files[0]) return;
        const name = input.files[0].name;
        const display = document.getElementById('file-name-display');
        display.textContent = '📎 ' + name;
        display.style.display = 'block';
        document.getElementById('video-name').value = name;
    }

    // ── Drag & drop ──
    const zone = document.getElementById('upload-zone');
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files[0]) {
            document.getElementById('video-file').files = files;
            handleFileSelect(document.getElementById('video-file'));
        }
    });

    // ── Upload ──
    async function uploadFile() {
        const fileInput = document.getElementById('video-file');
        if (!fileInput.files[0]) { showToast('No file selected.', 'error'); return; }
        const btn = document.getElementById('upload-btn');
        btn.classList.add('loading');
        document.getElementById('upload-status').textContent = 'Uploading…';
        document.getElementById('progress-wrap').style.display = 'block';

        const formData = new FormData();
        formData.append('video', fileInput.files[0]);

        const xhr = new XMLHttpRequest();
        xhr.upload.onprogress = e => {
            if (e.lengthComputable) {
                const pct = (e.loaded / e.total * 100).toFixed(0);
                document.getElementById('progress-bar').style.width = pct + '%';
            }
        };
        xhr.onload = () => {
            btn.classList.remove('loading');
            if (xhr.status === 200) {
                showToast('Video uploaded successfully!', 'success');
                document.getElementById('upload-status').textContent = 'Done ✓';
                loadFiles();
            } else {
                showToast('Upload failed.', 'error');
                document.getElementById('upload-status').textContent = '';
            }
        };
        xhr.onerror = () => {
            btn.classList.remove('loading');
            showToast('Upload error.', 'error');
        };
        xhr.open('POST', '/upload_ajax');
        xhr.send(formData);
    }

    // ── Load uploaded files ──
    async function loadFiles() {
        const res = await fetch('/files');
        const data = await res.json();
        const list = document.getElementById('files-list');
        list.innerHTML = '';
        data.files.forEach(f => {
            const el = document.createElement('div');
            el.className = 'file-item';
            el.innerHTML = `<svg viewBox="0 0 24 24"><path d="M15 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V7l-5-5z"/><path d="M14 2v5h5"/></svg>${f}`;
            el.onclick = () => {
                document.getElementById('video-name').value = f;
                showToast('Filename copied to form.', 'info');
            };
            list.appendChild(el);
        });
    }

    // ── Start stream ──
    async function startStream() {
        const videoName = document.getElementById('video-name').value.trim();
        const streamKey = document.getElementById('stream-key').value.trim();
        if (!videoName || !streamKey) { showToast('Fill in both fields.', 'error'); return; }

        const btn = document.getElementById('start-btn');
        btn.classList.add('loading');

        const res = await fetch('/start_ajax', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_name: videoName, stream_key: streamKey })
        });
        const data = await res.json();
        btn.classList.remove('loading');

        if (data.ok) {
            showToast('Stream started! Check YouTube Studio.', 'success');
            setLiveUI(true, videoName);
        } else {
            showToast(data.error || 'Failed to start stream.', 'error');
        }
    }

    // ── Stop stream ──
    async function stopStream() {
        const res = await fetch('/stop_ajax');
        const data = await res.json();
        if (data.ok) {
            showToast('Stream stopped.', 'info');
            setLiveUI(false);
        } else {
            showToast('No stream running.', 'error');
        }
    }

    // ── Status check ──
    async function checkStatus() {
        const res = await fetch('/status');
        const data = await res.json();
        if (data.live) {
            setLiveUI(true, data.video, data.start_time);
            showToast('Stream is live.', 'success');
        } else {
            setLiveUI(false);
            showToast('No stream running.', 'info');
        }
    }

    // ── Live UI toggle ──
    function setLiveUI(live, videoName, startTimestamp) {
        const dot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        const liveCard = document.getElementById('live-card');

        if (live) {
            dot.classList.add('live');
            statusText.textContent = 'Live';
            liveCard.classList.add('visible');
            document.getElementById('live-video-name').textContent = videoName || '—';
            streamStart = startTimestamp ? startTimestamp * 1000 : Date.now();
            clearInterval(timerInterval);
            timerInterval = setInterval(updateTimer, 1000);
        } else {
            dot.classList.remove('live');
            statusText.textContent = 'Idle';
            liveCard.classList.remove('visible');
            clearInterval(timerInterval);
            document.getElementById('live-duration').textContent = '00:00:00';
        }
    }

    function updateTimer() {
        const elapsed = Math.floor((Date.now() - streamStart) / 1000);
        const h = String(Math.floor(elapsed / 3600)).padStart(2, '0');
        const m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
        const s = String(elapsed % 60).padStart(2, '0');
        document.getElementById('live-duration').textContent = `${h}:${m}:${s}`;
    }

    // ── Init ──
    window.addEventListener('DOMContentLoaded', () => {
        loadFiles();
        checkStatus();
    });
</script>
</body>
</html>
'''

@app.route("/")
def home():
    return render_template_string(HOME_PAGE)


@app.route("/upload_ajax", methods=["POST"])
def upload_ajax():
    file = request.files.get('video')
    if not file or file.filename == '':
        return jsonify({"ok": False, "error": "No file provided."}), 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return jsonify({"ok": True, "filename": file.filename})


@app.route("/files")
def list_files():
    try:
        files = [f for f in os.listdir(UPLOAD_FOLDER)
                 if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
    except Exception:
        files = []
    return jsonify({"files": sorted(files)})


@app.route("/start_ajax", methods=["POST"])
def start_ajax():
    global stream_process, stream_start_time, stream_video_name
    data = request.get_json(silent=True) or {}
    video_name = data.get("video_name", "").strip()
    stream_key = data.get("stream_key", "").strip()

    if not video_name or not stream_key:
        return jsonify({"ok": False, "error": "Missing video name or stream key."})

    video_path = os.path.join(UPLOAD_FOLDER, video_name)
    if not os.path.exists(video_path):
        return jsonify({"ok": False, "error": f"Video '{video_name}' not found in uploads."})

    if stream_process and stream_process.poll() is None:
        return jsonify({"ok": False, "error": "A stream is already running. Stop it first."})

    command = [
    r'E:\Web\ffmpeg\bin\ffmpeg.exe', '-re', '-stream_loop', '-1', '-i', video_path,
    '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '3000k',
    '-c:a', 'aac', '-b:a', '128k', '-f', 'flv',
    f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
]


    def run_stream():
        global stream_process
        stream_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        stream_process.wait()

    stream_start_time = time.time()
    stream_video_name = video_name
    thread = threading.Thread(target=run_stream, daemon=True)
    thread.start()

    # Give ffmpeg a moment to either start or fail
    time.sleep(1.5)
    if stream_process and stream_process.poll() is not None:
        return jsonify({"ok": False, "error": "ffmpeg exited immediately. Check video file and stream key."})

    return jsonify({"ok": True})


@app.route("/stop_ajax")
def stop_ajax():
    global stream_process, stream_start_time, stream_video_name
    if stream_process and stream_process.poll() is None:
        stream_process.terminate()
        stream_process = None
        stream_start_time = None
        stream_video_name = None
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "No stream is running."})


@app.route("/status")
def status():
    live = stream_process is not None and stream_process.poll() is None
    return jsonify({
        "live": live,
        "video": stream_video_name if live else None,
        "start_time": stream_start_time if live else None,
    })


# ── Legacy routes (kept for backward compatibility) ──
@app.route("/upload", methods=["POST"])
def upload_legacy():
    file = request.files.get('video')
    if file:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        return redirect("/")
    return redirect("/")


@app.route("/start", methods=["POST"])
def start_legacy():
    return redirect("/")


@app.route("/stop")
def stop_legacy():
    return redirect("/")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)