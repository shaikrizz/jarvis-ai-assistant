import cv2
import speech_recognition as sr
import subprocess
from groq import Groq
from PIL import Image, ImageTk
import sounddevice as sd
import wave
import os
import time
import base64
import io
import threading
import tkinter as tk
from datetime import datetime
import numpy as np
import asyncio
import edge_tts

GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
recognizer = sr.Recognizer()

JARVIS_PERSONALITY = """You are JARVIS, an advanced AI assistant like ChatGPT or Claude.
You are highly intelligent, helpful, accurate and conversational.
You have a microphone and can hear the user's voice — their speech is transcribed and sent to you as text.
You have a live camera feed and can analyze images when asked.
You can answer any question on any topic — science, math, history, coding, general knowledge, advice, and more.
Never say you cannot hear or process audio — you can, through speech recognition.
Never say you are text-based only — you are a full voice and vision AI assistant.
Keep responses concise — 1 to 3 sentences for simple questions, longer only when needed.
Be natural and conversational, not robotic."""

conversation_history = [{"role": "system", "content": JARVIS_PERSONALITY}]
is_listening = False
is_speaking = False
stop_speaking = False
camera_visible = True
conversation_active = False
cap = None
root = None
chat_frame_inner = None
chat_canvas = None
status_label = None
camera_label = None
camera_frame = None
thinking_label = None
log_file = f"jarvis_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def save_to_file(speaker, text):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {speaker}: {text}\n")

def add_chat(speaker, text):
    def _add():
        bubble_frame = tk.Frame(chat_frame_inner, bg="#0d0d0d")
        bubble_frame.pack(fill=tk.X, pady=4, padx=8)
        timestamp = datetime.now().strftime("%H:%M")
        if speaker == "You":
            outer = tk.Frame(bubble_frame, bg="#0d0d0d")
            outer.pack(anchor="e")
            bubble = tk.Label(outer, text=text, bg="#1a4a7a", fg="#ffffff",
                             font=("Helvetica", 10), wraplength=280,
                             justify=tk.LEFT, padx=10, pady=6)
            bubble.pack(anchor="e")
            time_label = tk.Label(outer, text=timestamp, bg="#0d0d0d",
                                 fg="#444444", font=("Helvetica", 7))
            time_label.pack(anchor="e")
        else:
            outer = tk.Frame(bubble_frame, bg="#0d0d0d")
            outer.pack(anchor="w")
            bubble = tk.Label(outer, text=text, bg="#0a3d3d", fg="#00e5cc",
                             font=("Helvetica", 10), wraplength=280,
                             justify=tk.LEFT, padx=10, pady=6)
            bubble.pack(anchor="w")
            time_label = tk.Label(outer, text=timestamp, bg="#0d0d0d",
                                 fg="#444444", font=("Helvetica", 7))
            time_label.pack(anchor="w")
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1.0)
        save_to_file(speaker, text)
    root.after(0, _add)

def add_thinking_indicator():
    def _add():
        global thinking_label
        thinking_frame = tk.Frame(chat_frame_inner, bg="#0d0d0d")
        thinking_frame.pack(fill=tk.X, pady=4, padx=8, anchor="w")
        thinking_label = tk.Label(thinking_frame, text="● ● ●  thinking...",
                                  bg="#0d0d0d", fg="#444444",
                                  font=("Helvetica", 9, "italic"))
        thinking_label.pack(anchor="w")
        chat_canvas.update_idletasks()
        chat_canvas.yview_moveto(1.0)
    root.after(0, _add)

def remove_thinking_indicator():
    def _remove():
        global thinking_label
        try:
            thinking_label.master.destroy()
        except:
            pass
    root.after(0, _remove)

def set_status(text, color="#00ff00"):
    root.after(0, lambda: status_label.config(text=text, fg=color))

def speak(text):
    global is_speaking, is_listening, stop_speaking
    is_speaking = True
    stop_speaking = False
    is_listening = False
    set_status("JARVIS Speaking...", "#ffa500")
    try:
        async def generate():
            communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural", rate="+20%")
            await communicate.save("jarvis_tts.mp3")
        asyncio.run(generate())
        if not stop_speaking:
            subprocess.run(
                ['powershell', '-c',
                 f'Add-Type -AssemblyName presentationCore; '
                 f'$player = New-Object System.Windows.Media.MediaPlayer; '
                 f'$player.Open([uri]"{os.path.abspath("jarvis_tts.mp3")}"); '
                 f'$player.Play(); '
                 f'Start-Sleep -Milliseconds 500; '
                 f'while ($player.NaturalDuration.HasTimeSpan -eq $false) {{ Start-Sleep -Milliseconds 100 }}; '
                 f'$duration = $player.NaturalDuration.TimeSpan.TotalSeconds; '
                 f'Start-Sleep -Seconds $duration'],
                timeout=60
            )
    except Exception as e:
        print(f"Speech error: {e}")
    is_speaking = False
    stop_speaking = False
    set_status("Say: Hey Jarvis", "#888888")

def stop_jarvis_speaking():
    global stop_speaking, is_speaking, is_listening, conversation_active
    stop_speaking = True
    is_speaking = False
    conversation_active = False
    try:
        subprocess.run(
            ['powershell', '-c',
             'Get-Process powershell | Where-Object {$_.MainWindowTitle -eq ""} | Stop-Process -Force'],
            capture_output=True, timeout=3
        )
    except:
        pass
    set_status("Say: Hey Jarvis", "#888888")
    is_listening = False
def toggle_camera():
    global camera_visible
    camera_visible = not camera_visible
    if camera_visible:
        camera_label.config(width=480, height=360)
        camera_label.pack()
        toggle_cam_btn.config(text="📷 Hide Camera")
    else:
        camera_label.pack_forget()
        toggle_cam_btn.config(text="📷 Show Camera")

def capture_frame():
    global cap
    if cap is None:
        return None
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
    add_thinking_indicator()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history
    )
    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    if len(conversation_history) > 30:
        conversation_history = [conversation_history[0]] + conversation_history[-28:]
    remove_thinking_indicator()
    return reply

def ask_jarvis_vision(prompt):
    image_b64 = capture_frame()
    if image_b64 is None:
        return "Sir, I cannot access the camera."
    add_thinking_indicator()
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
    remove_thinking_indicator()
    return response.choices[0].message.content

def record_until_silence(sample_rate=16000, silence_threshold=800,
                          silence_duration=3.0, max_duration=20):
    chunk_size = int(sample_rate * 0.1)
    frames = []
    silent_chunks = 0
    speaking_started = False
    max_chunks = int(max_duration / 0.1)
    silence_chunks_needed = int(silence_duration / 0.1)
    no_speech_chunks = 0
    no_speech_limit = int(4.0 / 0.1)

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16')
    stream.start()

    for _ in range(max_chunks):
        chunk, _ = stream.read(chunk_size)
        volume = int(np.sqrt(np.mean(chunk.astype(np.float32)**2)))
        frames.append(chunk.tobytes())
        if volume > silence_threshold:
            speaking_started = True
            silent_chunks = 0
            no_speech_chunks = 0
        elif speaking_started:
            silent_chunks += 1
            if silent_chunks >= silence_chunks_needed:
                break
        else:
            no_speech_chunks += 1
            if no_speech_chunks >= no_speech_limit:
                stream.stop()
                stream.close()
                return None

    stream.stop()
    stream.close()

    if not speaking_started:
        return None

    tmp_path = os.path.join(os.path.expanduser("~"), f"jarvis_{int(time.time())}.wav")
    with wave.open(tmp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
    return tmp_path

def listen_for_command():
    global is_listening
    is_listening = True
    set_status("Listening...", "#00ff00")
    tmp_path = record_until_silence()
    is_listening = False
    if tmp_path is None:
        return None
    try:
        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), f),
                model="whisper-large-v3",
                language="en",
                response_format="text"
            )
        try:
            os.remove(tmp_path)
        except:
            pass
        text = transcription.strip()
        if not text:
            return None
        print(f"You: {text}")
        add_chat("You", text)
        return text.lower()
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

def handle_conversation():
    global is_listening, conversation_active
    if conversation_active:
        return
    conversation_active = True
    visual_keywords = ["what is", "what's this", "look at", "identify",
                      "what do you see", "show me", "can you see",
                      "who am i", "what am i", "camera"]
    speak("Sir?")
    while conversation_active:
        try:
            is_listening = True
            command = listen_for_command()
            if not conversation_active:
                break
            if command is None:
                continue
            if any(q in command for q in ["goodbye", "bye", "stop", "exit"]):
                speak("Goodbye Sir, I'll be here when you need me.")
                is_listening = False
                conversation_active = False
                return
            if any(kw in command for kw in visual_keywords):
                speak("Analyzing visual input, Sir.")
                reply = ask_jarvis_vision(command)
            else:
                reply = ask_jarvis(command)
            if conversation_active:
                add_chat("JARVIS", reply)
                speak(reply)
        except Exception as e:
            print(f"Error: {e}")
    is_listening = False
    conversation_active = False

def listen_for_wake_word():
    global is_listening
    print("Say 'Hey Jarvis' to wake me up...")
    while True:
        if is_speaking or conversation_active:
            time.sleep(0.2)
            continue
        try:
            tmp_path = record_until_silence(
                silence_threshold=600,
                silence_duration=1.5,
                max_duration=5
            )
            if tmp_path is None:
                continue
            with open(tmp_path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    file=(os.path.basename(tmp_path), f),
                    model="whisper-large-v3",
                    language="en",
                    response_format="text"
                )
            try:
                os.remove(tmp_path)
            except:
                pass
            text = transcription.strip().lower()
            print(f"Heard: {text}")
            if "hey jarvis" in text or ("hey" in text and "jarvis" in text):
                if not conversation_active:
                    threading.Thread(target=handle_conversation, daemon=True).start()
        except Exception as e:
            print(f"Wake error: {e}")

def send_text_message(event=None):
    msg = text_input.get().strip()
    if not msg:
        return
    text_input.delete(0, tk.END)
    add_chat("You", msg)
    def process():
        visual_keywords = ["what is", "what's this", "look at", "identify",
                          "what do you see", "show me", "can you see",
                          "see me", "look", "camera", "who am i", "what am i"]
        if any(kw in msg.lower() for kw in visual_keywords):
            speak("Analyzing visual input, Sir.")
            reply = ask_jarvis_vision(msg)
        else:
            reply = ask_jarvis(msg)
        add_chat("JARVIS", reply)
        speak(reply)
    threading.Thread(target=process, daemon=True).start()

def update_camera():
    global cap
    if not camera_visible:
        root.after(100, update_camera)
        return
    ret, frame = cap.read()
    if ret:
        if is_speaking:
            cv2.rectangle(frame, (0, 0), (frame.shape[1]-1, frame.shape[0]-1), (0, 165, 255), 3)
            cv2.putText(frame, "JARVIS Speaking...", (10, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        elif is_listening:
            cv2.rectangle(frame, (0, 0), (frame.shape[1]-1, frame.shape[0]-1), (0, 255, 0), 3)
            cv2.putText(frame, "Listening...", (10, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Say: Hey Jarvis", (10, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((480, 360))
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.config(image=imgtk)
    root.after(30, update_camera)

def build_gui():
    global root, chat_frame_inner, chat_canvas, status_label
    global camera_label, camera_frame, text_input, toggle_cam_btn

    root = tk.Tk()
    root.title("JARVIS - Virtual AI Assistant")
    root.configure(bg="#0a0a0a")
    root.geometry("1100x700")
    root.resizable(False, False)

    # Title
    title = tk.Label(root, text="J.A.R.V.I.S", font=("Courier", 22, "bold"),
                     bg="#0a0a0a", fg="#00bfff")
    title.pack(pady=(10, 0))
    subtitle = tk.Label(root, text="Just A Rather Very Intelligent System",
                        font=("Courier", 9), bg="#0a0a0a", fg="#444444")
    subtitle.pack()

    # Buttons row
    btn_row = tk.Frame(root, bg="#0a0a0a")
    btn_row.pack(pady=(6, 0))

    toggle_cam_btn = tk.Button(btn_row, text="📷 Hide Camera",
                               font=("Helvetica", 9, "bold"),
                               bg="#1a1a1a", fg="#aaaaaa",
                               bd=0, padx=10, pady=4,
                               cursor="hand2",
                               command=toggle_camera)
    toggle_cam_btn.pack(side=tk.LEFT, padx=5)

    stop_btn = tk.Button(btn_row, text="⏹ Stop Response",
                         font=("Helvetica", 9, "bold"),
                         bg="#4a0000", fg="#ff4444",
                         bd=0, padx=10, pady=4,
                         cursor="hand2",
                         command=lambda: threading.Thread(
                             target=stop_jarvis_speaking, daemon=True).start())
    stop_btn.pack(side=tk.LEFT, padx=5)

    main_frame = tk.Frame(root, bg="#0a0a0a")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Right — Chat (packed first so it always stays left when camera hides)
    camera_frame = tk.Frame(main_frame, bg="#0a0a0a")
    camera_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

    right_frame = tk.Frame(main_frame, bg="#0a0a0a")
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    camera_label = tk.Label(camera_frame, bg="#000000", width=480, height=360)
    camera_label.pack()

    status_label = tk.Label(camera_frame, text="Initializing...",
                            font=("Courier", 11), bg="#0a0a0a", fg="#888888")
    status_label.pack(pady=5)

    log_label = tk.Label(camera_frame, text=f"Saving to: {log_file}",
                         font=("Courier", 8), bg="#0a0a0a", fg="#333333")
    log_label.pack()

    chat_header = tk.Label(right_frame, text="Conversation",
                           font=("Helvetica", 12, "bold"),
                           bg="#0a0a0a", fg="#00bfff")
    chat_header.pack()

    chat_container = tk.Frame(right_frame, bg="#0d0d0d",
                              highlightthickness=1, highlightbackground="#1a1a1a")
    chat_container.pack(fill=tk.BOTH, expand=True)

    chat_canvas = tk.Canvas(chat_container, bg="#0d0d0d", bd=0,
                            highlightthickness=0)
    scrollbar = tk.Scrollbar(chat_container, orient="vertical",
                             command=chat_canvas.yview)
    chat_canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    chat_frame_inner = tk.Frame(chat_canvas, bg="#0d0d0d")
    chat_canvas_window = chat_canvas.create_window((0, 0), window=chat_frame_inner, anchor="nw")

    def on_frame_configure(e):
        chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))

    def on_canvas_configure(e):
        chat_canvas.itemconfig(chat_canvas_window, width=e.width)

    chat_frame_inner.bind("<Configure>", on_frame_configure)
    chat_canvas.bind("<Configure>", on_canvas_configure)

    # Input area
    input_frame = tk.Frame(right_frame, bg="#0a0a0a")
    input_frame.pack(fill=tk.X, pady=(8, 0))

    text_input = tk.Entry(input_frame, bg="#111111", fg="#ffffff",
                          font=("Helvetica", 11), bd=0,
                          highlightthickness=1,
                          highlightbackground="#00bfff",
                          insertbackground="#ffffff")
    text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 6))
    text_input.bind("<Return>", send_text_message)
    text_input.focus()

    send_btn = tk.Button(input_frame, text="Send ➤",
                         font=("Helvetica", 10, "bold"),
                         bg="#00bfff", fg="#000000",
                         bd=0, padx=14, pady=8,
                         cursor="hand2",
                         command=send_text_message)
    send_btn.pack(side=tk.LEFT)

    return root

def main():
    global cap, root

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

    root = build_gui()

    wake_thread = threading.Thread(target=listen_for_wake_word, daemon=True)
    wake_thread.start()

    root.after(1000, update_camera)

    intro = "JARVIS online. Say Hey Jarvis to wake me up, or type below. How can I assist you Sir?"
    add_chat("JARVIS", intro)
    root.after(1500, lambda: threading.Thread(
        target=speak, args=(intro,), daemon=True).start())

    set_status("Say: Hey Jarvis", "#888888")
    root.mainloop()
    cap.release()

if __name__ == "__main__":
    main()