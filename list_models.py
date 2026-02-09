from google import genai

API_KEY = "AIzaSyCX-rsSX3-O08nRspgieT2QJ7aNEPgcTNI"
client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """
You are an AI system that analyzes vocal prosody and speech patterns to estimate cognitive load.
You do NOT infer medical conditions or mental health diagnoses.
You return ONLY valid JSON with the following schema:

{
  "interaction_mode": "Patient_Consult" | "Admin_Work" | "Personal_Stress",
  "cognitive_load": integer (1 to 10),
  "speech_rate": "slow" | "normal" | "fast"
}
"""

response = client.models.generate_content(
    model="models/gemini-pro-latest",
    contents=[
        SYSTEM_PROMPT,
        "The speaker is talking very fast and sounds rushed and frustrated."
    ]
)

print(response.text)
