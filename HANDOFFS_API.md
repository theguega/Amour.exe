# Mistral Agent Handoffs — API Reference

Reference for the Mistral Agents Handoffs API (`client.beta`). Use this to wire up multi-agent workflows where agents delegate tasks to each other mid-conversation.

---

## Overview

Handoffs let an agent transfer control of a conversation to another agent. When a handoff is triggered, the target agent takes over, executes its tools, and returns a response. There is no limit to how many chained handoffs a workflow can have.

**Flow:**
1. Create all agents in the workflow.
2. Assign each agent its allowed `handoffs` (list of agent IDs it can delegate to).
3. Start a conversation with the entry-point agent.
4. The agent autonomously decides when to hand off based on the task.

---

## 1. Create Agents

Each agent needs a `model`, `name`, `description`, and optionally `tools`, `instructions`, and `completion_args`.

### Python

```python
from mistralai import Mistral, CompletionArgs, ResponseFormat, JSONSchema
from pydantic import BaseModel

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

class CalcResult(BaseModel):
    reasoning: str
    result: str

# Basic agent (no tools)
finance_agent = client.beta.agents.create(
    model="mistral-large-latest",
    description="Agent used to answer financial related requests",
    name="finance-agent",
)

# Agent with web_search tool
web_search_agent = client.beta.agents.create(
    model="mistral-large-latest",
    description="Agent that can search online for any information if needed",
    name="websearch-agent",
    tools=[{"type": "web_search"}],
)

# Agent with a custom function tool
ecb_interest_rate_agent = client.beta.agents.create(
    model="mistral-large-latest",
    description="Can find the current interest rate of the European central bank",
    name="ecb-interest-rate-agent",
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_european_central_bank_interest_rate",
                "description": "Retrieve the real interest rate of European central bank.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                        },
                    },
                    "required": ["date"],
                },
            },
        },
    ],
)

# Agent with code_interpreter tool
graph_agent = client.beta.agents.create(
    model="mistral-large-latest",
    name="graph-drawing-agent",
    description="Agent used to create graphs using the code interpreter tool.",
    instructions="Use the code interpreter tool when you have to draw a graph.",
    tools=[{"type": "code_interpreter"}],
)

# Agent with structured JSON output
calculator_agent = client.beta.agents.create(
    model="mistral-large-latest",
    name="calculator-agent",
    description="Agent used to make detailed calculations",
    instructions="When doing calculations explain step by step what you are doing.",
    completion_args=CompletionArgs(
        response_format=ResponseFormat(
            type="json_schema",
            json_schema=JSONSchema(
                name="calc_result",
                schema=CalcResult.model_json_schema(),
            ),
        )
    ),
)
```

### TypeScript

```typescript
import { z } from 'zod';
import { responseFormatFromZodObject } from '@mistralai/mistralai/extra/structChat.js';

const CalcResult = z.object({
  reasoning: z.string(),
  result: z.string(),
});

let financeAgent = await client.beta.agents.create({
  model: 'mistral-large-latest',
  description: 'Agent used to answer financial related requests',
  name: 'finance-agent',
});

let webSearchAgent = await client.beta.agents.create({
  model: 'mistral-large-latest',
  description: 'Agent that can search online for any information if needed',
  name: 'websearch-agent',
  tools: [{ type: 'web_search' }],
});

let ecbInterestRateAgent = await client.beta.agents.create({
  model: 'mistral-large-latest',
  description: 'Can find the current interest rate of the European central bank',
  name: 'ecb-interest-rate-agent',
  tools: [
    {
      type: 'function',
      function: {
        name: 'getEuropeanCentralBankInterestRate',
        description: 'Retrieve the real interest rate of European central bank.',
        parameters: {
          type: 'object',
          properties: { date: { type: 'string' } },
          required: ['date'],
        },
      },
    },
  ],
});

const graphAgent = await client.beta.agents.create({
  model: 'mistral-large-latest',
  name: 'graph-drawing-agent',
  description: 'Agent used to create graphs using the code interpreter tool.',
  instructions: 'Use the code interpreter tool when you have to draw a graph.',
  tools: [{ type: 'code_interpreter' }],
});

const calculatorAgent = await client.beta.agents.create({
  model: 'mistral-large-latest',
  name: 'calculator-agent',
  description: 'Agent used to make detailed calculations',
  instructions: 'When doing calculations explain step by step what you are doing.',
  completionArgs: {
    responseFormat: responseFormatFromZodObject(CalcResult),
  },
});
```

### Agent Create Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model` | `string` | Yes | Model ID (e.g. `mistral-large-latest`) |
| `name` | `string` | Yes | Agent display name |
| `description` | `string` | Yes | What the agent does — used by other agents to decide when to hand off |
| `instructions` | `string` | No | System-level instructions for the agent |
| `tools` | `list[dict]` | No | Tools available: `web_search`, `code_interpreter`, or `function` |
| `completion_args` | `CompletionArgs` | No | Response format, temperature, etc. |
| `handoffs` | `list[str]` | No | Agent IDs this agent can delegate to (can also be set via `update`) |

### Available Tool Types

| Type | Description |
|---|---|
| `web_search` | Lets the agent search the web |
| `code_interpreter` | Lets the agent write and execute code |
| `function` | Custom function with a JSON schema for parameters |

---

## 2. Define Handoffs

After creating agents, assign which agents each one can hand off to. The `handoffs` field takes a list of agent IDs.

### Python

```python
finance_agent = client.beta.agents.update(
    agent_id=finance_agent.id,
    handoffs=[ecb_interest_rate_agent.id, web_search_agent.id],
)

ecb_interest_rate_agent = client.beta.agents.update(
    agent_id=ecb_interest_rate_agent.id,
    handoffs=[graph_agent.id, calculator_agent.id],
)

web_search_agent = client.beta.agents.update(
    agent_id=web_search_agent.id,
    handoffs=[graph_agent.id, calculator_agent.id],
)
```

### TypeScript

```typescript
financeAgent = await client.beta.agents.update({
  agentId: financeAgent.id,
  agentUpdateRequest: {
    handoffs: [ecbInterestRateAgent.id, webSearchAgent.id],
  },
});

ecbInterestRateAgent = await client.beta.agents.update({
  agentId: ecbInterestRateAgent.id,
  agentUpdateRequest: {
    handoffs: [graphAgent.id, calculatorAgent.id],
  },
});

webSearchAgent = await client.beta.agents.update({
  agentId: webSearchAgent.id,
  agentUpdateRequest: {
    handoffs: [graphAgent.id, calculatorAgent.id],
  },
});
```

### Handoff Topology (Example)

```
finance-agent
├── ecb-interest-rate-agent
│   ├── graph-drawing-agent
│   └── calculator-agent
└── websearch-agent
    ├── graph-drawing-agent
    └── calculator-agent
```

The agent decides which handoff to trigger based on its `description` fields — make these clear and specific.

---

## 3. Start a Conversation

Use `client.beta.conversations.start()` to kick off the workflow with the entry-point agent.

### Python

```python
response = client.beta.conversations.start(
    agent_id=finance_agent.id,
    inputs="Fetch the current US bank interest rate and calculate the compounded effect if investing for the next 10y",
)
```

---

## 4. Execution Modes

Two modes control how handoffs are processed:

| Mode | Behavior |
|---|---|
| **`server`** (default) | Handoffs execute internally on Mistral's cloud. The full chain runs automatically and you receive the final result. |
| **`client`** | When a handoff triggers, control returns to you immediately. You handle the handoff routing yourself. |

Use `server` for fire-and-forget workflows. Use `client` when you need to intercept handoffs, inject custom logic, or route to non-Mistral agents.

---

## 5. Event Types

The conversation produces a stream of events. Each event has a `type` field:

### `agent.handoff`

Fires when one agent delegates to another.

```
type='agent.handoff'
agent_id='ag_067f...'
agent_name='websearch-agent'
```

### `tool.execution`

Fires when an agent runs a tool.

```
type='tool.execution'
name='web_search'
```

### `message.output`

The agent's response. Content is a list of chunks (text, tool references, etc.).

```
type='message.output'
agent_id='ag_067f...'
model='mistral-medium-2505'
role='assistant'
content=[
    TextChunk(text='The current US bank interest rate is 4.50 percent', type='text'),
    ToolReferenceChunk(tool='web_search', title='...', type='tool_reference', url='...'),
    TextChunk(text='\n\nI will now handoff...', type='text'),
]
```

---

## 6. Full Event Flow Example

Input: *"Fetch the current US bank interest rate and calculate the compounded effect if investing for the next 10y"*

```
1. [agent.handoff]    → websearch-agent
2. [tool.execution]   → web_search
3. [message.output]   → "The current US bank interest rate is 4.50%..."
                         "I will now handoff to the calculator agent..."
4. [agent.handoff]    → calculator-agent
5. [message.output]   → {"result": "The future value after 10 years is $1,540.10.",
                          "reasoning": "A = P(1 + r/n)^(nt) = 1000(1.045)^10 ≈ 1540.10"}
```

The finance agent received the query, handed off to the web search agent for the interest rate, which then handed off to the calculator agent for the compound interest calculation. The final output respects the `json_schema` response format set on the calculator agent.

---

## 7. Key Design Notes

- **Description matters.** The agent's `description` is what other agents read to decide whether to hand off. Write it like a capability statement, not a name.
- **No handoff limit.** Chains can be as deep as needed. A → B → C → D is fine.
- **Tools + Handoffs coexist.** An agent can have both tools and handoffs. It decides whether to use a tool or hand off based on the task.
- **Structured output works.** Agents with `completion_args.response_format` will output JSON matching the schema, even at the end of a handoff chain.
- **Beta API.** All endpoints are under `client.beta` — expect breaking changes.
