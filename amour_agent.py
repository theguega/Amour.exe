#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import quote
from urllib.request import urlopen

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from mistralai import Mistral

MIN_CALL_INTERVAL = 0.35
MAX_RETRIES = 5
MAX_TOOL_ROUNDS = 1
RELATIONSHIP_STAGES = ["strangers", "curious", "flirty", "bonded", "in_love"]


def _init_weave(enabled: bool) -> bool:
    if not enabled:
        return False
    try:
        import weave

        weave.init("theo-ppt-mistralai-ppt-hackathon/Amour.exe")
        print("[weave] Tracing enabled — project: theo-ppt-mistralai-ppt-hackathon/Amour.exe")
        return True
    except Exception as e:
        print(f"[weave] Failed to init: {e} — continuing without tracing")
        return False


def _wrap_weave_op(func):
    try:
        import weave

        try:
            return weave.op(kind="tool")(func)
        except Exception:
            return weave.op()(func)
    except Exception:
        return func


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_rate_limited(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "rate limit" in text or "rate_limited" in text


def _backoff_delay(attempt: int, rate_limited: bool) -> float:
    base = 1.2 * (2.2 if rate_limited else 1.0)
    exp_delay = min(20.0, base * (2**attempt))
    jitter = random.uniform(0.0, min(1.0, exp_delay * 0.25))
    return exp_delay + jitter


def _as_dict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def _extract_thinking(response: Any) -> list[str]:
    def walk(node: Any, out: list[str]) -> None:
        node = _as_dict(node)
        if isinstance(node, dict):
            for key, val in node.items():
                if key in {"thinking", "reasoning", "reasoning_content"} and isinstance(val, str):
                    txt = val.strip()
                    if txt:
                        out.append(txt)
                walk(val, out)
        elif isinstance(node, list):
            for item in node:
                walk(item, out)

    chunks: list[str] = []
    try:
        walk(response, chunks)
    except Exception:
        return []
    return list(dict.fromkeys(chunks))


def _flatten_nodes(node: Any) -> list[Any]:
    out: list[Any] = []

    def walk(value: Any) -> None:
        value = _as_dict(value)
        if isinstance(value, dict):
            out.append(value)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(node)
    return out


def _extract_native_events(response: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for node in _flatten_nodes(response):
        event_type = node.get("type")
        if not isinstance(event_type, str):
            continue
        if event_type.startswith("agent.") or event_type.startswith("tool.") or event_type.startswith("message."):
            events.append(node)
    return events


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for chunk in content:
            data = _as_dict(chunk)
            if isinstance(data, dict):
                txt = data.get("text")
                if isinstance(txt, str) and txt.strip():
                    parts.append(txt.strip())
                    continue
                maybe = data.get("content")
                if isinstance(maybe, str) and maybe.strip():
                    parts.append(maybe.strip())
        return "\n".join(parts).strip()
    return ""


def _try_parse_json_block(text: str) -> dict[str, Any] | None:
    t = text.strip()
    if not t:
        return None
    try:
        parsed = json.loads(t)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(t[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _get_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {"prompt_tokens": 0, "completion_tokens": 0}
    prompt = getattr(usage, "prompt_tokens", None) or getattr(usage, "input_tokens", None) or 0
    completion = getattr(usage, "completion_tokens", None) or getattr(usage, "output_tokens", None) or 0
    return {"prompt_tokens": int(prompt), "completion_tokens": int(completion)}


class _KeyThrottle:
    global_lock = threading.Lock()
    locks: dict[str, threading.Lock] = {}
    last_call: dict[str, float] = {}


class ToolPlan(BaseModel):
    use_memory: bool = Field(description="Whether memory agent should be called.")
    memory_reason: str = Field(description="Reason for calling or skipping memory agent.")
    use_seduction: bool = Field(description="Whether seduction agent should be called.")
    seduction_reason: str = Field(description="Reason for calling or skipping seduction agent.")
    use_web_search: bool = Field(description="Whether web_search agent should be called.")
    web_search_reason: str = Field(description="Reason for calling or skipping web_search agent.")
    web_query: str = Field(description="Web query text if web_search is needed, else a short placeholder.")
    response_goal: str = Field(description="Primary conversational goal for this turn.")


class SeductionAdvice(BaseModel):
    strategy: str = Field(description="High-level strategy for this response.")
    recommended_lines: list[str] = Field(description="2-3 short line options.")
    tone_guardrails: list[str] = Field(description="Safety and tone reminders.")


class SourceItem(BaseModel):
    title: str = Field(description="Source title.")
    url: str = Field(description="Source URL.")


class WebSearchResult(BaseModel):
    summary: str = Field(description="Short factual summary for conversation use.")
    key_points: list[str] = Field(description="Important factual points.")
    sources: list[SourceItem] = Field(description="Citations used.")


class FinalReply(BaseModel):
    reply: str = Field(description="Final response text to say to the lover.")
    short_rationale: str = Field(description="Brief explanation of why this response works.")
    memory_update_candidate: str = Field(description="Potential memory fact to store from this turn.")


class MemoryHandoffOutput(BaseModel):
    tool: str = Field(description="Tool identifier, always memory.")
    recalled_facts: list[str] = Field(description="Relevant recalled facts from provided memory candidates.")
    evidence: list[dict[str, Any]] = Field(description="Evidence rows linked to recalled facts.")
    important_moment: str = Field(description="Most relevant recent moment.")
    memory_confidence: float = Field(description="Confidence score in the recall quality.")
    should_store_new_memory: bool = Field(description="Whether new memory should be persisted this turn.")


class SeductionHandoffOutput(BaseModel):
    tool: str = Field(description="Tool identifier, always seduction.")
    friend_take: str = Field(description="What a trusted friend would bluntly advise in this exact moment.")
    strategy: str = Field(description="High-level strategy for this response.")
    recommended_lines: list[str] = Field(description="2-3 short line options.")
    tone_guardrails: list[str] = Field(description="Safety and tone reminders.")


class WebHandoffOutput(BaseModel):
    tool: str = Field(description="Tool identifier, always web_search.")
    summary: str = Field(description="Short factual summary for conversation use.")
    key_points: list[str] = Field(description="Important factual points.")
    sources: list[SourceItem] = Field(description="Citations used.")


@dataclass
class MistralCaller:
    api_key: str | None = None
    client: Any = None
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_calls: int = 0
    use_native_handoff: bool = True
    _native_handoff_agents: dict[str, dict[str, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        from mistralai import Mistral

        key = self.api_key or os.environ.get("MISTRAL_API_KEY")
        if not key:
            raise RuntimeError("MISTRAL_API_KEY is not set.")
        self.api_key = key
        self.client = self.client or Mistral(api_key=key)

    def _throttle(self) -> None:
        key = self.api_key or "default"
        with _KeyThrottle.global_lock:
            if key not in _KeyThrottle.locks:
                _KeyThrottle.locks[key] = threading.Lock()
                _KeyThrottle.last_call[key] = 0.0
        lock = _KeyThrottle.locks[key]
        with lock:
            elapsed = time.time() - _KeyThrottle.last_call[key]
            if elapsed < MIN_CALL_INTERVAL:
                time.sleep(MIN_CALL_INTERVAL - elapsed)
            _KeyThrottle.last_call[key] = time.time()

    def call_parse(
        self,
        *,
        model: str,
        system: str,
        payload: dict[str, Any],
        schema: Any,
        temperature: float = 0.0,
    ) -> tuple[Any, list[str], dict[str, int]]:
        assert self.client is not None
        for attempt in range(MAX_RETRIES + 1):
            try:
                self._throttle()
                response = self.client.chat.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": json.dumps(payload)},
                    ],
                    response_format=schema,
                    temperature=temperature,
                )
                usage = _get_usage(response)
                self.total_prompt_tokens += usage["prompt_tokens"]
                self.total_completion_tokens += usage["completion_tokens"]
                self.total_calls += 1
                parsed = response.choices[0].message.parsed
                thinking = _extract_thinking(response)
                return parsed, thinking, usage
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(_backoff_delay(attempt, _is_rate_limited(exc)))
        raise RuntimeError("Unreachable retry loop exit.")

    def _completion_args_json_schema(self, schema_name: str, schema_model: type[BaseModel]) -> dict[str, Any]:
        return {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema_model.model_json_schema(),
                },
            }
        }

    def _ensure_native_agents(self, agent_type: Literal["girl", "man"]) -> dict[str, str]:
        if agent_type in self._native_handoff_agents:
            return self._native_handoff_agents[agent_type]

        assert self.client is not None
        if not hasattr(self.client, "beta"):
            raise RuntimeError("Mistral beta agents API is unavailable in this SDK/client.")

        persona = _persona(agent_type)
        owner = persona["name"]
        other = "MAN" if owner == "GIRL" else "GIRL"

        memory_agent = self.client.beta.agents.create(
            model="mistral-small-latest",
            name=f"amour-{agent_type}-memory",
            description="Selects relevant relationship memories from provided memory candidates.",
            instructions=(
                f"You are the memory specialist for {owner}. "
                "Input is JSON and includes memory_candidates and recent_messages. "
                "Never invent memory. Use only memory_candidates.evidence facts. "
                "Return tool='memory'."
            ),
            completion_args=self._completion_args_json_schema("memory_handoff_output", MemoryHandoffOutput),
        )

        seduction_agent = self.client.beta.agents.create(
            model="mistral-small-latest",
            name=f"amour-{agent_type}-seduction",
            description=(
                "Acts like a trusted close friend who gives realistic, respectful texting advice "
                "to improve attraction, trust, and emotional connection."
            ),
            instructions=(
                f"You are {owner}'s trusted friend and dating advisor. "
                "Give practical, human, realistic advice, not generic pickup lines. "
                "Prioritize consent, emotional attunement, pacing, and authenticity. "
                "Adapt to stage and mood: strangers=light/curious, bonded=increased vulnerability. "
                "If hostility or disrespect is present, recommend boundaries over seduction. "
                "Output MUST be JSON with tool='seduction' and include friend_take, strategy, "
                "recommended_lines, and tone_guardrails."
            ),
            completion_args=self._completion_args_json_schema("seduction_handoff_output", SeductionHandoffOutput),
        )

        web_agent = self.client.beta.agents.create(
            model="mistral-small-latest",
            name=f"amour-{agent_type}-web",
            description="Finds concise factual context for conversation when factual lookup is needed.",
            instructions=(
                "Use web_search when needed. Keep claims concise and cite sources. "
                "Return tool='web_search'."
            ),
            tools=[{"type": "web_search"}],
            completion_args=self._completion_args_json_schema("web_handoff_output", WebHandoffOutput),
        )

        primary_agent = self.client.beta.agents.create(
            model="magistral-small-latest",
            name=f"amour-{agent_type}-primary",
            description=(
                f"Primary romantic dialogue agent for {owner}. "
                f"Speaks to {other}, optionally handing off to memory/seduction/web specialists."
            ),
            instructions=(
                f"You are {owner}. Style: {persona['style']}. Goal: {persona['goal']}. "
                "Input is JSON with fields like input_text, relationship_stage, mood_profile, "
                "hostile_input, memory_candidates, and handoff_hints. "
                "Decide autonomously whether to handoff to memory, seduction, and/or web specialists. "
                "Treat the seduction specialist as your trusted friend giving private coaching before you reply. "
                "Respect handoff_hints: if consult_seduction/memory/web_search is true, you should handoff unless clearly unnecessary. "
                "If hostile_input is true, do not flirt; set calm boundaries. "
                "Never claim detailed memories unless they appear in memory specialist output. "
                "Return only the final JSON reply."
            ),
            completion_args=self._completion_args_json_schema("final_reply", FinalReply),
        )

        primary_agent = self.client.beta.agents.update(
            agent_id=primary_agent.id,
            handoffs=[memory_agent.id, seduction_agent.id, web_agent.id],
        )

        agents = {
            "primary": primary_agent.id,
            "memory": memory_agent.id,
            "seduction": seduction_agent.id,
            "web_search": web_agent.id,
        }
        self._native_handoff_agents[agent_type] = agents
        return agents

    def call_native_handoff(
        self,
        *,
        agent_type: Literal["girl", "man"],
        payload: dict[str, Any],
    ) -> tuple[Any, list[str], dict[str, int], list[dict[str, Any]]]:
        assert self.client is not None
        agents = self._ensure_native_agents(agent_type)
        for attempt in range(MAX_RETRIES + 1):
            try:
                self._throttle()
                response = self.client.beta.conversations.start(
                    agent_id=agents["primary"],
                    inputs=json.dumps(payload, ensure_ascii=True),
                    handoff_execution="server",
                    store=False,
                )
                usage = _get_usage(response)
                self.total_prompt_tokens += usage["prompt_tokens"]
                self.total_completion_tokens += usage["completion_tokens"]
                self.total_calls += 1
                thinking = _extract_thinking(response)
                events = _extract_native_events(response)
                return response, thinking, usage, events
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(_backoff_delay(attempt, _is_rate_limited(exc)))
        raise RuntimeError("Unreachable retry loop exit.")


class MemoryStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")

    def _session(self, data: dict[str, Any], session_id: str) -> dict[str, Any]:
        session = data.setdefault(session_id, {})
        if "agents" not in session:
            legacy_messages = session.get("messages", [])
            legacy_facts = session.get("facts", [])
            legacy_relationship = session.get("relationship")
            session["agents"] = {
                "girl": {"messages": [], "facts": [], "relationship": None},
                "man": {"messages": [], "facts": [], "relationship": None},
            }
            if legacy_messages:
                session["agents"]["girl"]["messages"] = legacy_messages
                session["agents"]["man"]["messages"] = legacy_messages
            if legacy_facts:
                session["agents"]["girl"]["facts"] = legacy_facts
                session["agents"]["man"]["facts"] = legacy_facts
            if legacy_relationship:
                session["agents"]["girl"]["relationship"] = legacy_relationship
                session["agents"]["man"]["relationship"] = legacy_relationship
            session.pop("messages", None)
            session.pop("facts", None)
            session.pop("relationship", None)
        return session

    def _agent_bucket(self, data: dict[str, Any], session_id: str, owner: str) -> dict[str, Any]:
        session = self._session(data, session_id)
        agents = session.setdefault("agents", {})
        bucket = agents.setdefault(owner, {"messages": [], "facts": [], "relationship": None})
        bucket.setdefault("messages", [])
        bucket.setdefault("facts", [])
        return bucket

    def reset_session(self, session_id: str) -> None:
        data = self._load()
        if session_id in data:
            data[session_id] = {
                "agents": {
                    "girl": {"messages": [], "facts": [], "relationship": None},
                    "man": {"messages": [], "facts": [], "relationship": None},
                }
            }
            self._save(data)

    def append_message(self, session_id: str, owner: str, speaker: str, text: str) -> None:
        data = self._load()
        bucket = self._agent_bucket(data, session_id, owner)
        bucket["messages"].append({"speaker": speaker, "text": text, "ts": _utc_now()})
        self._save(data)

    def get_relationship_state(self, session_id: str, owner: str) -> dict[str, Any]:
        data = self._load()
        bucket = self._agent_bucket(data, session_id, owner)
        state = bucket.get("relationship")
        if not isinstance(state, dict):
            state = {
                "compatibility_score": 0.5,
                "momentum": 0.0,
                "stage": "strangers",
                "trend": "stable",
                "turns": 0,
                "history": [],
            }
            bucket["relationship"] = state
            self._save(data)
        return state

    def update_relationship_state(
        self,
        session_id: str,
        owner: str,
        *,
        input_text: str,
        response_text: str,
        memory_used: bool,
        seduction_used: bool,
        web_used: bool,
    ) -> dict[str, Any]:
        data = self._load()
        bucket = self._agent_bucket(data, session_id, owner)
        state = bucket.get("relationship")
        if not isinstance(state, dict):
            state = self.get_relationship_state(session_id, owner)
            data = self._load()
            bucket = self._agent_bucket(data, session_id, owner)
            state = bucket.get("relationship", {})

        turns = int(state.get("turns", 0)) + 1
        input_sent = _sentiment_score(input_text)
        output_sent = _sentiment_score(response_text)

        warmth_bonus = 0.06 if seduction_used else 0.0
        curiosity_bonus = 0.05 if "?" in response_text else 0.0
        memory_bonus = 0.05 if memory_used else 0.0
        factual_bonus = 0.03 if web_used else 0.0
        turn_quality = _clamp(
            0.45 * ((input_sent + 1.0) / 2.0)
            + 0.55 * ((output_sent + 1.0) / 2.0)
            + warmth_bonus
            + curiosity_bonus
            + memory_bonus
            + factual_bonus,
            0.0,
            1.0,
        )

        prev_compat = float(state.get("compatibility_score", 0.5))
        prev_momentum = float(state.get("momentum", 0.0))
        compatibility = _clamp(0.82 * prev_compat + 0.18 * turn_quality, 0.0, 1.0)
        momentum = _clamp(0.65 * prev_momentum + 0.35 * ((turn_quality - 0.5) * 2.0), -1.0, 1.0)

        stage = _derive_stage(compatibility, turns)
        if momentum > 0.1:
            trend = "improving"
        elif momentum < -0.1:
            trend = "declining"
        else:
            trend = "stable"

        state.update(
            {
                "compatibility_score": round(compatibility, 3),
                "momentum": round(momentum, 3),
                "stage": stage,
                "trend": trend,
                "turns": turns,
            }
        )
        history = state.setdefault("history", [])
        history.append(
            {
                "ts": _utc_now(),
                "input_sentiment": round(input_sent, 3),
                "response_sentiment": round(output_sent, 3),
                "turn_quality": round(turn_quality, 3),
                "tool_usage": {
                    "memory": bool(memory_used),
                    "seduction": bool(seduction_used),
                    "web_search": bool(web_used),
                },
                "stage": stage,
                "trend": trend,
            }
        )
        # Keep history bounded.
        if len(history) > 200:
            state["history"] = history[-200:]
        bucket["relationship"] = state
        self._save(data)
        return state

    def _normalize_facts(self, facts: list[Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in facts:
            if isinstance(item, str):
                out.append(
                    {
                        "fact": item,
                        "source_text": "",
                        "speaker": "unknown",
                        "confidence": 0.4,
                        "verified": False,
                        "ts": _utc_now(),
                    }
                )
            elif isinstance(item, dict) and isinstance(item.get("fact"), str):
                out.append(
                    {
                        "fact": item.get("fact", "").strip(),
                        "source_text": item.get("source_text", ""),
                        "speaker": item.get("speaker", "unknown"),
                        "confidence": float(item.get("confidence", 0.4)),
                        "verified": bool(item.get("verified", False)),
                        "ts": item.get("ts", _utc_now()),
                    }
                )
        return [x for x in out if x["fact"]]

    def append_fact(
        self,
        session_id: str,
        owner: str,
        fact: str,
        *,
        source_text: str,
        speaker: str,
        confidence: float = 0.7,
        verified: bool = False,
    ) -> None:
        data = self._load()
        bucket = self._agent_bucket(data, session_id, owner)
        facts = self._normalize_facts(bucket.setdefault("facts", []))
        if fact and not any(f["fact"] == fact for f in facts):
            facts.append(
                {
                    "fact": fact.strip(),
                    "source_text": source_text.strip(),
                    "speaker": speaker,
                    "confidence": float(confidence),
                    "verified": bool(verified),
                    "ts": _utc_now(),
                }
            )
        bucket["facts"] = facts
        self._save(data)

    def recall(self, session_id: str, owner: str, query: str, limit: int = 3) -> dict[str, Any]:
        data = self._load()
        bucket = self._agent_bucket(data, session_id, owner)
        fact_rows = self._normalize_facts(bucket.get("facts", []))
        messages: list[dict[str, str]] = bucket.get("messages", [])
        words = set(re.findall(r"[a-zA-Z']+", query.lower()))
        scored: list[tuple[int, float, dict[str, Any]]] = []
        for row in fact_rows:
            fact = row["fact"]
            tokens = set(re.findall(r"[a-zA-Z']+", fact.lower()))
            overlap = len(words & tokens)
            scored.append((overlap, float(row.get("confidence", 0.4)), row))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top_rows = [row for overlap, _, row in scored if overlap > 0][:limit]
        top_facts = [r["fact"] for r in top_rows]
        if not top_facts:
            top_rows = fact_rows[-limit:]
            top_facts = [r["fact"] for r in top_rows]
        important_moment = messages[-1]["text"] if messages else ""
        confidence = 0.85 if top_facts else 0.0
        return {
            "recalled_facts": top_facts,
            "evidence": top_rows,
            "important_moment": important_moment,
            "memory_confidence": confidence,
        }

    def snapshot(self, session_id: str, owner: str, *, fact_limit: int = 40, message_limit: int = 12) -> dict[str, Any]:
        data = self._load()
        bucket = self._agent_bucket(data, session_id, owner)
        facts = self._normalize_facts(bucket.get("facts", []))
        messages = bucket.get("messages", [])
        return {
            "evidence": facts[-fact_limit:],
            "recent_messages": messages[-message_limit:],
        }


def _persona(agent_type: Literal["girl", "man"]) -> dict[str, str]:
    if agent_type == "girl":
        return {
            "name": "GIRL",
            "style": "emotionally expressive, playful, warm, sincere",
            "goal": "build intimacy and trust while keeping dialogue natural",
        }
    return {
        "name": "MAN",
        "style": "confident, respectful, affectionate, clear",
        "goal": "deepen relationship and keep emotional momentum",
    }


def _heuristic_plan(input_text: str) -> ToolPlan:
    t = input_text.lower()
    use_memory = any(k in t for k in ["remember", "last time", "you said", "favorite", "dream"])
    use_web = "?" in t or any(k in t for k in ["what is", "how to", "why", "when", "where", "learn", "explain"])
    use_seduction = any(
        k in t
        for k in [
            "miss you",
            "love",
            "rough day",
            "sad",
            "upset",
            "stressed",
            "lonely",
            "date",
            "romantic",
        ]
    )
    return ToolPlan(
        use_memory=use_memory,
        memory_reason="Heuristic trigger." if use_memory else "No memory cue detected.",
        use_seduction=use_seduction,
        seduction_reason="Heuristic trigger." if use_seduction else "No seduction cue detected.",
        use_web_search=use_web,
        web_search_reason="Heuristic trigger." if use_web else "No factual lookup cue detected.",
        web_query=input_text if use_web else "n/a",
        response_goal="Respond warmly and keep relationship progression steady.",
    )


def _extract_fact_candidate(text: str) -> str:
    patterns = [
        r"\bi (?:love|like|want|dream of|prefer)\b([^.!?]+)",
        r"\bmy favorite\b([^.!?]+)",
        r"\bi always\b([^.!?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(0).strip()
            return candidate[:240]
    return ""


def _memory_cue_strength(text: str) -> tuple[bool, bool]:
    t = text.lower()
    strong_patterns = [
        r"\bdo you remember\b",
        r"\bremember when\b",
        r"\byou said\b",
        r"\blast time\b",
        r"\bwe talked about\b",
    ]
    weak_patterns = [
        r"\bfavorite\b",
        r"\bdream trip\b",
        r"\bagain\b",
        r"\bstill\b",
    ]
    strong = any(re.search(p, t) for p in strong_patterns)
    weak = any(re.search(p, t) for p in weak_patterns)
    return strong, weak


def _should_call_memory(input_text: str, planner_wants_memory: bool) -> tuple[bool, str]:
    strong, weak = _memory_cue_strength(input_text)
    if not planner_wants_memory:
        return False, "Planner did not request memory."
    if strong:
        return True, "Strong explicit memory cue detected."
    if weak:
        return False, "Weak cue only; strict memory gating skipped recall."
    return False, "No explicit memory cue; strict memory gating skipped recall."


def _forget_roll(
    *,
    session_id: str,
    agent_type: str,
    input_text: str,
    base_forget_prob: float,
) -> bool:
    # Deterministic pseudo-random roll for reproducible runs.
    seed = f"{session_id}|{agent_type}|{input_text}".encode("utf-8")
    digest = hashlib.md5(seed).hexdigest()
    roll = int(digest[:8], 16) / 0xFFFFFFFF
    return roll < base_forget_prob


def _search_wikipedia(query: str, max_results: int = 2) -> WebSearchResult | None:
    q = quote(query)
    search_url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=opensearch&search={q}&limit={max_results}&namespace=0&format=json"
    )
    try:
        with urlopen(search_url, timeout=4) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        titles = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        if not titles:
            return None

        points: list[str] = []
        sources: list[SourceItem] = []
        for title in titles[:max_results]:
            page = quote(str(title).replace(" ", "_"))
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page}"
            with urlopen(summary_url, timeout=4) as summary_resp:
                summary_data = json.loads(summary_resp.read().decode("utf-8"))
            extract = str(summary_data.get("extract", "")).strip()
            page_url = (
                summary_data.get("content_urls", {})
                .get("desktop", {})
                .get("page", f"https://en.wikipedia.org/wiki/{page}")
            )
            if extract:
                points.append(extract[:220])
            sources.append(SourceItem(title=str(title), url=str(page_url)))
        summary = points[0] if points else f"No concise summary found for '{query}'."
        return WebSearchResult(summary=summary, key_points=points[:3], sources=sources)
    except Exception:
        return None


def _build_plan_system(agent_type: Literal["girl", "man"]) -> str:
    p = _persona(agent_type)
    return (
        f"You are the planner for {p['name']} in a romantic dialogue system. "
        "Decide whether to call tools: memory, seduction, web_search. "
        "Call tools only when useful. "
        "If web_search is true, set web_query to a concise search query. "
        "Keep decisions practical and relationship-focused."
    )


def _mood_instruction(agent_type: Literal["girl", "man"], mood_profile: str) -> str:
    if agent_type == "girl" and mood_profile == "rejection":
        return (
            "Current mood profile: rejection. "
            "Be polite but guarded, slower to trust, and avoid immediate affection."
        )
    if mood_profile == "open":
        return "Current mood profile: open. Be warm and engaged while staying respectful."
    return "Current mood profile: neutral."


def _build_seduction_system(agent_type: Literal["girl", "man"], mood_profile: str = "neutral") -> str:
    p = _persona(agent_type)
    return (
        f"You are a seduction coach for {p['name']}. "
        f"{_mood_instruction(agent_type, mood_profile)} "
        "Return advice that is respectful, consensual, emotionally intelligent, and concise. "
        "Never produce manipulative or coercive guidance."
    )


def _build_web_fallback_system() -> str:
    return (
        "You are a factual assistant filling in when live web lookup fails. "
        "Provide cautious, high-level facts, avoid fabricated precision, and include generic source placeholders."
    )


def _build_reply_system(agent_type: Literal["girl", "man"], mood_profile: str = "neutral") -> str:
    p = _persona(agent_type)
    return (
        f"You are {p['name']}. "
        f"Style: {p['style']}. Goal: {p['goal']}. "
        f"{_mood_instruction(agent_type, mood_profile)} "
        "Write one natural reply to the lover's latest message. "
        "Use tool outputs if provided. Do not mention tools. Keep reply under 90 words. "
        "Critical memory rule: only reference specific past details if they appear in memory.recalled_facts. "
        "If memory.recalled_facts is empty, do not claim to remember specifics; be honest and ask for details."
    )


def _should_call_seduction(
    *,
    input_text: str,
    planner_wants_seduction: bool,
    relationship_stage: str,
    mood_profile: str = "neutral",
) -> tuple[bool, str]:
    if not planner_wants_seduction:
        return False, "Planner did not request seduction."

    t = input_text.lower()
    explicit_flirt = any(
        k in t
        for k in [
            "kiss",
            "date",
            "my dear",
            "my love",
            "beautiful",
            "handsome",
            "flirt",
        ]
    )
    emotional_support = any(k in t for k in ["sad", "upset", "rough day", "stressed", "lonely", "nervous"])

    if relationship_stage in {"flirty", "bonded", "in_love"}:
        return True, f"Relationship stage '{relationship_stage}' allows romantic coaching."
    if mood_profile == "rejection":
        if explicit_flirt and relationship_stage in {"curious", "flirty", "bonded", "in_love"}:
            return True, "Rejection mode: explicit flirt accepted after initial rapport."
        if emotional_support:
            return True, "Rejection mode: emotional support allowed."
        return False, "Rejection mode: hold romantic coaching until trust builds."
    if relationship_stage == "curious":
        if explicit_flirt:
            return True, "Explicit flirt cue detected."
        return True, "Curious stage allows light romantic coaching."
    # strangers
    if explicit_flirt:
        return True, "Explicit flirt cue detected."
    if emotional_support:
        return True, "Support cue detected; use gentle seduction coach tone."
    return False, "Stranger stage without flirt/support cue; skip seduction."


def _build_reply_system_with_stage(
    agent_type: Literal["girl", "man"], relationship_stage: str, mood_profile: str = "neutral"
) -> str:
    base = _build_reply_system(agent_type, mood_profile=mood_profile)
    if relationship_stage in {"strangers", "curious"}:
        return (
            base
            + " Early-stage rule: keep tone warm, curious, and respectful. "
            + "Avoid strong commitment/projection claims (e.g., destiny, forever, 'you make me feel X already')."
        )
    return base


def _detect_hostility(text: str) -> tuple[bool, str]:
    t = text.lower()
    hostile_patterns = [
        r"\bshut up\b",
        r"\bfuck you\b",
        r"\bbitch\b",
        r"\bta gueule\b",
        r"\bferme ta gueule\b",
        r"\bconnard\b",
        r"\bconne\b",
        r"\bpute\b",
        r"\bsalope\b",
    ]
    for p in hostile_patterns:
        if re.search(p, t):
            return True, f"Hostile phrase detected: {p}"
    return False, "No explicit hostility detected."


def _build_boundary_reply_system(agent_type: Literal["girl", "man"]) -> str:
    p = _persona(agent_type)
    return (
        f"You are {p['name']}. "
        "The incoming message is disrespectful or hostile. "
        "Respond with calm boundaries: short, firm, non-abusive. "
        "Do not flirt. Do not escalate. Invite respectful conversation or stop."
    )


def _sanitize_reply_for_memory(reply: str, memory_output: dict[str, Any]) -> str:
    recalled = memory_output.get("recalled_facts", []) if isinstance(memory_output, dict) else []
    if recalled:
        return reply
    risky = [
        r"\bof course i remember\b",
        r"\bi remember when\b",
        r"\byou wanted\b",
        r"\bwe promised\b",
        r"\blast time we\b",
    ]
    if any(re.search(p, reply, re.IGNORECASE) for p in risky):
        return (
            "I want to remember this with you, but I do not have the details yet. "
            "Tell me about your dream trip, and I will keep it close this time."
        )
    return reply


def _extract_message_payload(event: dict[str, Any]) -> dict[str, Any] | None:
    parsed = event.get("parsed")
    parsed = _as_dict(parsed)
    if isinstance(parsed, dict):
        return parsed
    text = _content_to_text(event.get("content"))
    return _try_parse_json_block(text)


def run_turn_native(
    *,
    caller: MistralCaller,
    memory_store: MemoryStore,
    agent_type: Literal["girl", "man"],
    input_text: str,
    session_id: str,
    mood_profile: str = "neutral",
) -> dict[str, Any]:
    stage_state = memory_store.get_relationship_state(session_id=session_id, owner=agent_type)
    relationship_stage = str(stage_state.get("stage", "strangers"))
    hostile_input, hostility_reason = _detect_hostility(input_text)
    memory_candidates = memory_store.snapshot(session_id=session_id, owner=agent_type, fact_limit=40, message_limit=12)
    heuristic = _heuristic_plan(input_text)
    use_memory_hint, memory_hint_reason = _should_call_memory(input_text, heuristic.use_memory)
    use_seduction_hint, seduction_hint_reason = _should_call_seduction(
        input_text=input_text,
        planner_wants_seduction=heuristic.use_seduction,
        relationship_stage=relationship_stage,
        mood_profile=mood_profile,
    )
    use_web_hint = heuristic.use_web_search
    web_hint_reason = heuristic.web_search_reason

    payload = {
        "input_text": input_text,
        "session_id": session_id,
        "agent_type": agent_type,
        "mood_profile": mood_profile,
        "relationship_stage": relationship_stage,
        "hostile_input": hostile_input,
        "hostility_reason": hostility_reason,
        "memory_candidates": memory_candidates,
        "handoff_hints": {
            "consult_memory": use_memory_hint,
            "memory_reason": memory_hint_reason,
            "consult_seduction": use_seduction_hint,
            "seduction_reason": seduction_hint_reason,
            "consult_web_search": use_web_hint,
            "web_search_reason": web_hint_reason,
            "web_query": heuristic.web_query if use_web_hint else "n/a",
        },
    }

    response, thinking, usage, events = caller.call_native_handoff(agent_type=agent_type, payload=payload)
    _ = response  # Keep for future debugging, events already extracted.

    tool_outputs: dict[str, Any] = {}
    called_tools: set[str] = set()
    for event in events:
        if event.get("type") == "tool.execution":
            name = event.get("name")
            if isinstance(name, str):
                called_tools.add(name)
        if event.get("type") != "message.output":
            continue
        parsed = _extract_message_payload(event)
        if not isinstance(parsed, dict):
            continue
        tool = parsed.get("tool")
        if tool == "memory":
            mem = MemoryHandoffOutput.model_validate(parsed)
            tool_outputs["memory"] = {
                "recalled_facts": mem.recalled_facts,
                "evidence": mem.evidence,
                "important_moment": mem.important_moment,
                "memory_confidence": mem.memory_confidence,
                "should_store_new_memory": mem.should_store_new_memory,
            }
            called_tools.add("memory")
        elif tool == "seduction":
            sed = SeductionHandoffOutput.model_validate(parsed)
            tool_outputs["seduction"] = {
                "friend_take": sed.friend_take,
                "strategy": sed.strategy,
                "recommended_lines": sed.recommended_lines,
                "tone_guardrails": sed.tone_guardrails,
            }
            called_tools.add("seduction")
        elif tool == "web_search":
            web = WebHandoffOutput.model_validate(parsed)
            tool_outputs["web_search"] = {
                "summary": web.summary,
                "key_points": web.key_points,
                "sources": [s.model_dump() for s in web.sources],
            }
            called_tools.add("web_search")

    final_reply: FinalReply | None = None
    for event in reversed(events):
        if event.get("type") != "message.output":
            continue
        parsed = _extract_message_payload(event)
        if not isinstance(parsed, dict):
            continue
        if {"reply", "short_rationale", "memory_update_candidate"} <= set(parsed.keys()):
            final_reply = FinalReply.model_validate(parsed)
            break
        text = _content_to_text(event.get("content"))
        if text and final_reply is None:
            final_reply = FinalReply(
                reply=text[:500],
                short_rationale="Native handoff fallback parsed from assistant text.",
                memory_update_candidate="",
            )
            break

    if final_reply is None:
        raise RuntimeError("Native handoff returned no parsable final reply.")

    plan = ToolPlan(
        use_memory="memory" in called_tools,
        memory_reason="Native handoff selected memory specialist." if "memory" in called_tools else "Native handoff skipped memory specialist.",
        use_seduction="seduction" in called_tools,
        seduction_reason=(
            "Native handoff selected seduction specialist."
            if "seduction" in called_tools
            else "Native handoff skipped seduction specialist."
        ),
        use_web_search="web_search" in called_tools,
        web_search_reason=(
            "Native handoff selected web_search specialist."
            if "web_search" in called_tools
            else "Native handoff skipped web_search specialist."
        ),
        web_query=input_text if "web_search" in called_tools else "n/a",
        response_goal="Respond naturally while managing specialist handoffs.",
    )

    memory_called = "memory" in called_tools
    tool_calls = [
        {"tool": "memory", "called": memory_called, "reason": plan.memory_reason},
        {"tool": "web_search", "called": "web_search" in called_tools, "reason": plan.web_search_reason},
        {"tool": "seduction", "called": "seduction" in called_tools, "reason": plan.seduction_reason},
    ]

    trace: dict[str, Any] = {
        "planning": ["Native Mistral handoff orchestration used."],
        "tool_reasons": [plan.memory_reason, plan.web_search_reason, plan.seduction_reason],
        "model_thinking": {
            "planner": thinking,
            "final_reply": [],
            "seduction": [],
            "web_fallback": [],
        },
        "fallbacks": [],
        "native_handoff_events": events,
    }

    other_speaker = "man" if agent_type == "girl" else "girl"
    memory_store.append_message(
        session_id=session_id,
        owner=agent_type,
        speaker=other_speaker,
        text=input_text,
    )
    fact_candidate = _extract_fact_candidate(input_text)
    if fact_candidate:
        memory_store.append_fact(
            session_id=session_id,
            owner=agent_type,
            fact=fact_candidate,
            source_text=input_text,
            speaker=other_speaker,
            confidence=0.75,
            verified=False,
        )

    safe_reply = _sanitize_reply_for_memory(final_reply.reply, tool_outputs.get("memory", {}))
    relationship = memory_store.update_relationship_state(
        session_id=session_id,
        owner=agent_type,
        input_text=input_text,
        response_text=safe_reply,
        memory_used=memory_called,
        seduction_used="seduction" in called_tools,
        web_used="web_search" in called_tools,
    )

    return {
        "ts": _utc_now(),
        "session_id": session_id,
        "agent_type": agent_type,
        "mood_profile": mood_profile,
        "input_text": input_text,
        "plan": plan.model_dump(),
        "tool_calls": tool_calls,
        "tool_outputs": tool_outputs,
        "reasoning_traces": trace,
        "response": safe_reply,
        "response_rationale": final_reply.short_rationale,
        "relationship": relationship,
        "usage": {
            "by_step": {"native_handoff": usage},
            "totals": {
                "total_calls": caller.total_calls,
                "total_prompt_tokens": caller.total_prompt_tokens,
                "total_completion_tokens": caller.total_completion_tokens,
            },
        },
    }


def run_turn(
    *,
    caller: MistralCaller,
    memory_store: MemoryStore,
    agent_type: Literal["girl", "man"],
    input_text: str,
    session_id: str,
    mood_profile: str = "neutral",
) -> dict[str, Any]:
    trace_native_fallback = ""
    if caller.use_native_handoff:
        try:
            return run_turn_native(
                caller=caller,
                memory_store=memory_store,
                agent_type=agent_type,
                input_text=input_text,
                session_id=session_id,
                mood_profile=mood_profile,
            )
        except Exception as native_exc:
            trace_native_fallback = f"native_handoff_error={type(native_exc).__name__}"

    trace: dict[str, Any] = {
        "planning": [],
        "tool_reasons": [],
        "model_thinking": {"planner": [], "final_reply": [], "seduction": [], "web_fallback": []},
        "fallbacks": [trace_native_fallback] if trace_native_fallback else [],
    }
    tool_outputs: dict[str, Any] = {}
    tool_calls: list[dict[str, Any]] = []
    usage_by_step: dict[str, dict[str, int]] = {}
    memory_called = False
    stage_state = memory_store.get_relationship_state(session_id=session_id, owner=agent_type)
    relationship_stage = str(stage_state.get("stage", "strangers"))
    hostile_input, hostility_reason = _detect_hostility(input_text)

    plan: ToolPlan
    try:
        planned, thinking, usage = caller.call_parse(
            model="magistral-small-latest",
            system=_build_plan_system(agent_type),
            payload={
                "input_text": input_text,
                "session_id": session_id,
                "relationship_stage": relationship_stage,
            },
            schema=ToolPlan,
            temperature=0.0,
        )
        plan = planned
        if hostile_input:
            plan.use_seduction = False
            plan.response_goal = "Set a calm boundary and request respectful language."
            plan.seduction_reason = f"Blocked by safety: {hostility_reason}"
        trace["model_thinking"]["planner"] = thinking
        trace["planning"].append("Planner model decision used.")
        usage_by_step["planner"] = usage
    except Exception as exc:
        plan = _heuristic_plan(input_text)
        if hostile_input:
            plan.use_seduction = False
            plan.response_goal = "Set a calm boundary and request respectful language."
            plan.seduction_reason = f"Blocked by safety: {hostility_reason}"
        trace["planning"].append("Heuristic plan used due to planner failure.")
        trace["fallbacks"].append(f"planner_error={type(exc).__name__}")

    for _ in range(MAX_TOOL_ROUNDS):
        use_memory_now, memory_gate_reason = _should_call_memory(input_text, plan.use_memory)
        if use_memory_now:
            mem = memory_store.recall(session_id=session_id, owner=agent_type, query=input_text, limit=3)
            if mem.get("recalled_facts"):
                strong, _ = _memory_cue_strength(input_text)
                forget_prob = 0.03 if strong else 0.1
                if _forget_roll(
                    session_id=session_id,
                    agent_type=agent_type,
                    input_text=input_text,
                    base_forget_prob=forget_prob,
                ):
                    mem["recalled_facts"] = []
                    mem["evidence"] = []
                    mem["memory_confidence"] = 0.0
                    mem["forgotten_this_turn"] = True
                    memory_gate_reason = f"{memory_gate_reason} Natural forget triggered."
            fact_candidate = _extract_fact_candidate(input_text)
            should_store = bool(fact_candidate)
            mem["should_store_new_memory"] = should_store
            tool_outputs["memory"] = mem
            memory_called = True
            tool_calls.append(
                {
                    "tool": "memory",
                    "called": True,
                    "reason": memory_gate_reason,
                    "memory_hits": len(mem.get("recalled_facts", [])),
                }
            )
            trace["tool_reasons"].append(memory_gate_reason)

        if plan.use_web_search:
            web_res = _search_wikipedia(plan.web_query.strip() or input_text)
            if web_res is not None:
                tool_outputs["web_search"] = web_res.model_dump()
                tool_calls.append(
                    {
                        "tool": "web_search",
                        "called": True,
                        "reason": plan.web_search_reason,
                        "status": "live_lookup",
                    }
                )
            else:
                try:
                    fallback_web, thinking, usage = caller.call_parse(
                        model="mistral-small-latest",
                        system=_build_web_fallback_system(),
                        payload={"query": plan.web_query.strip() or input_text},
                        schema=WebSearchResult,
                        temperature=0.1,
                    )
                    tool_outputs["web_search"] = fallback_web.model_dump()
                    trace["model_thinking"]["web_fallback"] = thinking
                    usage_by_step["web_fallback"] = usage
                    trace["fallbacks"].append("live_web_failed_used_model_fallback")
                    tool_calls.append(
                        {
                            "tool": "web_search",
                            "called": True,
                            "reason": plan.web_search_reason,
                            "status": "model_fallback",
                        }
                    )
                except Exception as exc:
                    trace["fallbacks"].append(f"web_search_error={type(exc).__name__}")
                    tool_outputs["web_search"] = {
                        "summary": "No web result available in this run.",
                        "key_points": [],
                        "sources": [],
                    }
                    tool_calls.append(
                        {
                            "tool": "web_search",
                            "called": True,
                            "reason": plan.web_search_reason,
                            "status": "failed",
                        }
                    )
            trace["tool_reasons"].append(plan.web_search_reason)

        use_seduction_now, seduction_gate_reason = _should_call_seduction(
            input_text=input_text,
            planner_wants_seduction=plan.use_seduction,
            relationship_stage=relationship_stage,
            mood_profile=mood_profile,
        )
        if use_seduction_now:
            try:
                seduction, thinking, usage = caller.call_parse(
                    model="mistral-small-latest",
                    system=_build_seduction_system(agent_type, mood_profile=mood_profile),
                    payload={
                        "input_text": input_text,
                        "memory": tool_outputs.get("memory", {}),
                        "web_context": tool_outputs.get("web_search", {}),
                        "relationship_stage": relationship_stage,
                    },
                    schema=SeductionAdvice,
                    temperature=0.2,
                )
                tool_outputs["seduction"] = seduction.model_dump()
                trace["model_thinking"]["seduction"] = thinking
                usage_by_step["seduction"] = usage
                tool_calls.append(
                    {
                        "tool": "seduction",
                        "called": True,
                        "reason": seduction_gate_reason,
                        "status": "ok",
                    }
                )
            except Exception as exc:
                trace["fallbacks"].append(f"seduction_error={type(exc).__name__}")
                tool_outputs["seduction"] = {
                    "strategy": "Validate feelings and invite deeper sharing.",
                    "recommended_lines": [
                        "I hear you. I am here with you.",
                        "Tell me what mattered most in your day, I want to understand.",
                    ],
                    "tone_guardrails": ["Respectful", "Warm", "No pressure"],
                }
                tool_calls.append(
                    {
                        "tool": "seduction",
                        "called": True,
                        "reason": seduction_gate_reason,
                        "status": "fallback",
                    }
                )
            trace["tool_reasons"].append(seduction_gate_reason)

    if not memory_called:
        _, memory_gate_reason = _should_call_memory(input_text, plan.use_memory)
        tool_calls.append({"tool": "memory", "called": False, "reason": memory_gate_reason})
    if not plan.use_web_search:
        tool_calls.append({"tool": "web_search", "called": False, "reason": plan.web_search_reason})
    if not any(c["tool"] == "seduction" and c.get("called") for c in tool_calls):
        _, seduction_gate_reason = _should_call_seduction(
            input_text=input_text,
            planner_wants_seduction=plan.use_seduction,
            relationship_stage=relationship_stage,
            mood_profile=mood_profile,
        )
        tool_calls.append({"tool": "seduction", "called": False, "reason": seduction_gate_reason})

    final: FinalReply
    try:
        final, thinking, usage = caller.call_parse(
            model="magistral-small-latest",
            system=(
                _build_boundary_reply_system(agent_type)
                if hostile_input
                else _build_reply_system_with_stage(agent_type, relationship_stage, mood_profile=mood_profile)
            ),
            payload={
                "input_text": input_text,
                "plan": plan.model_dump(),
                "tool_outputs": tool_outputs,
            },
            schema=FinalReply,
            temperature=0.3,
        )
        trace["model_thinking"]["final_reply"] = thinking
        usage_by_step["final_reply"] = usage
    except Exception as exc:
        trace["fallbacks"].append(f"final_reply_error={type(exc).__name__}")
        final = FinalReply(
            reply="I am here with you. Tell me what you need most right now, and I will stay with you.",
            short_rationale="Fallback response due to model error.",
            memory_update_candidate="",
        )

    # Update memory with the other agent message and useful extracted facts.
    other_speaker = "man" if agent_type == "girl" else "girl"
    memory_store.append_message(
        session_id=session_id,
        owner=agent_type,
        speaker=other_speaker,
        text=input_text,
    )
    fact_candidate = _extract_fact_candidate(input_text)
    if fact_candidate:
        memory_store.append_fact(
            session_id=session_id,
            owner=agent_type,
            fact=fact_candidate,
            source_text=input_text,
            speaker=other_speaker,
            confidence=0.75,
            verified=False,
        )

    safe_reply = _sanitize_reply_for_memory(final.reply, tool_outputs.get("memory", {}))
    relationship = memory_store.update_relationship_state(
        session_id=session_id,
        owner=agent_type,
        input_text=input_text,
        response_text=safe_reply,
        memory_used=memory_called,
        seduction_used=any(c["tool"] == "seduction" and c.get("called") for c in tool_calls),
        web_used=plan.use_web_search,
    )

    result = {
        "ts": _utc_now(),
        "session_id": session_id,
        "agent_type": agent_type,
        "mood_profile": mood_profile,
        "input_text": input_text,
        "plan": plan.model_dump(),
        "tool_calls": tool_calls,
        "tool_outputs": tool_outputs,
        "reasoning_traces": trace,
        "response": safe_reply,
        "response_rationale": final.short_rationale,
        "relationship": relationship,
        "usage": {
            "by_step": usage_by_step,
            "totals": {
                "total_calls": caller.total_calls,
                "total_prompt_tokens": caller.total_prompt_tokens,
                "total_completion_tokens": caller.total_completion_tokens,
            },
        },
    }
    return result


def _read_input_text(cli_text: str | None) -> str:
    if cli_text and cli_text.strip():
        return cli_text.strip()
    if sys.stdin.isatty():
        raise RuntimeError("No input text provided. Use --text or pipe input.")
    piped = sys.stdin.read().strip()
    if not piped:
        raise RuntimeError("No input text provided. Use --text or pipe input.")
    return piped


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _sentiment_score(text: str) -> float:
    positive_words = {
        "love",
        "like",
        "care",
        "happy",
        "excited",
        "beautiful",
        "wonderful",
        "great",
        "amazing",
        "trust",
        "kind",
        "hug",
        "together",
    }
    negative_words = {
        "sad",
        "upset",
        "angry",
        "hurt",
        "anxious",
        "nervous",
        "lonely",
        "bad",
        "rough",
        "stressed",
        "sorry",
        "afraid",
        "merde",
        "putain",
        "gueule",
        "ferme",
        "crier",
    }
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return 0.0
    pos = sum(1 for t in tokens if t in positive_words)
    neg = sum(1 for t in tokens if t in negative_words)
    raw = (pos - neg) / max(1, len(tokens) / 4)
    return _clamp(raw, -1.0, 1.0)


def _derive_stage(compatibility: float, turns: int) -> str:
    if compatibility < 0.25 or turns < 2:
        return "strangers"
    if compatibility < 0.45 or turns < 4:
        return "curious"
    if compatibility < 0.65 or turns < 6:
        return "flirty"
    if compatibility < 0.82 or turns < 10:
        return "bonded"
    return "in_love"


def _opposite(agent_type: Literal["girl", "man"]) -> Literal["girl", "man"]:
    return "man" if agent_type == "girl" else "girl"


def run_simulation(
    *,
    run_turn_fn,
    caller: MistralCaller,
    memory_store: MemoryStore,
    start_agent_type: Literal["girl", "man"],
    seed_text: str,
    turns: int,
    session_id: str,
    per_turn_log_file: Path,
) -> dict[str, Any]:
    transcript: list[dict[str, Any]] = []
    current_input = seed_text
    current_agent = start_agent_type

    for turn_idx in range(1, turns + 1):
        result = run_turn_fn(
            caller=caller,
            memory_store=memory_store,
            agent_type=current_agent,
            input_text=current_input,
            session_id=session_id,
        )
        _append_jsonl(per_turn_log_file, result)
        transcript.append(
            {
                "turn": turn_idx,
                "agent_type": current_agent,
                "heard": current_input,
                "response": result["response"],
                "plan": result["plan"],
                "tool_calls": result.get("tool_calls", []),
                "tool_outputs": result["tool_outputs"],
                "reasoning_traces": result["reasoning_traces"],
                "relationship": result.get("relationship", {}),
            }
        )
        current_input = result["response"]
        current_agent = _opposite(current_agent)

    return {
        "ts": _utc_now(),
        "mode": "simulation",
        "session_id": session_id,
        "seed_text": seed_text,
        "start_agent_type": start_agent_type,
        "turns": turns,
        "transcript": transcript,
        "usage_totals": {
            "total_calls": caller.total_calls,
            "total_prompt_tokens": caller.total_prompt_tokens,
            "total_completion_tokens": caller.total_completion_tokens,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Amour multi-agent responder (girl|man) using Mistral SDK."
    )
    parser.add_argument("--type", required=True, choices=["girl", "man"], dest="agent_type")
    parser.add_argument("--text", help="Input text from the other agent.")
    parser.add_argument("--session-id", default="default-couple")
    parser.add_argument("--log-file", default="logs/agent_runs.jsonl")
    parser.add_argument("--memory-file", default="logs/memory_store.json")
    parser.add_argument("--reset-memory", action="store_true", help="Reset memory for this session before running.")
    parser.add_argument("--simulate-turns", type=int, default=0, help="Run back-and-forth girl/man simulation.")
    parser.add_argument("--simulation-log-file", default="logs/simulations.jsonl")
    parser.add_argument("--disable-weave", action="store_true")
    parser.add_argument("--show-trace", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    weave_enabled = _init_weave(enabled=not args.disable_weave)
    run_turn_fn = _wrap_weave_op(run_turn) if weave_enabled else run_turn
    run_simulation_fn = _wrap_weave_op(run_simulation) if weave_enabled else run_simulation

    if args.simulate_turns > 0:
        text = (args.text or "Hi... I am curious about you. What makes you feel most alive?").strip()
    else:
        text = _read_input_text(args.text)

    caller = MistralCaller()
    memory_store = MemoryStore(Path(args.memory_file))
    if args.reset_memory:
        memory_store.reset_session(args.session_id)

    if args.simulate_turns > 0:
        sim = run_simulation_fn(
            run_turn_fn=run_turn_fn,
            caller=caller,
            memory_store=memory_store,
            start_agent_type=args.agent_type,
            seed_text=text,
            turns=args.simulate_turns,
            session_id=args.session_id,
            per_turn_log_file=Path(args.log_file),
        )
        _append_jsonl(Path(args.simulation_log_file), sim)

        if args.json:
            print(json.dumps(sim, ensure_ascii=True, indent=2))
            return

        print(
            f"[simulation] session={args.session_id} turns={args.simulate_turns} "
            f"start={args.agent_type} per_turn_log={args.log_file} summary_log={args.simulation_log_file}"
        )
        for item in sim["transcript"]:
            called = [c["tool"] for c in item.get("tool_calls", []) if c.get("called")]
            rel = item.get("relationship", {})
            trend = rel.get("trend", "n/a")
            stage = rel.get("stage", "n/a")
            score = rel.get("compatibility_score", "n/a")
            tools_txt = ",".join(called) if called else "none"
            print(
                f"{item['turn']:02d}. {item['agent_type']}: {item['response']} "
                f"[tools={tools_txt} stage={stage} trend={trend} score={score}]"
            )
        return

    result = run_turn_fn(
        caller=caller,
        memory_store=memory_store,
        agent_type=args.agent_type,
        input_text=text,
        session_id=args.session_id,
    )
    _append_jsonl(Path(args.log_file), result)

    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return

    print(result["response"])
    print(f"[log] {args.log_file}")
    if args.show_trace:
        print(json.dumps(result["reasoning_traces"], ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
