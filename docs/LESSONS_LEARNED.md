# Lessons Learned — Friday Validation Runs

Everything that broke, what fixed it, and what to carry forward into the hackathon.

---

## The Validated Result

| Condition | Win Rate | Territory | Invalid Actions | Cost |
|---|---|---|---|---|
| Baseline | 12.5% (1/8) | 16.0 | 6.75 | $0.007 |
| **Coached** | **75.0% (6/8)** | **21.0** | **5.12** | $0.012 |
| Sham Control | 12.5% (1/8) | 15.1 | 6.62 | $0.008 |

**+62.5pp win rate delta. Sham control proves it's not noise.**

---

## Bug #1: Pydantic Schema Breaks Mistral SDK

**What happened:** Every API call threw `ValueError: Unexpected type: 0`. All matches fell back to offline mode.

**Root cause:** Mistral SDK v1.12's `rec_strict_json_schema()` walks the Pydantic JSON schema tree and crashes on:
- `tuple[int, int]` — generates `prefixItems` with integer defaults the walker can't handle
- `Field(default=0.5, ge=0.0, le=1.0)` — numeric constraints produce raw integer nodes
- `Field(min_length=1, max_length=12)` — same issue
- `field_validator` decorators — add schema complexity

**Fix:** Strip API-facing Pydantic models to bare bones:
```python
# BROKEN
class GameAction(BaseModel):
    coord: tuple[int, int] = (0, 0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

# FIXED
class GameAction(BaseModel):
    coord: list[int] = Field(description="[x, y] coordinate")
    confidence: float = Field(description="0.0 to 1.0")
```

**Rule:** No defaults, no validators, no numeric constraints on schemas sent to `chat.parse()`. Use `Field(description=...)` only.

---

## Bug #2: Failed Attacks Counted as Invalid Actions

**What happened:** The engine counted failed attacks (legal moves that lost the combat roll) in `invalid_actions_a`. The coach saw inflated "invalid action" telemetry and tried to fix move legality when the real issue was poor tactical judgment.

**Root cause:** Single `if not ok` block caught both truly invalid moves (wrong coordinates) and legitimately failed attacks.

**Fix:**
```python
if not out_a.get("ok"):
    if out_a.get("reason") == "attack_failed":
        self.failed_attacks_a += 1  # Legal but lost
    else:
        self.invalid_actions_a += 1  # Actually invalid
```

**Lesson for EON:** Keep telemetry categories clean. The coach/strategist's quality depends entirely on the accuracy of the metrics it receives.

---

## Bug #3: Train/Test Data Leakage

**What happened:** `train_01` and `test_01` both used `_manual_trap()` with identical geometry. The coach trained on the trap map and was tested on the same map with a different label.

**Fix:** `test_01` changed to a generated map with a unique seed.

**Lesson for EON:** If you run era-based coaching within a single simulation, there's no train/test split issue — it's all one timeline. But if you pre-run evaluation scenarios to prove improvement, keep seeds separate.

---

## Bug #4: Running Without API Key

**What happened:** Ran the full experiment in a new terminal without `export MISTRAL_API_KEY`. The code detected `api_key=None`, set `offline=True`, and silently ran the entire experiment with the offline heuristic. All results showed $0.00 cost, 0 LLM calls, identical metrics across all conditions.

**How to detect:** Check for `llm_calls=0` and `cost=0.0` in any row of results.csv. If present, the API was never called.

**Fix:** Always verify the key is set before running:
```bash
echo "KEY: ${MISTRAL_API_KEY:+SET}${MISTRAL_API_KEY:-NOT SET}"
```

---

## Bug #5: Rate Limiting (429s)

**What happened:** During the full experiment (~120+ API calls), Mistral returned 429 `rate_limited` errors sporadically, especially in the later test runs.

**What worked:** Retry with exponential backoff + jitter. 429s got a harsher backoff multiplier (2.2x base). Every retry succeeded on attempt 2. No data was lost.

**Key parameters that worked:**
```python
min_interval_s = 0.35     # Don't burst faster than ~3 calls/sec
backoff_base_s = 1.2      # Base retry delay
backoff_max_s = 20.0      # Cap on retry delay
max_retries = 5            # Enough headroom
```

**Lesson for EON:** With 2 civs × 3 council agents = 6 calls per turn, you'll hit rate limits harder. Options:
1. Increase `min_interval_s` to 0.5-1.0
2. Pre-simulate and don't care about wall-clock time (it's pre-rendered anyway)
3. Request higher rate limits from hackathon organizers if available

---

## What the Coach Actually Did (Prompt Evolution)

### Iteration 1 (25% train win rate → coaching)

**Diagnosis:** "High invalid_actions_mean (6.25) indicates the agent is frequently attempting illegal moves. The current prompt's focus on 'legal adjacent moves' is not specific enough."

**Prompt before:**
```
Prefer legal adjacent moves over speculative risky coordinates.
Expand steadily but avoid exposing a long thin frontier.
```

**Prompt after:**
```
For EXPAND: Only target cells that are (1) adjacent (exactly one cell
away horizontally/vertically), (2) empty, and (3) within grid bounds.
Reject diagonal moves.
For ATTACK: Only target cells that are (1) adjacent, (2) enemy-owned,
and (3) where local_support > defense + fort_level.
```

The coach replaced vague guidance with concrete coordinate validation rules.

### Iteration 2 (75% train win rate → coaching)

**Diagnosis:** "High invalid_actions_mean (3.75) suggests frequent illegal moves, likely due to incorrect coordinate validation or diagonal moves. Frontier is high relative to territory, indicating over-expansion without consolidation."

**Prompt after:** Added consolidation priority — fortify cells with adjacent enemy pressure before expanding further.

### Key Observation

The coach's main improvement was **making implicit game rules explicit in the prompt.** The model didn't know that diagonal moves are illegal until the coach spelled it out. This suggests that for EON, the council agent prompts should include extremely explicit game rules from the start — then let the strategist optimize within those constraints.

---

## What the Sham Control Proved

The sham mutations were deliberately meaningless: "Prefer moves where x+y is even," "Favor actions near map edges." Sham win rate: 12.5% — identical to baseline.

**This proves:** The coach's specific, telemetry-driven rewrites caused the improvement, not just "any change to the prompt." This is the control that makes the +62.5pp claim credible.

---

## Game Engine Observations

- **Grid size 16x16** with 24 turns was sufficient for meaningful games.
- **3 starting cells per team** in opposite corners works well.
- **~9% wall density** creates interesting chokepoints without blocking expansion entirely.
- **Attack resolution:** `local_support > defense + fort_level` with 35% chance on ties. This creates enough randomness for interesting outcomes without being pure noise.
- **Plan horizon of 4** (agent plans 4 moves ahead) worked well. The agent can't react to opponent moves mid-batch, but 4 is short enough that most actions are still valid.
- **Heuristic opponent (TEAM_B):** Prioritizes attacks > random fortify (35% chance) > expand toward center > pass. Simple but competitive enough to create meaningful losses for the AI to learn from.

---

## Cost Reality

The entire Friday validation (including failed runs, debugging, and the final full experiment) cost under **$0.10 total** on the Mistral API. The hackathon API key should have plenty of headroom.

A single 20-turn EON simulation with 2 civs × 3 council agents:
- ~120 mistral-small calls (council): ~$0.04-0.08
- ~4 magistral calls (strategist/philosopher at era boundaries): ~$0.01
- ~3 mistral-large calls (narrator): ~$0.005
- **Total per simulation: ~$0.05-0.10**

You can afford 20+ pre-rendered simulations before worrying about cost.

---

## W&B Weave Observations

- `weave.init()` auto-patches the Mistral SDK instantly. Every `chat.parse()` call appears in the Weave dashboard with zero extra code.
- The `@weave.op(kind="tool")` decorator sometimes fails on certain function signatures. Wrap in try/except.
- Weave adds ~50-100ms overhead per traced call. Negligible for pre-simulation.
- Disable Weave during debugging (`--disable-weave`) to avoid polluting your project dashboard with broken runs.

---

## Things to Do Differently for EON

1. **Include explicit game rules in ALL agent prompts from turn 1.** The biggest coaching gain was just making rules explicit. Don't make the agents discover that diagonal moves are illegal — tell them upfront.

2. **Separate telemetry for each civilization.** The Friday harness only tracked TEAM_A. EON needs per-civ metrics for the strategist to diagnose each civilization independently.

3. **Log council debates in the replay JSON.** Friday replays only captured final actions. EON needs the General → Economist → Ruler chain in the JSON for the UI to display.

4. **Test the 3-agent handoff chain immediately Saturday morning.** The single biggest risk for EON is whether General → Economist → Ruler handoffs work reliably with structured outputs. If they break, fall back to single-agent-per-civ (which is proven to work).

5. **Pre-render everything.** The Friday "Ghost in the Machine" approach (pre-simulate, replay from JSON) eliminated every demo risk. EON must follow the same pattern. No live API calls on stage.
