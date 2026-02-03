# 🌐 Web Language Translator

A **single-page web application** that performs **real-time language translation** using voice and text — converted from a Python Tkinter desktop application into a modern web-based system.

This application provides **Audio, Text, and Speech translation features in one unified interface**, without any file upload. All audio input is captured live using the microphone.

---

## 🚀 Features

### 🎙️ Audio to Text Translation
- Live audio recording through browser microphone
- Speech-to-text using **AssemblyAI**
- Automatic language detection
- Translation into selected language

### 🔊 Audio to Audio Translation
- Speak in one language
- Get translated speech output
- Pipeline: Audio → Text → Translation → Text-to-Speech

### 📝 Text to Text Translation
- Manual text input
- Instant translation into selected language

### 🔈 Text to Speech
- Converts typed or translated text into speech
- Audio playback directly in browser

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- AssemblyAI (Speech Recognition)
- translate (Text Translation)
- gTTS (Text-to-Speech)

### Frontend
- HTML5
- CSS
- JavaScript
- MediaRecorder API (Live audio capture)

### Deployment
- GitHub
- Render

---

## 📁 Project Structure

```
WebLanguageTranslator/
│── app.py
│── requirements.txt
│── README.md
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   ├── script.js
│   └── icons / images
```

---

## 🔐 Environment Variables

The application requires an AssemblyAI API key.

```
ASSEMBLYAI_API_KEY=your_api_key_here
```

❗ Never hardcode API keys inside source files.

---

## ▶️ Run Locally

### Clone Repository
```
git clone https://github.com/Omkar994-star/WebLanguageTranslator.git
cd WebLanguageTranslator
```

### Create Virtual Environment (Optional)
```
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies
```
pip install -r requirements.txt
```

### Set Environment Variable

**Windows**
```
setx ASSEMBLYAI_API_KEY "your_api_key_here"
```

**Linux / macOS**
```
export ASSEMBLYAI_API_KEY="your_api_key_here"
```

### Run Application
```
python app.py
```

Open in browser:
```
http://127.0.0.1:5000
```

---

## 🌍 Deploy on Render

### Render Configuration

- Service Type: Web Service
- Runtime: Python
- Build Command:
```
pip install -r requirements.txt
```
- Start Command:
```
python app.py
```
- Environment Variable:
```
ASSEMBLYAI_API_KEY
```
- Plan: Free

---

## ❗ Important Notes

- Browser microphone permission is required
- No audio file upload support
- Internet connection needed for AssemblyAI
- Render free services may sleep when idle

---

## 👨‍💻 Author

**Omkar**  
Engineering Student | Python | AI | Web Development  

GitHub:  
https://github.com/Omkar994-star

---

## ⭐ Future Enhancements

- Additional language support
- Streaming transcription
- Mobile-responsive UI
- Translation history
- User authentication

---

⭐ Star the repository if you find this project useful!
