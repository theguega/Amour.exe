# Mistral Agent Handoff SDK Reference

Current official references (checked for this project on February 28, 2026):

1. Handoffs guide: https://docs.mistral.ai/agents/handoffs
2. Agents + conversations (`start`/`append`/`restart` + `handoff_execution`): https://docs.mistral.ai/agents/agents
3. API endpoint reference (`beta.agents`, `beta.conversations`):
   - https://docs.mistral.ai/api/endpoint/beta/agents
   - https://docs.mistral.ai/api/endpoint/beta/conversations
4. Python SDK repository (`mistralai[agents]`): https://github.com/mistralai/client-python

## How to use this in this codebase

### 1. Keep orchestration in `backend/engine.py`

Your turn loop and game resolution in `backend/engine.py` can stay the same. The main change is in `backend/agents.py`.

### 2. Replace direct dual `chat.parse` flow with agent handoff

Today, `backend/agents.py` calls:

- Stratege via `chat.parse`
- Roi via `chat.parse`

With handoffs, use one conversation start on Stratege and let it hand off to Roi.

### 3. One-time agent bootstrap

At startup (or a setup script):

1. `client.beta.agents.create(...)` for Stratege using instructions from `backend/prompts.py` (`STRATEGE_SYSTEM`)
2. `client.beta.agents.create(...)` for Roi using `ROI_SYSTEM`
3. `client.beta.agents.update(agent_id=<stratege_id>, handoffs=[<roi_id>])`

### 4. Per-turn call pattern

For each civ turn:

1. Build the same `board_view` payload you already use.
2. Call:
   - `client.beta.conversations.start(agent_id=<stratege_id>, inputs=<board_view>, handoff_execution="server", store=False)`
3. Parse returned outputs:
   - Stratege message output -> `StrategeAdvice`
   - Roi final message output -> `RoiDecision`
   - Optional `agent.handoff` events for trace/debug logs

### 5. Keep existing schemas

Reuse current models in `backend/schemas.py`:

- `StrategeAdvice`
- `RoiDecision`

Set each agent's `completion_args.response_format` (JSON schema) so outputs remain structured and compatible with your existing validation and history logging.

### 6. Dependency update

In `backend/requirements.txt`, prefer:

- `mistralai[agents]`

This ensures the agent SDK features are installed.

## Notes specific to this repo

- The grid simulation and action resolution in `backend/engine.py` do not need logic changes.
- The main migration surface is the `AgentCaller` methods in `backend/agents.py`.
- Existing retry/throttle/cost tracking can be kept and applied around `beta.conversations.start(...)`.
