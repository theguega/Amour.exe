import argparse
import asyncio
import json
from pathlib import Path

VOICE_IDS = {"girl": "dn2rTVHQ2BeQJfsX1Pr7", "man": "QtJDM0PJ8GaUfT83yDRe"}


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


async def play_audio(audio_path: Path) -> None:
    import pygame

    pygame.mixer.init()
    pygame.mixer.music.load(str(audio_path))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    pygame.mixer.quit()


def _fallback_prompt(agent_type: str) -> str:
    if agent_type == "girl":
        return "Hey... I am here with you. Tell me one thing about your day."
    return "Hi, I am listening. What are you feeling right now?"


def _print_turn(prefix: str, result: dict) -> None:
    reply = result["response"]
    tool_calls = [c["tool"] for c in result.get("tool_calls", []) if c.get("called")]
    rel = result.get("relationship", {})
    print(f"[{prefix}] {reply}")
    print(
        "[metrics] "
        f"tools={','.join(tool_calls) if tool_calls else 'none'} "
        f"stage={rel.get('stage', 'n/a')} "
        f"trend={rel.get('trend', 'n/a')} "
        f"score={rel.get('compatibility_score', 'n/a')}"
    )


async def run_voice_loop(args) -> None:
    # Weave init must happen before imports that pull Mistral SDK clients.
    from amour_agent import MistralCaller, MemoryStore, _init_weave, run_turn
    from voice_interaction.offline_stt import text_to_audio
    from voice_interaction.realtime_tts import listen_and_transcribe

    _init_weave(enabled=not args.disable_weave)
    caller = MistralCaller()
    memory_store = MemoryStore(Path(args.memory_file))
    if args.reset_memory:
        memory_store.reset_session(args.session_id)

    incoming = args.seed_text.strip() if args.seed_text else _fallback_prompt(args.type)
    turn_idx = 0

    while args.max_turns <= 0 or turn_idx < args.max_turns:
        turn_idx += 1
        print(f"\n[turn {turn_idx}] input -> {incoming}")

        result = run_turn(
            caller=caller,
            memory_store=memory_store,
            agent_type=args.type,
            input_text=incoming,
            session_id=args.session_id,
        )
        _append_jsonl(Path(args.log_file), result)

        reply = result["response"]
        _print_turn("agent", result)

        print("[tts] generating audio...")
        audio_path = text_to_audio(reply, VOICE_IDS[args.type])
        print(f"[tts] file={audio_path}")
        await play_audio(audio_path)

        print("[stt] listening for the other agent/user...")
        transcribed_text = await listen_and_transcribe(
            silence_timeout_s=args.silence_timeout_s,
            noise_calibration_s=args.noise_calibration_s,
            speech_ratio=args.speech_ratio,
        )
        incoming = transcribed_text.strip()
        if not incoming:
            incoming = _fallback_prompt("man" if args.type == "girl" else "girl")
            print("[stt] empty input detected, using fallback prompt.")


async def run_duplex_loop(args) -> None:
    from amour_agent import MistralCaller, MemoryStore, _init_weave, run_turn

    _init_weave(enabled=not args.disable_weave)
    caller = MistralCaller()
    memory_store = MemoryStore(Path(args.memory_file))
    if args.reset_memory:
        memory_store.reset_session(args.session_id)

    turns = args.max_turns if args.max_turns > 0 else 8
    incoming = args.seed_text.strip() if args.seed_text else _fallback_prompt(args.starter)
    current_agent = args.starter

    print(
        f"[duplex] session={args.session_id} turns={turns} starter={current_agent} "
        f"log={args.log_file}"
    )
    for turn_idx in range(1, turns + 1):
        print(f"\n[turn {turn_idx}] {current_agent} hears -> {incoming}")
        result = run_turn(
            caller=caller,
            memory_store=memory_store,
            agent_type=current_agent,
            input_text=incoming,
            session_id=args.session_id,
        )
        _append_jsonl(Path(args.log_file), result)
        _print_turn(current_agent, result)

        incoming = result["response"]
        current_agent = "man" if current_agent == "girl" else "girl"


def parse_args():
    parser = argparse.ArgumentParser(description="Voice runtime loop wired to amour_agent run_turn.")
    parser.add_argument("--type", choices=["girl", "man"], default="girl")
    parser.add_argument("--duplex", action="store_true", help="Run both girl and man in one local loop.")
    parser.add_argument("--starter", choices=["girl", "man"], default="girl")
    parser.add_argument("--session-id", default="voice-session")
    parser.add_argument("--seed-text", default="")
    parser.add_argument("--max-turns", type=int, default=0, help="0 means infinite.")
    parser.add_argument("--log-file", default="logs/voice_runs.jsonl")
    parser.add_argument("--memory-file", default="logs/memory_store.json")
    parser.add_argument("--reset-memory", action="store_true")
    parser.add_argument("--disable-weave", action="store_true")
    parser.add_argument("--silence-timeout-s", type=float, default=3.0)
    parser.add_argument("--noise-calibration-s", type=float, default=1.0)
    parser.add_argument("--speech-ratio", type=float, default=2.5)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.duplex:
        asyncio.run(run_duplex_loop(args))
    else:
        asyncio.run(run_voice_loop(args))
