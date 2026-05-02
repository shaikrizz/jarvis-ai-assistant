# J.A.R.V.I.S - Virtual AI Assistant

> Just A Rather Very Intelligent System

A fully functional AI-powered Virtual Assistant built with Python, featuring real-time voice interaction, camera vision analysis, and a modern chat interface — inspired by JARVIS from Iron Man.

---

## Features

| Feature | Description |
|---|---|
| 🎤 Voice Input | Speak naturally — powered by Groq Whisper AI for high accuracy |
| 🔊 Voice Output | Human-like female voice using Microsoft Edge TTS |
| 👁️ Vision Analysis | Real-time camera feed analysis on demand |
| 💬 Chat Interface | Modern bubble chat UI for text conversations |
| 🧠 AI Brain | Powered by Groq LLaMA 3.3 70B for intelligent responses |
| 📷 Live Camera | Live camera feed with hide/show toggle |
| 💾 Auto Save | All conversations automatically saved to file |
| ⏹️ Stop Response | Stop JARVIS mid-speech anytime |
| 🌐 Wake Word | Say "Hey Jarvis" to activate hands-free |
| 🌙 Dark Theme | Sleek futuristic dark UI |

---

## How It Works

1. Say **"Hey Jarvis"** to wake up the assistant
2. Speak your command or question naturally
3. JARVIS listens, thinks, and replies with voice and text
4. Say **"Jarvis what do you see?"** for camera vision analysis
5. Type in the chat box for text-based interaction
6. Say **"Goodbye"** to end the conversation

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Core programming language |
| Groq API (LLaMA 3.3 70B) | AI brain for intelligent responses |
| Groq Whisper Large V3 | High accuracy voice recognition |
| Groq LLaMA 4 Scout | Vision analysis |
| Microsoft Edge TTS | Human-like voice output |
| OpenCV | Live camera feed |
| Tkinter | GUI interface |
| SoundDevice | Audio recording |
| NumPy | Audio processing |

---

## Installation

### Prerequisites
- Python 3.11
- Groq API key (free at https://console.groq.com)
- Webcam
- Microphone

### Step 1 - Clone the repository
git clone https://github.com/shaikrizz/jarvis-ai-assistant.git
cd jarvis-ai-assistant

### Step 2 - Install dependencies
pip install opencv-python speechrecognition groq pillow sounddevice scipy edge-tts numpy

### Step 3 - Run
python jarvis_app.py

---

## Project Structure

jarvis-ai-assistant/
├── jarvis_app.py          # Main application file
└── README.md              # Project documentation

---

## Screenshots

Main Interface:
- Left: Chat panel with bubble UI
- Right: Live camera feed with status indicators
- Green border: JARVIS is listening
- Orange border: JARVIS is speaking

---

## Built By

Shaik Rizz

Built as part of the Plant Green Inertia Virtual AI Assistant project submission.

---

## License

This project is open source and available for educational purposes.