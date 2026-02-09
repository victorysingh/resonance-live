import sounddevice as sd
import numpy as np
import torch
import time

# Force Realtek Microphone (MME)
sd.default.device = 1  

# Load Silero VAD model
model, utils = torch.hub.load('snakers4/silero-vad', 'silero_vad', force_reload=False)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

SAMPLE_RATE = 16000
CHUNK_SIZE = 512  # Silero VAD expects exactly 512 samples at 16kHz

vad_iterator = VADIterator(model, threshold=0.15)


print("🎙️ Starting microphone... Speak to see detection. Ctrl+C to stop.")

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)

    audio_chunk = indata[:, 0]  # mono
    audio_tensor = torch.from_numpy(audio_chunk).float()

    volume = np.linalg.norm(indata)
    print("Volume:", round(volume, 4))

    vad_result = vad_iterator(audio_tensor, return_seconds=False)

    if vad_result is not None:
        print("🟢 Speech detected")
    else:
        print("⚪ Silence")

with sd.InputStream(channels=1, samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE, callback=audio_callback):
    while True:
        time.sleep(0.1)
