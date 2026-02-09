# Resonance Live

**Resonance Live** is a real-time multimodal system that detects clinician cognitive overload from live audio and triggers protective interventions to reduce burnout and prevent fatigue-driven medical errors.

## 🚑 Why This Matters
Clinicians are trained to ignore their own fatigue. Cognitive overload is a leading hidden cause of medical error. Resonance Live acts as a *guardian for the healer*, detecting invisible stress before it becomes dangerous.

## 🧠 How It Works (Architecture)
**Observation Layer**
- Live microphone audio capture
- Voice activity detection (Silero VAD)
- Prosodic signal extraction (speech rate, intensity, jitter proxy)

**Reasoning Layer**
- Gemini multimodal reasoning over live audio context
- Infers cognitive load and burnout risk in real time

**Action Layer**
- Autonomous agent logic
- Triggers UI calming mode
- Adds recovery buffer / break recommendations
- Session replay + export for post-session analysis

## ⚙️ Tech Stack
- Python (FastAPI, WebSockets)
- Gemini Multimodal API
- Real-time audio processing (sounddevice)
- Silero VAD
- HTML + Chart.js dashboard

## ▶️ Run Locally

```bash
python server.py
python resonance_live.py
