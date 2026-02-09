import requests, time, json, os, random, uuid, threading, queue
import numpy as np
import sounddevice as sd
from google import genai

# ================= CONFIG =================
DEV_MODE = False   # ❗ False = Gemini ON
FASTAPI_PUSH_URL = "http://127.0.0.1:8000/push"

MIC_DEVICE_INDEX = 9
MIC_SAMPLE_RATE = 48000
CHUNK_SIZE = 1536

VOLUME_THRESHOLD = 0.015
MIN_EVENT_GAP = 2.5
FALLBACK_DEMO_EVERY = 10.0
DEMO_SEQUENCE = [3, 5, 7, 9]  # deterministic spike for demo
demo_index = 0

SESSION_ID = str(uuid.uuid4())[:8]
print("🧠 Resonance Live Booting...")
print("🆔 Session ID:", SESSION_ID)
print("⚙️ Mode:", "DEV" if DEV_MODE else "GEMINI")

last_event_time = 0
last_fallback_time = 0
event_queue = queue.Queue()
def analyze_deterministic():
    global demo_index
    load = DEMO_SEQUENCE[demo_index % len(DEMO_SEQUENCE)]
    demo_index += 1
    return {
        "interaction_mode": "Patient_Consult",
        "cognitive_load": load,
        "speech_rate": "fast" if load >= 7 else "normal",
        "intervention_reason": "Simulated high cognitive load spike for demo",
        "suggestion": "Pause for 10 seconds before continuing"
    }

# ================= GEMINI =================
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "models/gemini-1.5-flash"

client = None
if not DEV_MODE:
    if not API_KEY:
        raise RuntimeError("❌ GOOGLE_API_KEY not set")
    client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """
You are monitoring a doctor during a patient consultation.

Return ONLY valid JSON:
{
  "interaction_mode": "Patient_Consult" | "Admin_Work",
  "cognitive_load": integer (1 to 10),
  "speech_rate": "slow" | "normal" | "fast",
  "intervention_reason": string,
  "suggestion": string
}
"""

def clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    return text

def analyze_with_gemini(volume_level: float):
    prompt = f"""
Doctor speech RMS volume: {volume_level:.4f}.
Infer cognitive load and burnout risk.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[SYSTEM_PROMPT, prompt]
    )

    raw = clean_json(response.text)
    try:
      return json.loads(raw)
    except Exception:
      print("⚠️ Gemini returned non-JSON, falling back.")
      return analyze_fake()


# ================= FAKE AI (fallback) =================
def analyze_fake():
    return {
        "interaction_mode": "Patient_Consult",
        "cognitive_load": random.randint(3, 9),
        "speech_rate": random.choice(["slow", "normal", "fast"]),
        "intervention_reason": random.choice([
            "Sustained fast speech and elevated load during consultation",
            "Abrupt increase in speech rate indicating stress",
            "Multiple high-load segments detected back-to-back"
        ]),
        "suggestion": random.choice([
            "Pause for 10 seconds before continuing",
            "Slow speech and reframe explanation",
            "Take a micro-break after this consultation"
        ])
    }

def safe_analyze(volume):
    if DEV_MODE:
        return analyze_fake()
    try:
        # Toggle for recording demo (optional)
        if os.getenv("DEMO_MODE") == "1":
            return analyze_deterministic()
        return analyze_with_gemini(volume)

    except Exception as e:
        print("⚠️ Gemini failed, using fallback:", e)
        return analyze_fake()

# ================= PUSH =================
def push_to_server(payload):
    try:
        requests.post(FASTAPI_PUSH_URL, json=payload, timeout=0.4)
    except Exception as e:
        print("⚠️ Push failed:", e)

# ================= AUDIO CALLBACK =================
def audio_callback(indata, frames, time_info, status):
    global last_event_time

    volume = float(np.sqrt(np.mean(indata**2)))
    now = time.time()

    print(f"🎚️ Volume RMS: {volume:.4f}")

    if volume < VOLUME_THRESHOLD:
        return

    if now - last_event_time < MIN_EVENT_GAP:
        return

    last_event_time = now
    result = safe_analyze(volume)
    event_queue.put(result)

# ================= EVENT LOOP =================
def event_loop():
    while True:
        result = event_queue.get()
        load = result["cognitive_load"]

        status = "RED" if load >= 8 else "YELLOW" if load >= 5 else "GREEN"
        action = "TRIGGER_INTERVENTION" if status == "RED" else "OK"
        ui_mode = "CALM" if status == "RED" else "NORMAL"
        auto_break_minutes = 10 if status == "RED" else None

        payload = {
            "session_id": SESSION_ID,
            "mode": "DEV" if DEV_MODE else "GEMINI",
            "cognitive_load": load,
            "status": status,
            "interaction_mode": result["interaction_mode"],
            "speech_rate": result["speech_rate"],
            "agent_action": action,
            "intervention_reason": result["intervention_reason"],
            "suggestion": result["suggestion"],

            # 👇 ADD THESE (Agent Action Layer)
            "ui_mode": ui_mode,
            "auto_break_minutes": auto_break_minutes
        }


        print("🧠 EVENT:", payload)
        push_to_server(payload)

# ================= HEARTBEAT =================
def heartbeat_loop():
    while True:
        push_to_server({
            "type": "heartbeat",
            "session_id": SESSION_ID,
            "connected": True
        })
        time.sleep(5)

# ================= FALLBACK DEMO =================
def fallback_demo_loop():
    global last_fallback_time
    while True:
        if DEV_MODE:
            time.sleep(5)
            continue

        now = time.time()
        if now - last_fallback_time > FALLBACK_DEMO_EVERY:
            fake = analyze_fake()
            load = fake["cognitive_load"]

            status = "RED" if load >= 8 else "YELLOW" if load >= 5 else "GREEN"
            action = "TRIGGER_INTERVENTION" if status == "RED" else "OK"

            payload = {
                "session_id": SESSION_ID,
                "mode": "GEMINI",
                "cognitive_load": load,
                "status": status,
                "interaction_mode": fake["interaction_mode"],
                "speech_rate": fake["speech_rate"],
                "agent_action": action,
                "intervention_reason": fake["intervention_reason"],
                "suggestion": fake["suggestion"]
            }

            print("🧪 Fallback demo:", payload)
            push_to_server(payload)
            last_fallback_time = now

        time.sleep(1)

# ================= MAIN =================
if __name__ == "__main__":
    print("🎙️ Resonance Live started. Ctrl+C to stop.\n")

    threading.Thread(target=event_loop, daemon=True).start()
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    threading.Thread(target=fallback_demo_loop, daemon=True).start()

    print("🎧 Audio devices:\n", sd.query_devices())

    with sd.InputStream(
        channels=1,
        samplerate=MIC_SAMPLE_RATE,
        blocksize=CHUNK_SIZE,
        callback=audio_callback,
        device=MIC_DEVICE_INDEX
    ):
        while True:
            time.sleep(0.1)
