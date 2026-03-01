import argparse
import asyncio
import json
import time
from pathlib import Path

import websockets

VOICE_IDS = {"girl": "dn2rTVHQ2BeQJfsX1Pr7", "man": "QtJDM0PJ8GaUfT83yDRe"}

CONNECTED_CLIENTS = set()


async def ws_handler(websocket):
    CONNECTED_CLIENTS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CONNECTED_CLIENTS.remove(websocket)


async def start_ws_server():
    print("[ws] starting server on ws://localhost:8080")
    async with websockets.serve(ws_handler, "localhost", 8080):
        await asyncio.Future()  # run forever


async def broadcast(message: dict):
    if not CONNECTED_CLIENTS:
        return
    payload = json.dumps(message)
    await asyncio.gather(
        *[client.send(payload) for client in CONNECTED_CLIENTS], return_exceptions=True
    )


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True, default=str) + "\n")


async def play_audio(audio_path: Path) -> None:
    import pygame

    pygame.mixer.init()
    pygame.mixer.music.load(str(audio_path))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    pygame.mixer.quit()


async def wait_for_spacebar(prompt: str = "[press SPACE to start talking]") -> None:
    import sys
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    print(prompt, flush=True)
    loop = asyncio.get_running_loop()
    try:
        tty.setraw(fd)
        while True:
            ch = await loop.run_in_executor(None, sys.stdin.read, 1)
            if ch == " ":
                break
            if ch in ("\x03", "\x1b"):
                raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _fallback_prompt(agent_type: str) -> str:
    if agent_type == "girl":
        return "Hey... I am here with you. Tell me one thing about your day."
    return "Hi, I am listening. What are you feeling right now?"


def _print_turn(prefix: str, result: dict) -> None:
    reply = result["response"]
    tool_calls = [c["tool"] for c in result.get("tool_calls", []) if c.get("called")]
    rel = result.get("relationship", {})
    native_timing = result.get("native_timing_ms", {})
    trace = result.get("reasoning_traces", {})
    native_events = trace.get("native_handoff_events", []) if isinstance(trace, dict) else []
    timing_parts = []
    if isinstance(native_timing, dict) and native_timing:
        for key in ["prep", "handoff", "parse", "total"]:
            if key in native_timing:
                timing_parts.append(f"{key}_ms={native_timing[key]}")
    timing_txt = f" timing=({' '.join(timing_parts)})" if timing_parts else ""
    event_txt = ""
    if isinstance(native_events, list) and native_events:
        types = [
            e.get("type")
            for e in native_events
            if isinstance(e, dict) and isinstance(e.get("type"), str)
        ]
        if types:
            short_types = ",".join(types[:6]) + ("..." if len(types) > 6 else "")
            event_txt = f" native_events={len(native_events)}[{short_types}]"
    print(f"[{prefix}] {reply}")
    print(
        "[metrics] "
        f"tools={','.join(tool_calls) if tool_calls else 'none'} "
        f"stage={rel.get('stage', 'n/a')} "
        f"trend={rel.get('trend', 'n/a')} "
        f"score={rel.get('compatibility_score', 'n/a')}{timing_txt}{event_txt}"
    )


def _mood_for(agent_type: str, args) -> str:
    return args.girl_mood if agent_type == "girl" else args.man_mood


def log_to_weave(result: dict, duration: float) -> dict:
    import datetime

    from amour_agent import _sentiment_score

    handoffs = []
    freq = {}

    tool_calls = [c for c in result.get("tool_calls", []) if c.get("called")]
    for tool in tool_calls:
        t_name = f"{str(tool.get('tool')).capitalize()} Agent"
        handoffs.append(
            {
                "agent": t_name,
                "timestamp": result.get(
                    "ts", datetime.datetime.now(datetime.timezone.utc).isoformat()
                ),
            }
        )
        freq[t_name] = freq.get(t_name, 0) + 1

    interaction_text = str(result.get("input_text", "")) + " " + str(result.get("response", ""))
    sentiment = _sentiment_score(interaction_text)

    if sentiment >= 0.5:
        dominant_emotion = "joy"
    elif sentiment >= 0.1:
        dominant_emotion = "curiosity"
    elif sentiment > -0.1:
        dominant_emotion = "neutral"
    elif sentiment > -0.5:
        dominant_emotion = "nervousness"
    else:
        dominant_emotion = "sadness"

    spider_chart = {
        "joy": max(0.0, sentiment),
        "nervousness": max(0.0, -sentiment * 0.5),
        "sadness": max(0.0, -sentiment),
        "curiosity": 1.0 - abs(sentiment),
        "anger": 0.0,
    }

    return {
        "agent_handoffs": {"handoffs": handoffs, "frequency": freq},
        "emotion_metrics": {
            "sentiment_score": sentiment,
            "dominant_emotion": dominant_emotion,
            "spider_web": spider_chart,
        },
        "general_stats": {
            "duration": duration,
            "words_spoken_ai": len(str(result.get("response", "")).split()),
            "words_spoken_user": len(str(result.get("input_text", "")).split()),
        },
    }


async def run_voice_loop(args) -> None:
    # Weave init must happen before imports that pull Mistral SDK clients.
    from amour_agent import MemoryStore, MistralCaller, _init_weave, _wrap_weave_op, run_turn
    from voice_interaction.offline_stt import text_to_audio
    from voice_interaction.realtime_tts import listen_and_transcribe

    # Start WebSocket server
    asyncio.create_task(start_ws_server())

    _init_weave(enabled=not args.disable_weave)
    log_to_weave_fn = _wrap_weave_op(log_to_weave) if not args.disable_weave else log_to_weave
    caller = MistralCaller()
    memory_store = MemoryStore(Path(args.memory_file))
    if args.reset_memory:
        memory_store.reset_session(args.session_id)

    incoming = args.seed_text.strip() if args.seed_text else _fallback_prompt(args.type)
    turn_idx = 0

    if args.listen_first and not args.seed_text.strip():
        await wait_for_spacebar("[press SPACE to start your first message]")
        print("[stt] listen-first enabled: waiting for your input...")
        from voice_interaction.realtime_tts import listen_and_transcribe

        heard = await listen_and_transcribe(
            silence_timeout_s=args.silence_timeout_s,
            noise_calibration_s=args.noise_calibration_s,
            speech_ratio=args.speech_ratio,
        )
        incoming = heard.strip() or _fallback_prompt("man" if args.type == "girl" else "girl")

    while args.max_turns <= 0 or turn_idx < args.max_turns:
        turn_idx += 1
        print(f"\n[turn {turn_idx}] input -> {incoming}")

        await broadcast({"action": "typing"})
        t_turn = time.perf_counter()
        result = await asyncio.to_thread(
            run_turn,
            caller=caller,
            memory_store=memory_store,
            agent_type=args.type,
            input_text=incoming,
            session_id=args.session_id,
            mood_profile=_mood_for(args.type, args),
        )
        await broadcast({"action": "stop_typing"})
        turn_duration = time.perf_counter() - t_turn
        log_to_weave_fn(result, turn_duration)
        _append_jsonl(Path(args.log_file), result)

        reply = result["response"]
        rel = result.get("relationship", {})
        await broadcast({"action": "speech", "text": reply})
        await broadcast({
            "action": "sentiment",
            "compatibility": rel.get("compatibility_score", 0.2),
            "stage": rel.get("stage", "strangers"),
            "trend": rel.get("trend", "stable"),
        })
        _print_turn("agent", result)

        print("[tts] generating audio...")
        audio_path = text_to_audio(reply, VOICE_IDS[args.type])
        print(f"[tts] file={audio_path}")
        await play_audio(audio_path)

        # After speaking, wait a bit before hiding bubble, or hide it now?
        # Maybe hide it after audio finishes?
        await broadcast({"action": "stop_typing"})  # Ensure it's hidden after speaking

        await wait_for_spacebar()
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
    from amour_agent import MemoryStore, MistralCaller, _init_weave, _wrap_weave_op, run_turn

    _init_weave(enabled=not args.disable_weave)
    log_to_weave_fn = _wrap_weave_op(log_to_weave) if not args.disable_weave else log_to_weave
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
        t_turn = time.perf_counter()
        t0 = time.perf_counter()
        result = run_turn(
            caller=caller,
            memory_store=memory_store,
            agent_type=current_agent,
            input_text=incoming,
            session_id=args.session_id,
            mood_profile=_mood_for(current_agent, args),
        )
        turn_duration = time.perf_counter() - t_turn
        log_to_weave_fn(result, turn_duration)
        turn_ms = round((time.perf_counter() - t0) * 1000, 1)
        _append_jsonl(Path(args.log_file), result)
        print(f"[duplex] turn={turn_idx} agent={current_agent} elapsed_ms={turn_ms}")
        _print_turn(current_agent, result)

        rel = result.get("relationship", {})
        await broadcast({
            "action": "sentiment",
            "compatibility": rel.get("compatibility_score", 0.2),
            "stage": rel.get("stage", "strangers"),
            "trend": rel.get("trend", "stable"),
        })

        incoming = result["response"]
        current_agent = "man" if current_agent == "girl" else "girl"


async def run_duplex_benchmark(args) -> None:
    from amour_agent import MemoryStore, MistralCaller, _init_weave, _wrap_weave_op, run_turn

    _init_weave(enabled=not args.disable_weave)
    log_to_weave_fn = _wrap_weave_op(log_to_weave) if not args.disable_weave else log_to_weave
    turns = args.max_turns if args.max_turns > 0 else 20
    runs = args.benchmark_runs
    if runs <= 0:
        raise ValueError("--benchmark-runs must be > 0")

    results = []
    global_t0 = time.perf_counter()
    for i in range(1, runs + 1):
        session_id = f"{args.session_id}-bench-{i}"
        caller = MistralCaller()
        memory_store = MemoryStore(Path(args.memory_file))
        memory_store.reset_session(session_id)

        incoming = args.seed_text.strip() if args.seed_text else _fallback_prompt(args.starter)
        current_agent = args.starter
        turn_to_curious = None
        turn_to_flirty = None

        t0 = time.perf_counter()
        for turn_idx in range(1, turns + 1):
            t_turn = time.perf_counter()
            result = run_turn(
                caller=caller,
                memory_store=memory_store,
                agent_type=current_agent,
                input_text=incoming,
                session_id=session_id,
                mood_profile=_mood_for(current_agent, args),
            )
            turn_duration = time.perf_counter() - t_turn
            log_to_weave_fn(result, turn_duration)
            _append_jsonl(Path(args.log_file), result)
            incoming = result["response"]

            if current_agent == "girl":
                stage = result.get("relationship", {}).get("stage", "strangers")
                if turn_to_curious is None and stage in {"curious", "flirty", "bonded", "in_love"}:
                    turn_to_curious = turn_idx
                if turn_to_flirty is None and stage in {"flirty", "bonded", "in_love"}:
                    turn_to_flirty = turn_idx
            current_agent = "man" if current_agent == "girl" else "girl"

        duration_s = round(time.perf_counter() - t0, 2)
        row = {
            "run": i,
            "session_id": session_id,
            "turn_to_curious": turn_to_curious,
            "turn_to_flirty": turn_to_flirty,
            "duration_s": duration_s,
            "total_calls": caller.total_calls,
            "prompt_tokens": caller.total_prompt_tokens,
            "completion_tokens": caller.total_completion_tokens,
        }
        results.append(row)
        print(
            f"[bench run {i}/{runs}] curious={turn_to_curious} flirty={turn_to_flirty} "
            f"duration={duration_s}s calls={caller.total_calls}"
        )

    avg_duration = round(sum(r["duration_s"] for r in results) / len(results), 2)
    success_curious = sum(1 for r in results if r["turn_to_curious"] is not None)
    success_flirty = sum(1 for r in results if r["turn_to_flirty"] is not None)
    summary = {
        "mode": "duplex_benchmark",
        "runs": runs,
        "turns_per_run": turns,
        "girl_mood": args.girl_mood,
        "man_mood": args.man_mood,
        "starter": args.starter,
        "seed_text": args.seed_text,
        "success_to_curious": success_curious,
        "success_to_flirty": success_flirty,
        "avg_duration_s": avg_duration,
        "total_wall_time_s": round(time.perf_counter() - global_t0, 2),
        "results": results,
    }
    _append_jsonl(Path(args.benchmark_log_file), summary)
    print(
        f"[benchmark] runs={runs} curious_success={success_curious}/{runs} "
        f"flirty_success={success_flirty}/{runs} avg_duration={avg_duration}s "
        f"log={args.benchmark_log_file}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Voice runtime loop wired to amour_agent run_turn."
    )
    parser.add_argument("--type", choices=["girl", "man"], default="girl")
    parser.add_argument(
        "--duplex", action="store_true", help="Run both girl and man in one local loop."
    )
    parser.add_argument(
        "--benchmark-runs", type=int, default=0, help="Run N duplex simulations and report metrics."
    )
    parser.add_argument("--starter", choices=["girl", "man"], default="girl")
    parser.add_argument("--session-id", default="voice-session")
    parser.add_argument("--seed-text", default="")
    parser.add_argument("--max-turns", type=int, default=0, help="0 means infinite.")
    parser.add_argument("--log-file", default="logs/voice_runs.jsonl")
    parser.add_argument("--memory-file", default="logs/memory_store.json")
    parser.add_argument("--reset-memory", action="store_true")
    parser.add_argument("--girl-mood", choices=["neutral", "open", "rejection"], default="neutral")
    parser.add_argument("--man-mood", choices=["neutral", "open", "rejection"], default="neutral")
    parser.add_argument("--benchmark-log-file", default="logs/benchmark_runs.jsonl")
    parser.add_argument("--disable-weave", action="store_true")
    parser.add_argument(
        "--listen-first", action="store_true", help="In voice mode, listen before first response."
    )
    parser.add_argument("--silence-timeout-s", type=float, default=3.0)
    parser.add_argument("--noise-calibration-s", type=float, default=1.0)
    parser.add_argument("--speech-ratio", type=float, default=2.5)
    return parser.parse_args()


def _open_html(filename: str):
    import os
    import webbrowser
    from pathlib import Path

    html_path = Path(__file__).parent / filename
    if os.path.exists(html_path):
        webbrowser.open(html_path.as_uri())
    else:
        print(f"Warning: HTML file not found at {html_path}")


def _html_for_agent(agent_type: str) -> str:
    return "guy.html" if agent_type == "man" else "girl.html"


if __name__ == "__main__":
    args = parse_args()

    if args.duplex:
        _open_html("girl.html")
        _open_html("guy.html")
    else:
        _open_html(_html_for_agent(args.type))

    if args.benchmark_runs > 0:
        if not args.duplex:
            raise SystemExit("--benchmark-runs requires --duplex.")
        asyncio.run(run_duplex_benchmark(args))
    elif args.duplex:
        asyncio.run(run_duplex_loop(args))
    else:
        asyncio.run(run_voice_loop(args))
