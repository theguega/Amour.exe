# SDK Reference — Mistral + W&B Weave

Extracted from the Friday validation codebase. Everything here was tested against live APIs on Feb 27, 2026.

---

## Dependencies

```
pip install mistralai>=1.5.0 pydantic>=2.7.0 weave>=0.51.0
```

---

## 1. Mistral Client Setup

```python
from mistralai import Mistral
import os

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
```

---

## 2. Structured Outputs (chat.parse)

This is the core pattern. Forces the model to return JSON matching a Pydantic schema.

### Schema Definition (CRITICAL GOTCHAS)

```python
from pydantic import BaseModel, Field
from enum import Enum

class ActionType(str, Enum):
    EXPAND = "expand"
    FORTIFY = "fortify"
    ATTACK = "attack"
    PASS = "pass"

class GameAction(BaseModel):
    action: ActionType
    coord: list[int] = Field(description="[x, y] coordinate on the grid")
    reasoning: str = Field(description="Brief explanation")

class ActionPlan(BaseModel):
    actions: list[GameAction] = Field(description="List of actions")
```

### What BREAKS the Mistral SDK schema converter

The SDK's `rec_strict_json_schema()` cannot handle certain Pydantic features. These will throw `ValueError: Unexpected type: <value>`:

| Broken | Fix |
|---|---|
| `tuple[int, int]` | Use `list[int]` instead |
| `Field(default=0.5, ge=0.0, le=1.0)` | Use `Field(description="0.0 to 1.0")` — no numeric constraints |
| `Field(min_length=1, max_length=12)` | Remove constraints, validate manually after parsing |
| `field_validator` decorators | Remove — the SDK sends schema to API, validators run client-side and conflict |
| Default values with integers `= (0, 0)` | Remove defaults from API-facing schemas, or use `Field(description=...)` only |

**Rule of thumb:** API-facing Pydantic models should have NO defaults, NO validators, NO numeric constraints. Use `Field(description=...)` for guidance. Validate after parsing.

### Making the Call

```python
response = client.chat.parse(
    model="mistral-small-latest",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload)},
    ],
    response_format=ActionPlan,  # Pass the class, not an instance
    temperature=0.0,
)

parsed = response.choices[0].message.parsed  # Typed ActionPlan object
raw_json = response.choices[0].message.content  # Raw JSON string
```

### Usage Tracking

```python
usage = response.usage
prompt_tokens = usage.prompt_tokens    # or usage.input_tokens
completion_tokens = usage.completion_tokens  # or usage.output_tokens
```

The attribute names vary across SDK versions. Safe pattern:
```python
prompt_tokens = getattr(usage, "prompt_tokens", None) or getattr(usage, "input_tokens", None) or 0
completion_tokens = getattr(usage, "completion_tokens", None) or getattr(usage, "output_tokens", None) or 0
```

---

## 3. Model IDs (Verified Working Feb 2026)

### Tactical / Fast Agents
| Model | ID | Cost (In/Out per M tok) | Notes |
|---|---|---|---|
| Mistral Small 3.2 | `mistral-small-latest` | $0.10 / $0.30 | Best general-purpose. 24B. Structured output works. |
| Ministral 8B | `ministral-8b-latest` | $0.15 / $0.15 | Cheaper, faster, 8B. Good for simple JSON actions. |

### Reasoning / Coach Agents
| Model | ID | Cost (In/Out per M tok) | Notes |
|---|---|---|---|
| Magistral Small | `magistral-small-latest` | $0.50 / $1.50 | Reasoning traces. Open-weight. Structured output works WITH reasoning. |
| Magistral Medium | `magistral-medium-latest` | $2.00 / $5.00 | Strongest reasoning. Higher cost. |

### Creative / Narrator
| Model | ID | Cost (In/Out per M tok) | Notes |
|---|---|---|---|
| Mistral Large 3 | `mistral-large-latest` | $0.50 / $1.50 | Best for creative writing, narration scripts. |

### DO NOT USE for game agents
| Model | ID | Why Not |
|---|---|---|
| Devstral | `devstral-latest` | Code/SWE agent. Optimized for file editing, not game strategy. Costs $0.40/$2.00. |

---

## 4. Magistral Reasoning Traces

Magistral models automatically produce thinking traces. The response content is a LIST of content chunks, not a plain string.

```python
response = client.chat.parse(
    model="magistral-small-latest",
    messages=[...],
    response_format=CoachOutput,
    temperature=0.2,
)

# The parsed result is in .parsed as usual
parsed = response.choices[0].message.parsed

# Thinking traces are in .content as a list of chunks
content = response.choices[0].message.content
# content is a list like:
# [
#   {"type": "thinking", "thinking": "Let me analyze the telemetry..."},
#   {"type": "text", "text": "{\"diagnosis\": \"...\", ...}"}
# ]
```

### Extracting Thinking Chunks (Tested Pattern)

```python
def extract_thinking_chunks(response) -> list[str]:
    chunks = []
    content = response.choices[0].message.content
    if not isinstance(content, list):
        return chunks

    for item in content:
        # Items may be objects with model_dump() or plain dicts
        if hasattr(item, "model_dump"):
            part = item.model_dump()
        elif isinstance(item, dict):
            part = item
        else:
            continue

        part_type = str(part.get("type", "")).lower()
        if part_type not in {"thinking", "reasoning"}:
            continue

        text = (
            part.get("thinking")
            or part.get("reasoning")
            or part.get("text")
            or part.get("content")
            or ""
        )
        if text:
            chunks.append(str(text).strip())

    return chunks
```

**Key insight:** Magistral supports structured output AND reasoning traces simultaneously. The thinking chunks and the parsed JSON come as separate content items. They do not conflict.

---

## 5. Rate Limiting

The Mistral API returns HTTP 429 with:
```json
{"object":"error","message":"Rate limit exceeded","type":"rate_limited","param":null,"code":"1300"}
```

### Tested Rate Limit Handling Pattern

```python
def _is_rate_limited(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "rate limit" in text or "rate_limited" in text

# Throttle: minimum spacing between calls
min_interval_s = 0.35  # ~3 calls/sec max

# Backoff: exponential with jitter, harsher for 429s
def backoff_delay(attempt: int, rate_limited: bool) -> float:
    base = 1.2 * (2.2 if rate_limited else 1.0)  # 429s get 2.2x slower base
    exp_delay = min(20.0, base * (2 ** attempt))
    jitter = random.uniform(0.0, min(1.0, exp_delay * 0.25))
    return exp_delay + jitter
```

At hackathon API key rate limits, expect occasional 429s with ~8+ matches running sequentially. The retry pattern above handled it cleanly in testing — all retries succeeded on attempt 2.

---

## 6. W&B Weave Integration

### Setup

```python
import weave

weave.init("your-project/your-run-name")
```

### Auto-Patching (Free Tracing)

After `weave.init()`, **every `client.chat.parse()` and `client.chat.complete()` call is automatically traced.** Zero code changes needed. Weave patches the Mistral SDK at import time.

Each trace captures:
- Model name
- Input messages (system + user)
- Output (parsed JSON or text)
- Token counts
- Latency
- Cost estimate

### Manual Op Tracing

To trace your own functions (game engine, coaching loop):

```python
@weave.op(kind="tool")
def run_match(agent, prompt, scenario, seed):
    ...
    return result
```

Or wrap dynamically:
```python
run_matches_fn = weave.op(kind="tool")(run_matches)
```

**Gotcha:** The `kind` parameter on `weave.op()` may not be supported in all Weave versions. Wrap in try/except:
```python
try:
    traced_fn = weave.op(kind="tool")(my_function)
except Exception:
    traced_fn = my_function
```

### What Shows Up in the Dashboard

After a run with Weave enabled, navigate to `wandb.ai` → your project → Weave tab. You'll see:
- Every Mistral API call with inputs/outputs
- Nested traces if you wrapped parent functions with `@weave.op`
- Token usage and cost per call
- Latency distribution

---

## 7. Basic Chat (Non-Structured)

For narration or creative text (no JSON schema needed):

```python
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {"role": "system", "content": "You are a dramatic historical narrator."},
        {"role": "user", "content": f"Narrate these events: {json.dumps(events)}"},
    ],
    temperature=0.7,
)
text = response.choices[0].message.content  # Plain string
```

---

## 8. Cost Estimation

```python
MODEL_PRICING_USD_PER_MTOK = {
    "mistral-small-latest": (0.10, 0.30),
    "ministral-8b-latest": (0.15, 0.15),
    "magistral-small-latest": (0.50, 1.50),
    "magistral-medium-latest": (2.00, 5.00),
    "mistral-large-latest": (0.50, 1.50),
}

def estimate_cost(model, prompt_tokens, completion_tokens):
    in_rate, out_rate = MODEL_PRICING_USD_PER_MTOK[model]
    return (prompt_tokens / 1_000_000) * in_rate + (completion_tokens / 1_000_000) * out_rate
```

### Friday Run Costs (Reference)

Full experiment (4 train maps, 4 test maps, 2 repeats, 2 coach iterations):
- Tactical calls (mistral-small): ~$0.027
- Coach calls (magistral-small): ~$0.002
- **Total: ~$0.03 per full experiment run**

A 20-turn EON simulation with 2 civs × 3 council agents = ~6 Mistral calls/turn × 20 turns = 120 calls. At ~1K tokens each with mistral-small, that's roughly $0.04-0.08 per simulation.

---

## 9. Environment Variables

```bash
export MISTRAL_API_KEY=your_key_here
export WANDB_API_KEY=your_key_here  # Only needed if using Weave
```

Verify Mistral key works:
```bash
python -c "from mistralai import Mistral; c = Mistral(api_key='YOUR_KEY'); print(c.chat.complete(model='mistral-small-latest', messages=[{'role':'user','content':'ping'}]).choices[0].message.content)"
```
