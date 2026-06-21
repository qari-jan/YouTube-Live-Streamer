
Overview
This is a Python project built with **Flask + FFmpeg**, written entirely in a single Python file.  
It allows users to upload a video and stream it live on YouTube with simple start/stop controls.

 Features
- Upload video directly from Python interface
- Stream video live to YouTube using FFmpeg
- Start/Stop streaming controls
- Loop playback option
- No external HTML/CSS files required (everything handled inside Python)

Project Structure

YouTube-Live-Streamer/ │── web.py            # Main Python file (Flask + FFmpeg logic) 
── requirements.txt  # Python dependencies 
── README.md         # Project guide


Requirements
- Python 3.x
- FFmpeg (must be installed separately on system)
- Install Python dependencies:
  ```bash
  pip install -r requirements.txt

requirements.txt

Flask
Werkzeug
requests

How to Run

Clone this repository:

git clone https://github.com/YourUsername/YouTube-Live-Streamer.git

Navigate to the project folder:

cd YouTube-Live-Streamer

Run the Python file:

python app.py

Open browser → http://127.0.0.1:5000/

Upload video → Click Start Stream → Video goes live on YouTube.

Use Stop Stream button to end broadcast.

Notes

You must obtain a YouTube Stream Key from YouTube Studio.

Enable Reuse Stream Key for continuous streaming.

PC must remain ON and CMD window open during streaming.

If filename mismatches, FFmpeg will fail to start.

FFmpeg Installation
1. Download FFmpeg from official site: https://www.gyan.dev/ffmpeg/builds/
2. Extract the folder.
3. Add `bin/` folder path to System Environment Variables (PATH).
4. Verify installation:
   ```bash
   ffmpeg -version


Developer

Developed by HamzaIntern at Quantum Logics (Web Intern)
