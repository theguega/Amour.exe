<p align="center">
  <img src="assets/heart.png" alt="Amour.exe" width="80"/>
</p>

<h1 align="center">Amour.exe</h1>

<p align="center">
  <em>"Two computers, two voices, one love story — engineered in real time."</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white" alt="Python 3.12+"/>
  <img src="https://img.shields.io/badge/Mistral_AI-agents_%26_realtime-orange" alt="Mistral AI"/>
  <img src="https://img.shields.io/badge/ElevenLabs-TTS-purple" alt="ElevenLabs"/>
  <img src="https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white" alt="React"/>
</p>

---

An AI-powered love story simulation where two agents — **Girl** and **Man** — fall in love through real-time voice conversation across two separate computers. Built with Mistral AI native agents, ElevenLabs TTS, Voxtral STT, and a retro pixel-art interface.

<p align="center">
  <img src="assets/girl.png" alt="Girl character" width="200"/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/heart.png" alt="heart" width="60"/>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/guy.png" alt="Guy character" width="200"/>
</p>

## How It Works

Each agent runs on a separate computer with its own pixel-art character on screen. They speak aloud via **ElevenLabs** and listen via **Voxtral** real-time speech-to-text. Under the hood, a multi-agent orchestration system drives the conversation forward through a relationship state machine:

```
strangers → curious → flirty → bonded → in_love
```

Agents can delegate to specialized sub-agents mid-conversation:

| Sub-Agent | Role |
|-----------|------|
| **Memory** | Recalls past facts to build continuity ("Remember when you said you loved jazz?") |
| **Seduction** | Romantic strategy & charm lines, adapted to the current relationship stage |
| **Web Search** | Wikipedia lookups for factual questions that come up naturally |

Every turn is scored for **sentiment** and **emotion** (joy, curiosity, nervousness, sadness, anger), which feeds back into the relationship progression and is tracked live in a **Weights & Biases** dashboard.

<p align="center">
  <img src="assets/room.png" alt="Room background" width="600"/>
</p>

## Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Agents | [Mistral AI](https://mistral.ai/) — native agent orchestration with server-side handoffs |
| Voice Output (TTS) | [ElevenLabs](https://elevenlabs.io/) |
| Voice Input (STT) | Voxtral (Mistral realtime API) |
| Relationship Tracking | [Weights & Biases (Weave)](https://wandb.ai/) |
| Frontend | HTML5 pixel-art UIs + React dashboard with Chart.js |
| Communication | WebSockets (real-time state broadcast) |
| Audio | PyAudio + Pygame |

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Node.js (for the dashboard)
- API keys for Mistral AI, ElevenLabs, and Weights & Biases

### Installation

```bash
# Clone the repo
git clone https://github.com/your-org/Amour.exe.git
cd Amour.exe

# Install system dependency (macOS)
brew install pyaudio

# Install Python dependencies
uv sync

# Install dashboard dependencies
cd dashboard && npm install && cd ..
```

### Configuration

Create a `.env` file at the project root:

```env
MISTRAL_API_KEY=your_mistral_key
ELEVENLABS_API_KEY=your_elevenlabs_key
WANDB_API_KEY=your_wandb_key
```

## Usage

### Single Agent (Voice Mode)

Run one agent on each computer. They talk and listen through the speakers/microphone:

```bash
# Computer 1
python main.py --type girl

# Computer 2
python main.py --type man
```

Use `--auto` to automatically start listening after speaking (for the two-computer setup):

```bash
python main.py --type girl --auto --auto-delay 2.5
```

### Duplex Mode (Both Agents Locally)

Run both agents on a single machine for testing — they converse via text with no audio:

```bash
python main.py --duplex --max-turns 20
```

### Replay Mode

Replay a recorded conversation with optional voice playback:

```bash
python main.py --replay --replay-session-id voice-session
```

### Benchmark Mode

Run multiple simulations and measure relationship progression metrics:

```bash
python main.py --duplex --benchmark-runs 5
```

### Dashboard

Real-time visualization of emotions, sentiment, and relationship progression:

```bash
cd dashboard
npm run dev
```

### Key Flags

| Flag | Description |
|------|-------------|
| `--type [girl\|man]` | Which agent to run |
| `--duplex` | Run both agents locally |
| `--auto` | Auto-listen after speaking |
| `--auto-delay N` | Seconds to wait before listening (avoid echo) |
| `--girl-mood [neutral\|open\|rejection]` | Girl personality override |
| `--man-mood [neutral\|open\|rejection]` | Man personality override |
| `--max-turns N` | Limit conversation length |
| `--disable-weave` | Disable W&B tracing |
| `--reset-memory` | Clear session memory |

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                     main.py                          │
│         Voice Runtime & WebSocket Server             │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐    WebSocket     ┌──────────────┐  │
│  │  girl.html   │ ◄────────────► │  dashboard/   │  │
│  │  guy.html    │    (port 8080)  │  (React app)  │  │
│  └─────────────┘                  └──────────────┘  │
│                                                      │
├──────────────────────────────────────────────────────┤
│                  amour_agent.py                       │
│            Agent Core & Orchestration                 │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Memory   │  │  Seduction   │  │  Web Search  │  │
│  │  Agent    │  │  Agent       │  │  Agent       │  │
│  └──────────┘  └──────────────┘  └──────────────┘  │
│                                                      │
├──────────────────────────────────────────────────────┤
│              voice_interaction/                        │
│  ┌──────────────────┐  ┌───────────────────────┐    │
│  │  ElevenLabs TTS   │  │  Voxtral STT          │    │
│  │  (offline_stt.py) │  │  (realtime_tts.py)    │    │
│  └──────────────────┘  └───────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

## Relationship Model

The relationship progresses through five stages based on the Girl's interest score (0.0 → 1.0):

| Score | Stage | Description |
|-------|-------|-------------|
| 0.0 – 0.2 | **Strangers** | Initial awkward small talk |
| 0.2 – 0.4 | **Curious** | Growing interest, asking questions |
| 0.4 – 0.6 | **Flirty** | Playful banter, compliments |
| 0.6 – 0.8 | **Bonded** | Deeper emotional connection |
| 0.8 – 1.0 | **In Love** | Full romantic attachment |

Sentiment analysis, memory usage, and seduction tool calls all influence the score. The Guy's confidence (starts at 1.0) fluctuates based on the Girl's reception.

## Project Structure

```
Amour.exe/
├── main.py                 # Voice runtime, WebSocket server, CLI entry point
├── amour_agent.py          # Agent logic, handoffs, relationship state machine
├── voice_interaction/
│   ├── offline_stt.py      # ElevenLabs TTS wrapper
│   └── realtime_tts.py     # Voxtral real-time STT
├── assets/                 # Pixel art sprites & backgrounds
├── dashboard/              # React + Chart.js analytics dashboard
├── girl.html               # Girl character pixel-art UI
├── guy.html                # Guy character pixel-art UI
├── logs/                   # Conversation logs, memory, benchmarks
├── audio_cache/            # Cached TTS audio (MD5-hashed)
└── docs/                   # Design docs & references
```

## License

Built at a hackathon with love (and a lot of Mistral API calls).
