Prompt
Mistral Worldwide Hackathon — Context Profile & Battle Plan
Operator: Pol Bachelin | Generated: Feb 25, 2026 | Status: Pre-Hackathon (3 days out)

1. Context: Who Pol Is
Identity
Pol Bachelin, 24, French-born software engineer based in Los Angeles (DTLA). Currently employed as a Software Engineer at TBSCG/Hartford working remotely with approximately 3 hours of real daily workload — the rest is slack time used strategically for personal projects. Simultaneously serves as CTO of DriveStay a peer-to-peer parking marketplace he architected solo (~90k lines of production Go + React Native code).
Technical Profile
* Primary stack: Go backend, React Native CLI, TypeScript/JavaScript
* Infrastructure: AWS (EKS, Lambda, Cognito, RDS Postgres), Akamai EdgeWorkers, Rancher
* AI/Agents: Daily Claude user, builds agentic workflows, creates meta-prompts for AI agents, familiar with MCP, multi-agent orchestration
* Production-proven: Built DriveStay end-to-end (Go backend, React Native app, Cognito auth, RDS Postgres, Stripe Connect escrow). Built a Solana trading bot with WebSocket architecture and RPC failover. Built DataDash — a Go data access layer that translates API requests into generated SQL queries or NoSQL pipelines (published on GitHub).
* Low-level roots: Epitech background — Corewar compiler + VM in C, game engine in C++ (ECS pattern), Babel (Skype remake with VoIP), BomberVerse (Bomberman with custom engine)
* Current edge: Operates more as an AI-augmented architect than a line-by-line coder. Creates meta-prompts and agent configurations rather than writing every function by hand. This is a strength at a hackathon, not a weakness.
Unfair Advantages for This Hackathon
* French + English bilingual. Mistral is a French company headquartered in Paris. Cultural rapport with Mistral staff and mentors is a real soft advantage.
* Production backend experience. Most hackathon attendees are ML enthusiasts, data scientists, or frontend devs. Pol can ship something that looks and works like a real product, not a notebook demo.
* Insurance domain knowledge from Hartford/TBSCG — enterprise pain points, compliance, document processing.
* Crypto/DeFi experience from the Solana bot — real-time event processing, financial infrastructure.
* Marketplace dynamics from DriveStay — payments, escrow, multi-sided platform design.
* Competitive athlete. 8-1 amateur boxing record. Performs under pressure, physically and mentally conditioned for endurance events.
* DataDash already exists on his GitHub — a Go data access layer for SQL generation.

2. What the Mistral Worldwide Hackathon Is
Event Details
* Dates: Saturday Feb 28 (9am) → Sunday Mar 1 (7pm)
* Location: 1885 Mission St, San Francisco
* Format: 48-hour overnight hackathon, teams of 1-4
* Total Prize Pool: $200,000+ across 7 cities worldwide
Prize Structure
SF Local: | Place | Cash | Credits | Extras | |-------|------|---------|--------| | 1st | $1,500 | $3,000 Mistral | + sponsor prizes | | 2nd | $1,000 | $2,000 Mistral | + sponsor prizes | | 3rd | $500 | $2,000 Mistral | + sponsor prizes |
Global Prize (SF winner competes Mar 9 via YouTube):
* $10,000 cash  15,000 Mistral credits + hiring opportunity at Mistral AI + final interview for Supercell AI Innovation Lab ( 15,000Mistralcredits+hiringopportunityatMistralAI+finalinterviewforSupercellAIInnovationLab(100k value)
Special Awards (stackable with placement): | Award | Prize | Sponsor | |-------|-------|---------| | Best Vibe Usage | Custom Apple AirPods | Mistral | | Best Use of ElevenLabs | $2,000-6,000 in credits | ElevenLabs | | Best Video Game Project | Custom GameBoy Color | Supercell | | Best Use of Agent Skills | Reachy Mini robot | Hugging Face |
Prize stacking is possible: Win 1st place + a special award + compete for global.
SF-specific sponsors to note: Jump Trading (trading firm — would respond to financial/strategic tools) and White Circle.
Judging Criteria
Category	Weight
Creativity / Uniqueness	25%
Future Potential / Impact	25%
Technical Implementation	25%
Pitch Quality	25%
Mistral's Tech Stack Available
Models:
* Mistral Large 3 (675B MoE, 41B active) — flagship, multimodal, 256K context
* Mistral Medium 3.1 — frontier multimodal, good balance
* Mistral Small 3.2 — fast, efficient for chaining
* Magistral Medium 1.2 — reasoning model with chain-of-thought (key differentiator)
* Devstral 2 (123B) — SOTA coding model, 72.2% SWE-bench
* Mistral Small Creative — creative writing and character interaction
* OCR 3 — document AI / extraction
* Voxtral Mini Transcribe — audio transcription
Agents API (the core platform to showcase):
* Persistent agents with instructions, tools, and memory
* Stateful conversations maintaining context
* Multi-agent handoffs — agents delegate to other agents
* Built-in connector tools: web_search, code_interpreter, image_generation, document_library
* Custom function calling with JSON schemas
* MCP (Model Context Protocol) — connect to external services
* Handoff execution modes: server-side or client-side control
Mistral Vibe CLI (dedicated prize category):
* Open-source CLI coding agent powered by Devstral
* File manipulation, shell commands, code search, git-aware context
* Subagent delegation for parallel work
* Custom agent profiles via TOML configs
* MCP server support
* Apache 2.0 licensed
Other capabilities: Fine-tuning API, embeddings, batch inference, moderation, citations, structured outputs, predicted outputs.
What Mistral Already Showcases (Cookbooks)
These exist as published examples — building the same pattern without significant differentiation would be uninspired:
* Multi-Agent Data Analysis & Simulation (Router → Analysis → Simulation → Report)
* HubSpot Dynamic Multi-Agent System with Magistral Reasoning
* Industrial Equipment Knowledge Agent
* Call Transcript → PRD → Linear Tickets
* Multi-Agent Recruitment Workflow
* Earnings Call Analysis System (MAECAS)
* Financial Analyst with MCP
* GitHub Automation Agent
* NutriSense Food Diet Companion
* Travel Assistant
* Bank Support Agent
* Arxiv Research Paper Agent
Implication: Any project that directly replicates these cookbook patterns will look derivative. The winning project must operate in a domain or interaction model that doesn't pattern-match to existing Mistral demos.

3. Goals for Pol & Why Winning Matters
The Direct Stakes
Financial: 1st place SF = $1,500 cash + $3,000 credits. With special awards stacked, potentially $3,500+ cash. Global competition = $10,000 cash + hiring opportunity at Mistral. This is meaningful income above the W-2.
Career signal: A hackathon win at a Mistral-sponsored event — a major French AI company — creates a verifiable credential. This is the kind of event that shows up on LinkedIn, gets mentioned in interviews, and signals technical credibility in the AI/agents space. After the Portola technical interview stumble, a win here would be a concrete counter-narrative.
Foundry validation: The Foundry design brief identifies the need for "$1 of online revenue from something Pol built." While a hackathon prize isn't product revenue, it validates a product direction and creates a working prototype. If the hackathon project has real product potential (judging criteria: 25% future potential), it could become the Foundry's first product.
Network: 1,000+ hackers across 7 cities. The SF venue will have Mistral staff, sponsor representatives (Jump Trading, White Circle, ElevenLabs, Hugging Face), and mentors. This is a concentrated networking event in the exact ecosystem Pol wants to operate in. A winning project makes Pol the person everyone wants to talk to after the ceremony.
Portola positioning: Pol is reaching out to the Portola founders for a casual lunch/coffee while in SF for the hackathon. The message has been drafted:
"Hey Hunter, I'll be in SF this weekend for the Mistral AI hackathon. If you're around, would be great to grab lunch or coffee — no agenda, just wanted to connect while I'm in town. Pol"
This reframes Pol from "candidate waiting for verdict" to "builder competing at an AI hackathon in your city." Whether or not Portola responds, the positioning shift is valuable.
The Psychological Stakes

The real win is not the prize. It's proving to himself that he can execute under pressure in a public, competitive, high-stakes environment. That he can ship something in 48 hours that makes a room of strangers pay attention. That the technical foundation he's built over years can produce something remarkable when focused.
From the Foundry brief: "The first $100 of independent online revenue is a psychological objective, not a financial one. It proves the system works." A hackathon win serves a similar function — it proves the builder works.


Wargame / AI Strategic Simulation Engine Three agents (Bull, Bear, Arbiter) visibly debate a business decision in real-time. Streaming output shows the debate. Magistral reasoning model synthesizes a verdict. ElevenLabs delivers audio briefing. Different voices per agent.
Current assessment: Highest "spectacle" ceiling. Visible multi-agent handoffs. Uses Magistral reasoning prominently (Mistral wants this showcased). ElevenLabs voice integration is natural, not forced. Jump Trading sponsor would appreciate strategic reasoning tools. Demo writes itself. Build complexity is medium — 3 agents with handoffs, web search, structured output, ElevenLabs. Achievable solo in 48 hours. But Pol hasn't fully connected with this idea yet.
The Current Doubt
Pol's position as of the end of this conversation: none of the explored ideas have fully landed. The doubt is specifically:
1. Cookbook overlap. Many of the Mistral cookbooks already demonstrate multi-agent patterns in financial analysis, data analysis, recruitment, document processing, and task management. Building a variation of an existing cookbook pattern doesn't score high on Creativity/Uniqueness (25% of judging).
2. Narrow framing. The ideas so far have been too anchored on Pol's existing repos (DataDash) or the Foundry brief (DB-GPT). The winning idea might come from an unexpected intersection — boxing + AI, multilingual + AI, insurance + AI, game engines + AI, or something entirely new.
3. The right idea hasn't clicked yet. Pol's instinct is that the idea needs to arrive naturally, not be forced through analysis. He's taking tonight (Tue night) to let ideas percolate, using the structured method below.
Strategic Constraints for Idea Selection
* Must NOT replicate an existing Mistral cookbook pattern without significant differentiation
* Must be buildable solo in 48 hours (or with 1-2 teammates found on-site)
* Must create a visible, visceral demo moment — not just a useful tool
* Must naturally use 3-4+ Mistral capabilities (not forced integration)
* Should be eligible for prize stacking (1st place + at least one special award)
* Should have real product potential (25% of judging = future impact)



# EON — The Cognitive Civilization Engine

**Mistral Worldwide Hackathon — SF Venue — API / Agentic Track**

---

## North Star

Build a precomputed AI civilization replay where each civilization's move is decided by an internal council (agent handoffs), and the replay shows how those decisions create geopolitical outcomes — with beliefs, philosophy, and strategy emerging autonomously across eras.

**Pitch line:**
"EON combines multi-agent handoffs, constrained-memory governance, and replayable world simulation into one end-to-end system for emergent AI geopolitics."

---

## Mistral Moonshot Alignment

This project directly addresses three moonshots from Mistral's challenge list:

| Moonshot | How EON Delivers |
|---|---|
| **"Design a simulation where LLM agents form civilizations"** | Two civilizations with country-inspired cultural priors compete on a shared grid. Each develops doctrine, evolves beliefs, adapts strategy across eras. |
| **"Design agents that can play cooperative/competitive games better than humans can"** | Internal council (General + Economist + Ruler) uses multi-agent handoffs to make nuanced tradeoff decisions no single-prompt agent could. |
| **"Create a simulation where agents develop religion, philosophy, or art"** | The Philosopher agent analyzes each era's outcomes and generates emergent cultural beliefs — not hardcoded, but derived from the civilization's lived experience. |
| **"Design a system where an LLM improves its own prompts"** | The Strategist coach takes match telemetry, diagnoses failures, and autonomously rewrites the tactical prompt. Validated Friday night: +62.5pp win rate improvement on unseen scenarios. This is the quantitative backbone of the entire project. |

---

## Validated Foundation

Friday night experiment (real Mistral API, 8 test matches per condition):

| Condition | Win Rate | Territory | Invalid Actions |
|---|---|---|---|
| Baseline | 12.5% | 16.0 | 6.75 |
| **Coached** | **75.0%** | **21.0** | **5.12** |
| Sham Control | 12.5% | 15.1 | 6.62 |

**+62.5pp win rate delta on unseen maps. The autonomous improvement loop is proven.**

---

## Locked Decisions (Do Not Re-open)

| Decision | Locked Value |
|---|---|
| **Name** | EON |
| **Demo mode** | Offline pre-simulated replay only. No live inference on stage. |
| **Scope** | 2 civilizations. 3 council agents each. 20 turns. 1 simulation run. Era updates every 5 turns (4 eras total). |
| **Stack** | Go sim engine + Python Mistral orchestration + React replay UI + W&B Weave traces + ElevenLabs narration |
| **Win condition** | Judges clearly see handoffs, strategy tradeoffs, and emergent behavior in under 2 minutes. |

---

## Explicit Cut List (Out of Scope)

- No 4-civilization world. Two civilizations only.
- No 5-generation evolution loop. One 20-turn run with 4 intra-run eras.
- No 3D graphics. Minimalist 2D grid (think Defcon / Dwarf Fortress).
- No real-time on-stage inference. Replay only.
- No unverifiable claims in the pitch.
- No Go rewrite if the proven Python engine covers it — Go only where it adds clear value (simulation speed, concurrency).

---

## System Architecture

```
┌────────────────────────────────────────────────────┐
│              THE WORLD (20x20 Grid)                │
│         Resources · Walls · Territory              │
│        2 Civilizations, opposite corners           │
└────────────────────────┬───────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
     ┌────────────────┐    ┌────────────────┐
     │   CIV A        │    │   CIV B        │
     │   (Rome-       │    │   (Japan-      │
     │    inspired)   │    │    inspired)   │
     │                │    │                │
     │  ⚔️ General    │    │  ⚔️ General    │
     │      │         │    │      │         │
     │      ▼ handoff │    │      ▼ handoff │
     │  📊 Economist  │    │  📊 Economist  │
     │      │         │    │      │         │
     │      ▼ handoff │    │      ▼ handoff │
     │  👑 Ruler      │    │  👑 Ruler      │
     │  (magistral)   │    │  (magistral)   │
     └───────┬────────┘    └───────┬────────┘
             │                     │
             ▼                     ▼
        JSON action           JSON action
             │                     │
             └──────────┬──────────┘
                        ▼
               ┌─────────────────┐
               │  ENGINE         │
               │  Resolves turn  │
               │  Updates state  │
               │  Logs to Weave  │
               └────────┬────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
   ┌─────────────────┐    ┌─────────────────┐
   │  Every 5 turns: │    │  Every 5 turns: │
   │  STRATEGIST     │    │  PHILOSOPHER    │
   │  (magistral)    │    │  (magistral)    │
   │  Rewrites       │    │  Rewrites       │
   │  strategy_prompt│    │  belief_prompt  │
   │  "How to win"   │    │  "Who are we"   │
   └─────────────────┘    └─────────────────┘
            │                       │
            └───────────┬───────────┘
                        ▼
               ┌─────────────────┐
               │  NARRATOR       │
               │  mistral-large  │
               │  + ElevenLabs   │
               │  2-3 clips tied │
               │  to key turns   │
               └─────────────────┘
```

---

## The Internal Council (Core Mechanic)

Each civilization's turn is decided by three agents in sequence using Mistral's Agent Handoff API:

```
World state arrives
        │
        ▼
⚔️ GENERAL (mistral-small)
   Sees: board state, resources, enemy positions
   Personality: aggressive, territorial, short-term
   Output: military assessment + recommended action
        │
        ▼ HANDOFF (General's assessment passed as context)
📊 ECONOMIST (mistral-small)
   Sees: General's recommendation + resource state
   Personality: conservative, resource-focused, risk-averse
   Output: economic assessment + counter-recommendation
        │
        ▼ HANDOFF (Both assessments passed as context)
👑 RULER (magistral — reasoning model)
   Sees: General's push + Economist's pushback + belief constraints
   Personality: synthesizer, bound by civilization's cultural values
   Output: final JSON action with reasoning trace visible to judges
        │
        ▼
{"action":"fortify", "coord":[4,1], "reasoning":"Secure border while preserving grain reserves"}
```

**Why this matters for the moonshots:** This is not one model playing a game. This is a **governance simulation** — competing internal priorities synthesized under resource constraints. The council debate IS the emergent behavior.

---

## The Two-Prompt System

Each civilization carries two prompts that evolve at era boundaries (every 5 turns):

**`belief_prompt` — The Soul** (rewritten by the Philosopher)
Country-inspired cultural priors. Constrains what the agent is WILLING to do.
```
Example seed (Rome-inspired):
"This civilization values order and infrastructure. It builds
before it conquers. It fortifies before it expands. Historical
lesson: roads outlast armies."
```

**`strategy_prompt` — The Brain** (rewritten by the Strategist)
Tactical instructions. HOW to achieve goals within belief constraints.
```
Example (after Era 2 coaching):
"Expand only into resource cells adjacent to fortified borders.
Attack only when local support exceeds defense by 2+. Prioritize
wheat cells — they sustain future expansion."
```

The Strategist optimizes for winning (proven +62.5pp loop). The Philosopher optimizes for cultural coherence — generating beliefs that emerge from experience, not from hardcoded rules.

---

## The Amnesia Constraint

Each council agent sees only the last 3 turns of history. They forget earlier events.

This serves the moonshot goals:
- **Emergent philosophy:** The Philosopher exists because the agents CAN'T learn from long history on their own. Cultural memory must be externalized into the belief prompt. This mirrors how real civilizations encode lessons into religion, law, and tradition.
- **Drama:** Limited memory creates paranoia, repeated mistakes, and narrative arcs that make the demo watchable.
- **Technical honesty:** Context windows are finite. This constraint is real, not artificial.

---

## The Philosopher — Where Philosophy Emerges

After every 5-turn era, the Philosopher (magistral with reasoning traces) receives:
1. The civilization's current belief_prompt
2. The era's full replay log (all turns, all council debates, outcomes)
3. Territory and resource deltas

It outputs structured JSON:
```json
{
  "era_analysis": "In Era 2, this civilization attacked twice and lost
    both times due to insufficient support. The General overrode the
    Economist's caution. Resources dropped from 8 to 2.",
  "emergent_belief": "Aggression without economic backing is suicide.
    The council must reach consensus before committing to war.",
  "belief_diff": [
    "Added: 'No attack without 5+ resource reserves'",
    "Modified: General's voice now requires Economist approval for war"
  ],
  "new_belief_prompt": "..."
}
```

**This is the moonshot delivery.** The Philosopher is generating philosophy, doctrine, and cultural values FROM the civilization's lived experience. Not hardcoded. Not scripted. Emergent.

The reasoning traces (magistral thinking chunks) stream to the UI panel so judges can watch the AI form beliefs in real time.

---

## Civilization Seeds (Country-Inspired Priors)

### Civilization A — Rome-Inspired: Imperial Pragmatism
- **Starting values:** Order, infrastructure, military discipline
- **Starting constraint:** Must build (fortify) before expanding — roads before conquest
- **Designed tension:** The General wants to attack. The Economist wants to build. The Ruler must balance empire-building instinct against resource reality.

### Civilization B — Japan-Inspired: Strategic Consolidation
- **Starting values:** Discipline, honor, technological adaptation, insular defense
- **Starting constraint:** Fortifies heavily before any expansion — quality over quantity
- **Designed tension:** The Economist favors isolation (safe, efficient). The General sees opportunity cost. The Ruler must decide when isolation becomes a death sentence.

---

## Demo Artifacts (MVP)

The simulation produces one `history.json` containing everything the UI needs:

```json
{
  "metadata": {
    "civilizations": ["civ_a", "civ_b"],
    "grid_size": 20,
    "total_turns": 20,
    "eras": 4
  },
  "turns": [
    {
      "turn": 0,
      "board": [[...]],
      "resources": {"civ_a": {"wheat": 5, "iron": 3}, "civ_b": {"wheat": 4, "iron": 4}},
      "council_a": {
        "general": {"recommendation": "attack", "reasoning": "..."},
        "economist": {"recommendation": "fortify", "reasoning": "..."},
        "ruler": {"decision": "fortify", "coord": [4,1], "reasoning": "..."}
      },
      "council_b": {
        "general": {"recommendation": "...", "reasoning": "..."},
        "economist": {"recommendation": "...", "reasoning": "..."},
        "ruler": {"decision": "...", "coord": [...], "reasoning": "..."}
      },
      "weave_trace_id": "trace_xxx"
    }
  ],
  "era_updates": [
    {
      "era": 1,
      "after_turn": 5,
      "civ_a": {
        "strategist_diagnosis": "...",
        "philosopher_belief": "...",
        "belief_diff": ["..."]
      },
      "civ_b": {
        "strategist_diagnosis": "...",
        "philosopher_belief": "...",
        "belief_diff": ["..."]
      }
    }
  ],
  "narration_cues": [
    {"turn": 3, "text": "...", "audio_file": "era1_opening.mp3"},
    {"turn": 10, "text": "...", "audio_file": "era2_crisis.mp3"},
    {"turn": 19, "text": "...", "audio_file": "finale.mp3"}
  ]
}
```

---

## Demo Screen Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                            EON                                    │
├────────────────────┬──────────────────────┬──────────────────────┤
│                    │                      │                      │
│  INTERNAL COUNCIL  │    THE WORLD         │  ERA TIMELINE        │
│                    │    (2-Color Grid)    │                      │
│  ⚔️ General:       │                      │  Era 1 (Turns 1-5)  │
│  "Attack while     │   🏛️🏛️⬜⬜⬜⬜    │  "Age of Expansion"  │
│   they fortify"    │   🏛️⬜⬜⛰️⬜⬜    │                      │
│                    │   ⬜⬜🌾⬜⬜⬜    │  Era 2 (Turns 6-10)  │
│  📊 Economist:     │   ⬜⬜⬜🌾⬜⬜    │  "The Crisis"        │
│  "We have 2 wheat. │   ⬜⬜⛰️⬜⬜🏯    │                      │
│   War costs 3."    │   ⬜⬜⬜⬜🏯🏯    │  Beliefs evolved:    │
│                    │                      │  A: pragmatic        │
│  👑 Ruler:         │                      │  B: expansionist     │
│  "Build farms.     │  ▶ Turn 12/20       │                      │
│   Wait for Era 3." │  ⏸ ⏭ Speed: 2x     │  Philosopher:        │
│                    │                      │  "A has learned that │
│  [THINKING TRACE]  │  🎙️ Narration ON    │   infrastructure     │
│  "The Economist    │                      │   outlasts armies."  │
│   is right — we    │                      │                      │
│   cannot sustain   │                      │  PROMPT EVOLUTION:   │
│   a campaign..."   │                      │  Era1→Era2 diff:     │
│                    │                      │  + "No attack w/o    │
│                    │                      │    5+ reserves"      │
│                    │                      │  + "Fortify before   │
│                    │                      │    expanding"        │
│                    │                      │  Δ win rate: +62.5pp │
└────────────────────┴──────────────────────┴──────────────────────┘
```

**Controls:** Play / Pause / Step / Speed (1x, 2x, 4x). Judges can scrub through the timeline or let it play with narration.

---

## Observability (W&B Weave)

Every turn logs to Weave:
- Council handoff chain: General input/output → Economist input/output → Ruler input/output
- Final action + engine resolution (success/failure/reason)
- Resource state before and after
- Territory delta

Every era boundary logs:
- Strategist diagnosis + prompt diff + new strategy
- Philosopher analysis + belief diff + new beliefs + reasoning traces
- Win rate / territory metrics (before vs after coaching)

**Bounty proof:** The Weave dashboard shows the full agent decision tree per turn, plus measurable improvement across eras.

---

## Tech Stack

| Component | Technology | Owner |
|---|---|---|
| Sim Engine | Go (turn resolution, grid state, resource tracking) | Pol |
| Mistral Orchestration | Python (council handoffs, strategist, philosopher) | Paul |
| Replay UI | React + Canvas (3-panel layout, timeline controls) | Pol |
| Narration | mistral-large (script) → ElevenLabs Flash v2.5 (audio) | 3rd |
| Observability | W&B Weave (auto-patched Mistral SDK) | Paul |
| Replay Artifact | Single `history.json` with all turn states + council transcripts | All |

**Note:** If the proven Python engine covers simulation needs without performance issues, skip the Go rewrite. Go only where it adds clear value (grid simulation speed for larger maps or concurrent agent calls).

---

## Bounties Targeted

| Bounty | Alignment |
|---|---|
| **Mistral Main Track** | Agent Handoffs (council) + Magistral reasoning (ruler + philosopher) + Structured JSON outputs. Direct API showcase. |
| **W&B Agentic Coding (Mac Mini)** | Weave traces every council handoff + strategist/philosopher evolution loop. Measurable improvement across eras. |
| **Supercell Best Game AI (GameBoy)** | Autonomous game engine with LLM-driven civilizations making strategic decisions under resource constraints. |
| **ElevenLabs Voice** | Narrator voice clips generated from game events, synced to replay timeline. |

---

## Build Plan (Saturday → Sunday)

### Saturday Morning — P0: Engine + Basic Agents
- [ ] Grid engine: 2 civs on 20x20 grid, resources (wheat/iron), walls
- [ ] Single-agent per civ (mistral-small + structured output) — get turns running
- [ ] Replay capture: `history.json` with board states per turn
- [ ] Verify: 20 turns complete, JSON artifact produced

### Saturday Afternoon — P0: The Council
- [ ] Implement 3-agent handoff chain (General → Economist → Ruler)
- [ ] Ruler uses magistral with reasoning traces
- [ ] Council transcripts captured in `history.json`
- [ ] W&B Weave tracing on every handoff + every turn
- [ ] Verify: council debate visible in JSON, Weave dashboard shows traces

### Saturday Evening — P1: Era Evolution
- [ ] Strategist agent: rewrites strategy_prompt at turn 5, 10, 15 (proven coaching loop)
- [ ] Philosopher agent: rewrites belief_prompt at era boundaries, reasoning traces captured
- [ ] Verify: belief prompts drift across eras, strategy improves measurably

### Sunday Morning — P1: Demo Polish
- [ ] React UI: 3-panel layout with timeline controls (play/pause/step/speed)
- [ ] ElevenLabs: 2-3 narration clips at key turns (era transitions, critical moments)
- [ ] Audio sync in the replay player
- [ ] Pre-render the final `history.json` + audio files

### Sunday Afternoon — Ship
- [ ] Test replay 5 times end-to-end with zero API calls during playback
- [ ] Write 2-minute pitch script
- [ ] Record video walkthrough as backup
- [ ] Submit to Iterate platform

---

## Saturday Noon Checkpoint (Decision Gate)

| State | Action |
|---|---|
| 2 civs running, council handoffs working, 20 turns complete | **Full speed. Add Philosopher + Narrator.** |
| Council handoffs unstable, single-agent fallback working | **Ship with single-agent per civ. Focus Philosopher + Narrator for the moonshot story.** |
| Engine broken, no turns completing | **Fall back to proven Friday architecture (2-team validated loop) with civilization framing.** |

---

## Definition of Done (Sunday Noon)

- [ ] Replay runs end-to-end 5 times with zero API dependence during playback
- [ ] Council handoff chain visible in replay (General → Economist → Ruler per turn)
- [ ] Belief prompts evolved across eras with Philosopher reasoning traces
- [ ] Coached strategy measurably outperforms baseline on same seed
- [ ] Weave dashboard shows council traces and era updates
- [ ] At least 2 ElevenLabs narration clips synced to replay
- [ ] One clear emergent moment: a belief that formed from experience, not from the seed

---

## The Pitch (2 Minutes)

> "We built EON — a cognitive civilization engine.
>
> Two AI civilizations compete on a shared world. But they don't make decisions with a single prompt. Inside each civilization is a political council — a General, an Economist, and a Ruler — built on Mistral's Agent Handoff API. They argue. They disagree. The Ruler synthesizes their debate using Magistral's reasoning model, and we can watch the thinking traces live.
>
> Every five turns, a Philosopher AI analyzes what happened and generates new cultural beliefs — not scripted, but emergent from the civilization's actual experience. After losing two attacks with insufficient resources, Civilization A developed the doctrine: 'No war without economic backing.' That wasn't in the prompt. The AI wrote it.
>
> We combine multi-agent handoffs, constrained-memory governance, and replayable world simulation into one end-to-end system for emergent AI geopolitics.
>
> We validated the core improvement loop Friday night: +62.5% win rate gain from autonomous coaching on unseen scenarios. That's the engine. On top, you're watching AI civilizations develop philosophy from their own failures."

---

## What This Is Not

- This is not a prediction of what real countries would do.
- This is not a ranking of civilizations.
- This is a sandbox for exploring how cultural priors shape strategic decisions under resource constraints — and how those priors evolve from experience.
- Country-inspired seeds are starting points, not claims about nations.



Things to review before tomorrow:
Be realistic regarding the tools we have at our disposal (codex, vibe, Claude code) we can generate large amounts of code fast
We have free api access and higher rate limits so less constraints than believed. 


Each point should be reviewed first before being accepted. And they should prove that it will either
1. help the overall idea improve its score in one of the metrics listed above
2. Reduce technical debt and improve the chances of success for the project
if they do fit in one of these then the point should be rejected with a reason “why”

