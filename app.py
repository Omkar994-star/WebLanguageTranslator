import os
import uuid
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from dotenv import load_dotenv
from pydub import AudioSegment
from gtts import gTTS
from langdetect import detect
from translate import Translator
import assemblyai as aai

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    raise RuntimeError("Set ASSEMBLYAI_API_KEY in your .env or environment")

aai.settings.api_key = ASSEMBLYAI_API_KEY

BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
LANGUAGE_OPTIONS = {"Select": None, "English": "en", "Hindi": "hi", "Marathi": "mr"}

# save uploaded blob and convert to wav (pydub + ffmpeg required)
def save_audio_blob(file_storage):
    uid = uuid.uuid4().hex
    filename = file_storage.filename or f"{uid}.webm"
    ext = Path(filename).suffix if Path(filename).suffix else ".webm"
    orig_path = TEMP_DIR / f"{uid}{ext}"
    file_storage.save(orig_path)
    wav_path = TEMP_DIR / f"{uid}.wav"
    try:
        audio = AudioSegment.from_file(orig_path)
        audio = audio.set_channels(1).set_frame_rate(44100)
        audio.export(wav_path, format="wav")
    except Exception:
        # fallback copy if conversion fails
        shutil.copy(orig_path, wav_path)
    return str(wav_path), str(orig_path)

def transcribe_audio(wav_path):
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(language_detection=True)
    transcription = transcriber.transcribe(wav_path, config=config)
    if transcription.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"Transcription error: {transcription.error}")
    text = transcription.text
    # assemblyai may provide detected language attribute
    detected_language = getattr(transcription, "detected_language", None)
    return text, detected_language

def translate_text_core(text, target_lang_code):
    if not target_lang_code:
        return text
    try:
        src = detect(text)
    except Exception:
        src = "auto"
    translator = Translator(from_lang=src, to_lang=target_lang_code)
    return translator.translate(text)

def generate_tts(text, lang_code):
    uid = uuid.uuid4().hex
    out_mp3 = TEMP_DIR / f"{uid}.mp3"
    tts = gTTS(text=text, lang=lang_code)
    tts.save(str(out_mp3))
    return str(out_mp3)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generated/<path:filename>")
def generated_file(filename):
    return send_from_directory(str(TEMP_DIR), filename, as_attachment=False)

# Translate text (Text->Text)
@app.route("/api/translate_text", methods=["POST"])
def api_translate_text():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    target = data.get("language")  # expects "English"/"Hindi"/"Marathi"
    if not text:
        return jsonify({"error": "No text provided"}), 400
    if not target:
        return jsonify({"error": "No target language selected"}), 400
    target_code = LANGUAGE_OPTIONS.get(target)
    try:
        translated = translate_text_core(text, target_code)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"translated_text": translated})

# Text->Speech (TTS) returns path to mp3 in temp folder
@app.route("/api/play_text_audio", methods=["POST"])
def api_play_text_audio():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    # detect language of the text to speak in same language
    try:
        lang = detect(text)
    except Exception:
        lang = "en"
    try:
        mp3 = generate_tts(text, lang)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    rel = url_for("generated_file", filename=Path(mp3).name)
    return jsonify({"audio_url": rel})

# Audio -> Transcribe + Translate + (TTS)  (Audio-to-Text & Audio-to-Audio)
@app.route("/api/translate_audio", methods=["POST"])
def api_translate_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio provided"}), 400
    f = request.files["audio"]
    language = request.form.get("language")  # expect "English"/"Hindi"/"Marathi"
    target_code = LANGUAGE_OPTIONS.get(language)
    try:
        wav_path, orig = save_audio_blob(f)
    except Exception as e:
        return jsonify({"error": f"Failed to save audio: {e}"}), 500

    try:
        text, detected_lang = transcribe_audio(wav_path)
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {e}"}), 500

    try:
        translated = translate_text_core(text, target_code) if target_code else text
    except Exception as e:
        return jsonify({"error": f"Translation failed: {e}"}), 500

    # generate TTS in target language for Audio->Audio
    audio_url = None
    if target_code:
        try:
            mp3 = generate_tts(translated, target_code)
            audio_url = url_for("generated_file", filename=Path(mp3).name)
        except Exception as e:
            # non-fatal; still return text
            audio_url = None

    return jsonify({
        "transcribed_text": text,
        "translated_text": translated,
        "audio_url": audio_url,
        "detected_language": detected_lang
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
