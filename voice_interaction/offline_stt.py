import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

CACHE_DIR = Path("audio_cache")


def text_to_audio(text: str, voice_id: str) -> Path:
    """
    Converts text to speech using ElevenLabs API and returns the path to the MP3 file.
    Caches the audio by MD5 hash of the text.
    """
    if not client:
        raise ValueError("ELEVENLABS_API_KEY not found. Check your .env file.")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    audio_path = CACHE_DIR / f"{text_hash}.mp3"

    if audio_path.exists():
        return audio_path

    try:
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id, text=text, model_id="eleven_multilingual_v2"
        )

        with open(audio_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)

        return audio_path
    except Exception as e:
        print(f"Error generating audio with ElevenLabs: {e}")
        raise e
