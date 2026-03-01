import asyncio
import math
import os
import struct
from typing import AsyncIterator

import certifi
from dotenv import load_dotenv
from mistralai import Mistral
from mistralai.extra.exceptions import RealtimeTranscriptionException
from mistralai.extra.realtime import UnknownRealtimeEvent
from mistralai.models import (
    AudioFormat,
    RealtimeTranscriptionError,
    RealtimeTranscriptionSessionCreated,
    TranscriptionStreamDone,
    TranscriptionStreamTextDelta,
)

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
# Force a known CA bundle for TLS validation (helps on macOS Python cert-chain issues).
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
client = Mistral(api_key=MISTRAL_API_KEY)
audio_format = AudioFormat(encoding="pcm_s16le", sample_rate=16000)


def rms(data: bytes) -> float:
    """Compute RMS energy of a PCM s16le chunk."""
    count = len(data) // 2
    if count == 0:
        return 0.0
    samples = struct.unpack(f"<{count}h", data)
    return math.sqrt(sum(s * s for s in samples) / count)


async def iter_microphone(
    *,
    sample_rate: int,
    chunk_duration_ms: int,
    silence_timeout_s: float = 3.0,
    noise_calibration_s: float = 1.0,
    speech_ratio: float = 2.5,
) -> AsyncIterator[bytes]:
    import pyaudio

    p = pyaudio.PyAudio()
    chunk_samples = int(sample_rate * chunk_duration_ms / 1000)
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_samples,
    )
    loop = asyncio.get_running_loop()

    # --- Calibration phase: measure ambient noise floor ---
    calibration_chunks = max(1, int(noise_calibration_s * 1000 / chunk_duration_ms))
    print(f"[Calibrating noise floor for {noise_calibration_s}s, please stay quiet...]")
    noise_samples = []
    for _ in range(calibration_chunks):
        data = await loop.run_in_executor(None, stream.read, chunk_samples, False)
        noise_samples.append(rms(data))
    noise_floor = sum(noise_samples) / len(noise_samples)
    silence_threshold = noise_floor * speech_ratio
    print(f"[Noise floor: {noise_floor:.1f}, silence threshold set to: {silence_threshold:.1f}]")
    print("Listening...")

    silence_since: float | None = None
    speech_started = False

    try:
        while True:
            data = await loop.run_in_executor(None, stream.read, chunk_samples, False)
            yield data

            energy = rms(data)
            now = loop.time()

            if energy >= silence_threshold:
                if not speech_started:
                    speech_started = True
                    print("[Speech detected]")
                silence_since = None
            elif speech_started:
                if silence_since is None:
                    silence_since = now
                elif now - silence_since >= silence_timeout_s:
                    print(f"\n[Silence detected for {silence_timeout_s}s, stopping.]")
                    break

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


async def listen_and_transcribe(
    *,
    chunk_duration_ms: int = 480,
    target_streaming_delay_ms: int = 1000,
    timeout_seconds: int = 10,
    silence_timeout_s: float = 3.0,
    noise_calibration_s: float = 1.0,
    speech_ratio: float = 2.5,
) -> str:
    audio_stream = iter_microphone(
        sample_rate=audio_format.sample_rate,
        chunk_duration_ms=chunk_duration_ms,
        silence_timeout_s=silence_timeout_s,
        noise_calibration_s=noise_calibration_s,
        speech_ratio=speech_ratio,
    )
    transcribed_text = []
    try:
        async for event in client.audio.realtime.transcribe_stream(
            audio_stream=audio_stream,
            model="voxtral-mini-transcribe-realtime-2602",
            audio_format=audio_format,
            target_streaming_delay_ms=target_streaming_delay_ms,
        ):
            if isinstance(event, RealtimeTranscriptionSessionCreated):
                print("Session created.")
            elif isinstance(event, TranscriptionStreamTextDelta):
                transcribed_text.append(event.text)
                print(event.text, end="", flush=True)
            elif isinstance(event, TranscriptionStreamDone):
                print("Transcription done.")
                break
            elif isinstance(event, RealtimeTranscriptionError):
                print(f"Error: {event}")
                break
            elif isinstance(event, UnknownRealtimeEvent):
                print(f"Unknown event: {event}")
                continue
    except RealtimeTranscriptionException as e:
        print(f"Realtime transcription connection failed: {e}")
        print(
            "TLS cert check failed. On macOS, run: "
            "'/Applications/Python\\ 3.12/Install\\ Certificates.command' "
            "then retry with uv."
        )
        return ""
    except KeyboardInterrupt:
        print("Stopping...")
    return "".join(transcribed_text)
