import os
import uuid
import base64
import wave
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from groq import Groq
from google import genai


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set.")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set.")


# =========================================================
# CLIENTS
# =========================================================

groq_client = Groq(api_key=GROQ_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# MODELS
# =========================================================

GROQ_STT_MODEL = "whisper-large-v3"
GROQ_TRANSLATION_MODEL = "openai/gpt-oss-20b"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)


# =========================================================
# LANGUAGES
# =========================================================

LANGUAGE_OPTIONS = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese": "cmn",
    "French": "fr",
    "German": "de",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Nepali": "ne",
    "Odia": "or",
    "Punjabi": "pa",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Tamil": "ta",
    "Telugu": "te",
    "Urdu": "ur",
    "Japanese": "ja",
    "Korean": "ko",
    "Italian": "it",
    "Dutch": "nl",
    "Turkish": "tr",
    "Vietnamese": "vi",
    "Indonesian": "id",
    "Thai": "th",
    "Polish": "pl",
    "Ukrainian": "uk",
    "Greek": "el",
    "Hebrew": "he",
    "Persian": "fa",
    "Romanian": "ro",
    "Swedish": "sv",
    "Danish": "da",
    "Finnish": "fi",
    "Norwegian": "nb",
    "Czech": "cs",
    "Hungarian": "hu",
    "Slovak": "sk",
    "Bulgarian": "bg",
    "Croatian": "hr",
    "Serbian": "sr",
    "Malay": "ms",
    "Filipino": "fil",
    "Swahili": "sw",
    "Sinhala": "si",
    "Punjabi": "pa",
    "Tamil": "ta",
    "Telugu": "te",
    "Konkani": "kok",
    "Maithili": "mai",
    "Sindhi": "sd",
    "Assamese": "bn"
}


# =========================================================
# LANGUAGE NAMES
# =========================================================

LANGUAGE_NAMES = {
    code: name
    for name, code in LANGUAGE_OPTIONS.items()
}


# =========================================================
# SAVE AUDIO
# =========================================================

def save_audio(file_storage):
    """
    Save browser-recorded audio without converting it.

    The browser normally sends WebM audio.
    Groq Whisper supports WebM directly.
    """

    extension = ".webm"

    original_name = file_storage.filename or ""

    if "." in original_name:
        extension = Path(original_name).suffix.lower()

    allowed_extensions = {
        ".webm",
        ".wav",
        ".mp3",
        ".m4a",
        ".mp4",
        ".mpeg",
        ".mpga",
        ".ogg",
        ".flac"
    }

    if extension not in allowed_extensions:
        extension = ".webm"

    filename = f"{uuid.uuid4().hex}{extension}"

    audio_path = TEMP_DIR / filename

    file_storage.save(audio_path)

    return audio_path


# =========================================================
# TRANSCRIBE AUDIO - GROQ WHISPER
# =========================================================

def transcribe_audio(audio_path):
    """
    Transcribe multilingual audio using Groq Whisper.

    The language is not manually specified so Whisper can
    automatically detect the spoken language.
    """

    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    result = groq_client.audio.transcriptions.create(
        file=(
            audio_path.name,
            audio_bytes
        ),
        model=GROQ_STT_MODEL,
        response_format="json",
        temperature=0.0
    )

    text = getattr(result, "text", None)

    if not text:
        raise RuntimeError("Groq Whisper did not return transcription.")

    return text.strip()


# =========================================================
# TRANSLATE TEXT - GROQ LLM
# =========================================================

def translate_text_core(text, target_lang_code):
    """
    Translate text into the selected target language.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    target_language = LANGUAGE_NAMES.get(
        target_lang_code,
        target_lang_code
    )

    system_prompt = f"""
You are a professional multilingual translator.

Translate the user's text into {target_language}.

Rules:
- Return ONLY the translated text.
- Do not explain the translation.
- Do not add quotation marks.
- Preserve the original meaning.
- Preserve names, numbers and important technical terms.
- Do not summarize.
- Do not add extra information.
"""

    response = groq_client.chat.completions.create(
        model=GROQ_TRANSLATION_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0,
        max_completion_tokens=2048,
        include_reasoning=False
    )

    translated_text = response.choices[0].message.content

    if not translated_text:
        raise RuntimeError("Groq did not return translated text.")

    return translated_text.strip()


# =========================================================
# GENERATE TTS - GEMINI
# =========================================================

def generate_tts(text):
    """
    Generate multilingual speech using Gemini TTS.

    Gemini automatically detects the language of the text.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    prompt = f"""
Read the following text naturally and clearly.

Use the language of the provided text.

Text:
{text}
"""

    interaction = gemini_client.interactions.create(
        model=GEMINI_TTS_MODEL,
        input=prompt,
        response_format={
            "type": "audio"
        },
        generation_config={
            "speech_config": [
                {
                    "voice": "Kore"
                }
            ]
        }
    )

    output_audio = getattr(
        interaction,
        "output_audio",
        None
    )

    if output_audio is None:
        raise RuntimeError("Gemini did not return audio.")

    audio_data = getattr(
        output_audio,
        "data",
        None
    )

    if audio_data is None:
        raise RuntimeError("Gemini audio data is empty.")

    if isinstance(audio_data, str):
        audio_bytes = base64.b64decode(audio_data)
    else:
        audio_bytes = bytes(audio_data)

    filename = f"{uuid.uuid4().hex}.wav"

    output_path = TEMP_DIR / filename

    # Gemini returns PCM audio.
    # Save it as a standard WAV file.
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(audio_bytes)

    return filename


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return render_template(
        "index.html",
        languages=LANGUAGE_OPTIONS
    )


# =========================================================
# SERVE AUDIO
# =========================================================

@app.route("/temp/<filename>")
def serve_audio(filename):
    return send_from_directory(
        TEMP_DIR,
        filename
    )


# =========================================================
# TEXT TRANSLATION
# =========================================================

@app.route("/api/translate_text", methods=["POST"])
def translate_text():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received."
            }), 400

        text = data.get("text", "").strip()
        target_language = data.get("language", "").strip()

        if not text:
            return jsonify({
                "success": False,
                "error": "Please enter some text."
            }), 400

        if not target_language:
            return jsonify({
                "success": False,
                "error": "Please select a target language."
            }), 400

        if target_language not in LANGUAGE_NAMES:
            return jsonify({
                "success": False,
                "error": "Unsupported target language."
            }), 400

        translated_text = translate_text_core(
            text,
            target_language
        )

        return jsonify({
            "success": True,
            "translated_text": translated_text
        })

    except Exception as e:

        print("TEXT TRANSLATION ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# TEXT TO SPEECH
# =========================================================

@app.route("/api/play_text_audio", methods=["POST"])
def play_text_audio():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received."
            }), 400

        text = data.get("text", "").strip()

        if not text:
            return jsonify({
                "success": False,
                "error": "Please enter some text."
            }), 400

        audio_filename = generate_tts(text)

        return jsonify({
            "success": True,
            "audio_url": f"/temp/{audio_filename}"
        })

    except Exception as e:

        print("TEXT TO SPEECH ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# AUDIO TO AUDIO + AUDIO TO TEXT
# =========================================================

@app.route("/api/translate_audio", methods=["POST"])
def translate_audio():

    audio_path = None

    try:

        if "audio" not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio file received."
            }), 400

        target_language = request.form.get(
            "language",
            ""
        ).strip()

        if not target_language:
            return jsonify({
                "success": False,
                "error": "Please select a target language."
            }), 400

        if target_language not in LANGUAGE_NAMES:
            return jsonify({
                "success": False,
                "error": "Unsupported target language."
            }), 400

        audio_file = request.files["audio"]

        if not audio_file.filename:
            return jsonify({
                "success": False,
                "error": "Audio file is empty."
            }), 400

        # Save original browser audio.
        audio_path = save_audio(audio_file)

        # -------------------------------------------------
        # STEP 1: SPEECH TO TEXT
        # -------------------------------------------------

        transcribed_text = transcribe_audio(
            audio_path
        )

        if not transcribed_text:
            return jsonify({
                "success": False,
                "error": "Could not understand the audio."
            }), 400

        # -------------------------------------------------
        # STEP 2: TRANSLATION
        # -------------------------------------------------

        translated_text = translate_text_core(
            transcribed_text,
            target_language
        )

        # -------------------------------------------------
        # STEP 3: TEXT TO SPEECH
        # -------------------------------------------------

        audio_filename = generate_tts(
            translated_text
        )

        return jsonify({
            "success": True,
            "transcribed_text": transcribed_text,
            "translated_text": translated_text,
            "audio_url": f"/temp/{audio_filename}"
        })

    except Exception as e:

        print("AUDIO TRANSLATION ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:

        # Delete uploaded source audio.
        if audio_path and audio_path.exists():

            try:
                audio_path.unlink()

            except Exception:
                pass


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok"
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )