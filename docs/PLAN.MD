Here's a clean skeleton cut into 3 parts for your team:

---

## Part 1 — **Polo**: Agent Core & Prompt Management

```python
# agent.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentState:
    name: str  # "girl" | "guy"
    personality: str
    memory: list[str]
    sentiment_score: float

def build_prompt(state: AgentState, message: str, sentiment: float) -> str:
    """Build dynamic prompt based on state and sentiment"""
    ...

def call_llm(prompt: str, api_key: str) -> str:
    """Call Mistral API, return text response"""
    ...

def call_poetry_agent(context: str) -> str:
    """Sub-agent: generate a love poem"""
    ...

def call_memory_agent(state: AgentState, message: str) -> Optional[str]:
    """Sub-agent: retrieve relevant memory"""
    ...

def update_sentiment(current: float, message: str) -> float:
    """Score message sentiment, return updated score"""
    ...

def should_trigger_tool(message: str, sentiment: float) -> Optional[str]:
    """Return tool name to call, or None"""
    ...
```

---

## Part 2 — **Puch**: Voice I/O & Main Loop

```python
# voice.py + main.py
def transcribe_audio(audio_bytes: bytes, api_key: str) -> str:
    """Voxtral: audio → text"""
    ...

def speak(text: str, voice_id: str, elevenlabs_key: str) -> bytes:
    """ElevenLabs: text → audio bytes, play it"""
    ...

def record_until_silence() -> bytes:
    """Capture mic input, return audio bytes"""
    ...

# main.py
def run_agent_loop(
    my_state: AgentState,
    role: str,  # "girl" | "guy"
    mistral_key: str,
    elevenlabs_key: str,
    wb_run,  # W&B run object
):
    """
    Main loop for one computer:
    1. Listen (Voxtral) or receive message over socket
    2. Build prompt + call LLM
    3. Speak response (ElevenLabs)
    4. Send text to other computer over socket
    5. Log to W&B
    6. Repeat
    """
    ...

def send_message(text: str, host: str, port: int) -> None:
    """Send text to other computer via socket"""
    ...

def receive_message(port: int) -> str:
    """Blocking receive from other computer"""
    ...
```

---

## Part 3 — **Theo**: Frontend & W&B Tracking

```python
# ui.py
import pygame

def init_display(role: str) -> pygame.Surface:
    """Init pygame window for girl or guy"""
    ...

def render_character(screen: pygame.Surface, role: str, sentiment: float) -> None:
    """Draw pixel art character, animate based on sentiment"""
    ...

def render_speech_bubble(screen: pygame.Surface, text: str) -> None:
    """Show current spoken text"""
    ...

def render_mood(screen: pygame.Surface, sentiment: float) -> None:
    """Color overlay / hearts based on sentiment score"""
    ...

# tracking.py
import wandb

def init_tracking(project: str, run_name: str) -> wandb.run:
    """weave.init + wandb.init"""
    ...

def log_exchange(
    run,
    turn: int,
    speaker: str,
    prompt: str,
    response: str,
    sentiment: float,
    tool_used: Optional[str],
) -> None:
    """Log one turn to W&B"""
    ...
```

---

## Interaction Flow

```
Computer 1 (Girl)                    Computer 2 (Guy)
─────────────────                    ────────────────
receive_message()        ←socket←    send_message()
build_prompt()                       build_prompt()
call_llm()                           call_llm()
speak()                              speak()
send_message()           →socket→    receive_message()
log_exchange()                       log_exchange()
render_character()                   render_character()
```

Each computer runs `main.py` with `role="girl"` or `role="guy"`. The socket is the only bridge between them — keeping it simple and real-time.
