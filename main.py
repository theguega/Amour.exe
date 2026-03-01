import argparse
import asyncio

from voice_interaction.offline_stt import text_to_audio
from voice_interaction.realtime_tts import listen_and_transcribe

voice_list = {"girl": "dn2rTVHQ2BeQJfsX1Pr7", "guy": "QtJDM0PJ8GaUfT83yDRe"}


async def play_audio(audio_path):
    import pygame

    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    pygame.mixer.quit()


async def main():
    while True:
        print("Hello from amour-exe!")
        print("Listening to your voice...")
        transcribed_text = await listen_and_transcribe()
        print("Sending to ElevenLabs")
        audio_path = text_to_audio(transcribed_text, voice_list[args.voice])
        print(f"Audio saved to {audio_path}")
        print("Playing audio...")
        await play_audio(audio_path)
        print("Audio playback completed. Restarting loop...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", choices=["girl", "guy"], default="girl")
    args = parser.parse_args()
    asyncio.run(main())
