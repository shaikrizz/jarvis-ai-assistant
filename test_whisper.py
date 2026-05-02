import sounddevice as sd
import wave
import os
import numpy as np
from groq import Groq

client = Groq(api_key="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")

print('Speak for 3 seconds...')
recording = sd.rec(48000, samplerate=16000, channels=1, dtype='int16')
sd.wait()

tmp_path = 'test_audio.wav'
with wave.open(tmp_path, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(recording.tobytes())

print(f'File size: {os.path.getsize(tmp_path)} bytes')

with open(tmp_path, 'rb') as f:
    result = client.audio.transcriptions.create(
        file=(tmp_path, f),
        model='whisper-large-v3',
        language='en',
        response_format='text'
    )
print(f'Transcription: {result}')