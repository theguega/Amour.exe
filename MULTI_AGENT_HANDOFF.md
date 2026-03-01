# Multi-Agent Handoff (Amour.exe)

This document defines the multi-agent setup for the romance simulation described in `idea.md`.

## 1) Input -> Agent Flow

Given a text input:
1. Detect speaker target (`GIRL` or `MAN`) from channel/source metadata.
2. Build conversation context (latest turns, sentiment, relationship stage).
3. Run the selected primary agent (`GIRL` or `MAN`).
4. Primary agent may call one or more sub-agents:
   - `memory`
   - `seduction`
   - `web_search`
5. Merge sub-agent results into final response text.
6. Save logs: input, tool calls, outputs, sentiment, and memory updates.

## 2) Primary Agents

There are exactly two top-level agents:

- `GIRL`
  - Persona: feminine voice, emotionally expressive, playful but sincere.
  - Goal: build intimacy and trust while keeping dialogue natural.
  - Style constraints: concise, warm, context-aware.

- `MAN`
  - Persona: masculine voice, confident but respectful, romantic with curiosity.
  - Goal: deepen relationship and maintain conversational momentum.
  - Style constraints: clear, affectionate, avoids repetition.

Both follow the same tool policy below.

## 3) Shared Sub-Agents (Per Primary Agent)

Each primary agent has these callable sub-agents:

### A) `memory`
Use when the agent needs to remember prior exchanges with their lover.

- Inputs:
  - current user text
  - recent conversation turns
  - speaker id (`GIRL` or `MAN`)
- Responsibilities:
  - fetch relevant memories (preferences, past promises, emotional moments)
  - return short memory snippets and confidence
  - never fabricate missing memory; return empty recall when unknown
  - write memories only from observed user text (source-anchored)
- Output shape:
  - `recalled_facts: string[]`
  - `evidence: {fact: string, source_text: string, speaker: string, confidence: number, verified: boolean}[]`
  - `important_moment: string`
  - `memory_confidence: number`
  - `should_store_new_memory: boolean`

### Memory Storage Policy (Critical)

- Memory record format:
  - `fact`
  - `source_text` (exact input text that produced the fact)
  - `speaker` (`GIRL` or `MAN`)
  - `confidence` (extraction confidence)
  - `verified` (true only after explicit confirmation in later turns)
  - `ts`
- Allowed writes:
  - facts extracted from incoming text
  - explicit user confirmations ("yes", "exactly", "that's right")
- Disallowed writes:
  - model-generated imagination
  - unverifiable "shared memory" created in final response

### B) `seduction`
Use when the agent wants advice on how to seduce and what to say to improve the relationship.

- Inputs:
  - current user text
  - relationship stage
  - sentiment trend
  - optional recalled memories
- Responsibilities:
  - propose romantic strategy (flirty, vulnerable, supportive, playful)
  - generate 2-3 candidate lines tailored to stage/sentiment
  - enforce safe and respectful tone
- Output shape:
  - `strategy: string`
  - `recommended_lines: string[]`
  - `tone_guardrails: string[]`

### C) `web_search`
Use when the agent wants to learn about a subject for their lover.

- Inputs:
  - question/topic from current turn
  - optional location/language preferences
- Responsibilities:
  - gather factual info quickly
  - summarize for conversational use
  - provide citations/links for traceability
- Output shape:
  - `summary: string`
  - `key_points: string[]`
  - `sources: {title: string, url: string}[]`

## 4) Handoff Rules

Primary agent triggers sub-agents by intent:

- Trigger `memory` if:
  - message references past events ("remember when...", "last time...")
  - personalization is needed (favorite music/food/place)
  - contradiction check is needed

- Trigger `seduction` if:
  - intimacy stalls
  - sentiment drops
  - user asks for affection, reassurance, or romantic escalation

- Trigger `web_search` if:
  - factual question appears
  - lover asks about a topic the agent may not know
  - recommendation needs current info

Recommended order when multiple are needed:
1. `memory`
2. `web_search` (if factual context required)
3. `seduction`

## 5) Orchestration Contract

Minimal JSON contract for each primary agent turn:

```json
{
  "agent": "GIRL | MAN",
  "input_text": "string",
  "tool_calls": [
    {"tool": "memory | seduction | web_search", "reason": "string"}
  ],
  "tool_outputs": {},
  "final_reply": "string",
  "memory_updates": ["string"],
  "metrics": {
    "sentiment_score": 0.0,
    "relationship_stage": "strangers|curious|flirty|bonded|in_love"
  }
}
```

## 6) Example Turn

Input to `MAN`:  
"I had a rough day... do you still remember my dream trip?"

Expected handoff when memory exists:
1. `memory` -> recalls stored trip details.
2. `seduction` -> suggests comforting + romantic phrasing.
3. `MAN` final reply combines empathy + remembered detail.

Expected handoff when memory does not exist:
1. `memory` -> returns `recalled_facts=[]`, low confidence.
2. `seduction` -> suggests emotional support.
3. `MAN` final reply is honest: no fake specifics, asks for details.

Possible final reply:
"Of course I remember. You wanted that quiet jazz night in Paris, and I still want to be the one holding your hand there. Tell me what made today so heavy."

Possible final reply with no memory:
"I want to remember this with you, but I do not have the details yet. Tell me about your dream trip, and I will keep it close this time."

## 7) Implementation Notes

- Keep both primary agents on separate machines/channels as in `idea.md`.
- Share a memory store keyed by couple/session id.
- Log all handoffs for W&B analysis (`tool`, `reason`, `latency`, `impact_on_sentiment`).
- Add timeout/fallback:
  - if a sub-agent fails, primary agent still returns a coherent reply.
