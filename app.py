```python
import os
import uuid
import shutil
import wave
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from dotenv import load_dotenv
from pydub import AudioSegment

import assemblyai as aai

from google import genai
from google.genai import types


load_dotenv()


# --------------------------------------------------
# API KEYS
# --------------------------------------------------

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not ASSEMBLYAI_API_KEY:
    raise RuntimeError(
        "Set ASSEMBLYAI_API_KEY in your .env or environment"
    )

if not GEMINI_API_KEY:
    raise RuntimeError(
        "Set GEMINI_API_KEY in your .env or environment"
    )


aai.settings.api_key = ASSEMBLYAI_API_KEY

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)


LANGUAGE_OPTIONS = {
    "Select": None,
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr"
}


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi"
}


# --------------------------------------------------
# SAVE UPLOADED AUDIO AND CONVERT TO WAV
# --------------------------------------------------

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

        audio.export(
            wav_path,
            format="wav"
        )

    except Exception:

        shutil.copy(
            orig_path,
            wav_path
        )

    return str(wav_path), str(orig_path)


# --------------------------------------------------
# ASSEMBLYAI SPEECH-TO-TEXT
# --------------------------------------------------

def transcribe_audio(wav_path):

    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig(
        language_detection=True
    )

    transcription = transcriber.transcribe(
        wav_path,
        config=config
    )

    if transcription.status == aai.TranscriptStatus.error:

        raise RuntimeError(
            f"Transcription error: {transcription.error}"
        )

    text = transcription.text

    detected_language = getattr(
        transcription,
        "detected_language",
        None
    )

    return text, detected_language


# --------------------------------------------------
# GEMINI TEXT TRANSLATION
# --------------------------------------------------

def translate_text_core(text, target_lang_code):

    if not target_lang_code:
        return text

    target_language = LANGUAGE_NAMES.get(
        target_lang_code,
        target_lang_code
    )

    prompt = f"""
Translate the following text into {target_language}.

Important instructions:
- Translate only the text.
- Do not explain the translation.
- Do not add extra information.
- Preserve the original meaning.
- Keep names, numbers, and important technical terms accurate.

Text:
{text}
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    translated_text = response.text

    if not translated_text:
        raise RuntimeError(
            "Gemini returned an empty translation."
        )

    return translated_text.strip()


# --------------------------------------------------
# GEMINI TEXT-TO-SPEECH
# --------------------------------------------------

def generate_tts(text, lang_code):

    uid = uuid.uuid4().hex

    out_wav = TEMP_DIR / f"{uid}.wav"

    # Gemini TTS voice
    voice_name = "Kore"

    language_instruction = {
        "en": "Speak in English.",
        "hi": "Speak in Hindi.",
        "mr": "Speak in Marathi."
    }.get(
        lang_code,
        "Speak naturally."
    )

    prompt = f"{language_instruction}\n\n{text}"

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            )
        )
    )

    # Get generated PCM audio
    audio_data = (
        response
        .candidates[0]
        .content
        .parts[0]
        .inline_data
        .data
    )

    # Save PCM data as WAV
    with wave.open(str(out_wav), "wb") as wf:

        wf.setnchannels(1)

        wf.setsampwidth(2)

        wf.setframerate(24000)

        wf.writeframes(audio_data)

    return str(out_wav)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# --------------------------------------------------
# SERVE GENERATED AUDIO
# --------------------------------------------------

@app.route("/generated/<path:filename>")
def generated_file(filename):

    return send_from_directory(
        str(TEMP_DIR),
        filename,
        as_attachment=False
    )


# --------------------------------------------------
# TEXT -> TEXT TRANSLATION
# --------------------------------------------------

@app.route("/api/translate_text", methods=["POST"])
def api_translate_text():

    data = request.json or {}

    text = (
        data.get("text") or ""
    ).strip()

    target = data.get("language")

    if not text:

        return jsonify({
            "error": "No text provided"
        }), 400

    if not target:

        return jsonify({
            "error": "No target language selected"
        }), 400

    target_code = LANGUAGE_OPTIONS.get(
        target
    )

    if not target_code:

        return jsonify({
            "error": "Invalid target language"
        }), 400

    try:

        translated = translate_text_core(
            text,
            target_code
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    return jsonify({
        "translated_text": translated
    })


# --------------------------------------------------
# TEXT -> SPEECH
# --------------------------------------------------

@app.route("/api/play_text_audio", methods=["POST"])
def api_play_text_audio():

    data = request.json or {}

    text = (
        data.get("text") or ""
    ).strip()

    if not text:

        return jsonify({
            "error": "No text provided"
        }), 400

    # Detect language using Gemini
    try:

        detection_response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Identify the language of the following text.

Return ONLY one language code:
en = English
hi = Hindi
mr = Marathi

Text:
{text}
"""
        )

        lang = (
            detection_response.text
            .strip()
            .lower()
        )

        if lang not in ["en", "hi", "mr"]:
            lang = "en"

    except Exception:

        lang = "en"

    try:

        wav = generate_tts(
            text,
            lang
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    rel = url_for(
        "generated_file",
        filename=Path(wav).name
    )

    return jsonify({
        "audio_url": rel
    })


# --------------------------------------------------
# AUDIO -> TRANSCRIBE -> TRANSLATE -> TTS
# --------------------------------------------------

@app.route("/api/translate_audio", methods=["POST"])
def api_translate_audio():

    if "audio" not in request.files:

        return jsonify({
            "error": "No audio provided"
        }), 400

    f = request.files["audio"]

    language = request.form.get(
        "language"
    )

    target_code = LANGUAGE_OPTIONS.get(
        language
    )

    # ----------------------------------------------
    # Save audio
    # ----------------------------------------------

    try:

        wav_path, orig = save_audio_blob(f)

    except Exception as e:

        return jsonify({
            "error": f"Failed to save audio: {e}"
        }), 500

    # ----------------------------------------------
    # Speech to Text
    # ----------------------------------------------

    try:

        text, detected_lang = transcribe_audio(
            wav_path
        )

    except Exception as e:

        return jsonify({
            "error": f"Transcription failed: {e}"
        }), 500

    # ----------------------------------------------
    # Gemini Translation
    # ----------------------------------------------

    try:

        translated = (
            translate_text_core(
                text,
                target_code
            )
            if target_code
            else text
        )

    except Exception as e:

        return jsonify({
            "error": f"Translation failed: {e}"
        }), 500

    # ----------------------------------------------
    # Gemini TTS
    # ----------------------------------------------

    audio_url = None

    if target_code:

        try:

            wav = generate_tts(
                translated,
                target_code
            )

            audio_url = url_for(
                "generated_file",
                filename=Path(wav).name
            )

        except Exception as e:

            print(
                f"Gemini TTS failed: {e}"
            )

            audio_url = None

    # ----------------------------------------------
    # Response
    # ----------------------------------------------

    return jsonify({

        "transcribed_text": text,

        "translated_text": translated,

        "audio_url": audio_url,

        "detected_language": detected_lang
    })


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )

