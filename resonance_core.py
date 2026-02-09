import json
import re
from google import genai

API_KEY = "AIzaSyCX-rsSX3-O08nRspgieT2QJ7aNEPgcTNI"
client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """
You analyze vocal prosody and speech patterns to estimate cognitive load.
You do NOT perform medical diagnosis.
Return ONLY valid JSON:

{
  "interaction_mode": "Patient_Consult" | "Admin_Work" | "Personal_Stress",
  "cognitive_load": integer (1 to 10),
  "speech_rate": "slow" | "normal" | "fast"
}
"""

def analyze_text_proxy(text: str):
    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=[SYSTEM_PROMPT, text]
    )

    raw = response.text.strip()

    # --- Robust JSON extraction ---
    if raw.startswith("```"):
        raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    try:
        data = json.loads(raw)
        return data
    except Exception:
        print("JSON parse failed:", raw)
        return None


class DoctorState:
    def __init__(self):
        self.consecutive_high = 0

    def update(self, result):
        load = result["cognitive_load"]

        if load >= 8:
            self.consecutive_high += 1
        else:
            self.consecutive_high = 0

        if self.consecutive_high >= 3:
            return "TRIGGER_INTERVENTION"
        return "OK"


if __name__ == "__main__":
    print("Running Resonance core test...")

    test = analyze_text_proxy(
        "The speaker is talking very fast and sounds rushed and frustrated."
    )

    print("Parsed:", test)

    if test:
        state = DoctorState()
        for i in range(3):
            action = state.update(test)
            print(f"Update {i+1} -> Action:", action)