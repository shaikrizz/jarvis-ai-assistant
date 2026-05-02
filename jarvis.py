import cv2
import speech_recognition as sr
import subprocess
from groq import Groq
from PIL import Image
import sounddevice as sd
import wave
import os
import time
import base64
import io
import threading

GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
recognizer = sr.Recognizer()

JARVIS_PERSONALITY = """You are JARVIS, a helpful and intelligent AI assistant.
You are professional, friendly and precise.
Answer questions accurately and helpfully like a general purpose AI assistant.
Keep responses short and conversational — max 3-4 sentences.
Address the user as 'Sir'."""

conversation_history = [
    {"role": "system", "content": JARVIS_PERSONALITY}
]

is_listening = False
is_speaking = False
cap = None

def speak(text):
    global is_speaking
    print(f"JARVIS: {text}")
    is_speaking = True
    try:
        subprocess.run(
            ['python', '-c', f'''
import pyttsx3
engine = pyttsx3.init()
engine.setProperty("rate", 150)
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)
engine.say("""{text}""")
engine.runAndWait()
'''],
            timeout=30
        )
    except Exception as e:
        print(f"Speech error: {e}")
    is_speaking = False

def capture_frame():
    global cap
    for _ in range(5):
        ret, frame = cap.read()
    if not ret:
        return None
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def ask_jarvis(prompt):
    global conversation_history
    conversation_history.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history
    )
    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    if len(conversation_history) > 20:
        conversation_history = [conversation_history[0]] + conversation_history[-18:]
    return reply

def ask_jarvis_vision(prompt):
    image_b64 = capture_frame()
    if image_b64 is None:
        return "Sir, I cannot access the camera."
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": JARVIS_PERSONALITY},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ]
    )
    return response.choices[0].message.content

def listen_for_command():
    print("Listening... speak now!")
    duration = 6
    sample_rate = 16000
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()

    tmp_path = os.path.join(os.path.expanduser("~"), f"jarvis_{int(time.time())}.wav")
    with wave.open(tmp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())

    with sr.AudioFile(tmp_path) as source:
        audio = recognizer.record(source)
    try:
        os.remove(tmp_path)
    except:
        pass

    text = recognizer.recognize_google(audio)
    print(f"You: {text}")
    return text.lower()

def record_audio(duration=4, sample_rate=16000):
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    tmp_path = os.path.join(os.path.expanduser("~"), f"jarvis_wake_{int(time.time())}.wav")
    with wave.open(tmp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())
    return tmp_path

def listen_for_wake_word():
    global is_listening, is_speaking
    recognizer2 = sr.Recognizer()
    print("Wake word listener started... Say 'Hey Jarvis'")
    while True:
        if is_speaking:
            time.sleep(0.1)
            continue
        try:
            print("Waiting for wake word...")
            tmp_path = record_audio(duration=4)
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer2.record(source)
            try:
                os.remove(tmp_path)
            except:
                pass
            text = recognizer2.recognize_google(audio).lower()
            print(f"Heard: {text}")
            if "jarvis" in text:
                is_listening = True
                handle_conversation()
                is_listening = False
        except sr.UnknownValueError:
            print("Listening...")
        except Exception as e:
            print(f"Wake word error: {e}")
            
def handle_conversation():
    global is_listening
    visual_keywords = ["what is", "what's this", "look at", "identify", "what do you see", "show me"]
    speak("Sir?")
    while True:
        try:
            command = listen_for_command()
            if any(q in command for q in ["goodbye", "bye", "stop", "exit", "quit"]):
                speak("Goodbye Sir, I'll be here when you need me.")
                is_listening = False
                return
            if any(kw in command for kw in visual_keywords):
                speak("Analyzing visual input, Sir.")
                reply = ask_jarvis_vision(command)
            else:
                reply = ask_jarvis(command)
            speak(reply)
        except sr.UnknownValueError:
            speak("Could you repeat that, Sir?")
        except Exception as e:
            print(f"Error: {e}")
            speak("Something went wrong, Sir.")

def main():
    global cap
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    wake_thread = threading.Thread(target=listen_for_wake_word, daemon=True)
    wake_thread.start()

    speak("JARVIS online. Say Hey Jarvis to wake me up, Sir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        if is_listening:
            cv2.rectangle(frame, (0, 0), (639, 479), (0, 255, 0), 4)
            cv2.putText(frame, "Listening...", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        elif is_speaking:
            cv2.rectangle(frame, (0, 0), (639, 479), (255, 165, 0), 4)
            cv2.putText(frame, "JARVIS Speaking...", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 165, 0), 2)
        else:
            cv2.putText(frame, "Say: Hey Jarvis", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

        cv2.imshow("JARVIS Vision", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            speak("Shutting down. Goodbye Sir.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()