<p align="center">
  <img src="header-agent.jpg" width="100%" alt="nemotron-think — Visible Reasoning Agent Framework for NVIDIA Nemotron 3 Ultra">
</p>

<!-- Alternative banners in assets/:
     - header-abstract.jpg (beautiful thought bubbles + code)
     - header-agent.jpg (stylized transparent AI head)
-->

# nemotron-think

**Visible Reasoning Agent Framework for NVIDIA Nemotron 3 Ultra.**

Every step the model takes — its internal reasoning, why it chose a tool, the incremental tool call JSON, the observations — is **logged and surfaced** in real time.

This is not another wrapper. It is purpose-built to showcase (and productionize) the unique strengths of Nemotron 3 Ultra:

- `enable_thinking` + controllable `reasoning_budget`
- Extremely high-quality long-horizon reasoning
- Streamed `delta.tool_calls` (you watch the arguments being built live)
- Reliable self-correction when you feed tool results back

## Installation

```bash
git clone https://github.com/cobusgreyling/nemotron-think.git
cd nemotron-think

python -m venv .venv
source .venv/bin/activate
pip install -e .

# Add your key
cp .env.example .env
# edit .env → put your nvapi-... key
```

Or:

```bash
pip install git+https://github.com/cobusgreyling/nemotron-think.git
```

## Quickstart (CLI — the recommended way)

```bash
# See what the agent can do
nemotron-think tools

# Run a visible reasoning agent (the whole point)
nemotron-think run "A bat and a ball cost $1.10. The bat costs $1 more than the ball. How much does the ball cost? Show your full reasoning and explain the common mistake."

# Use more thinking power + save the complete trace
nemotron-think run "Research the current best open-source text-to-video models (last 6 months). List the top 3 with licenses, GitHub stars if available, and key differentiators." --budget 8192 --save-trace traces/video_research.json

# Replay any trace later (perfect for demos, no API calls needed)
nemotron-think replay traces/video_research.json
```

Live output shows:
- Green = model reasoning / thinking
- Orange = tool call progress (incremental JSON)
- Clean final answer

## Python API (for building your own agents)

```python
from nemotron_think import VisibleReasoningAgent

agent = VisibleReasoningAgent(
    max_steps=8,
    default_reasoning_budget=4096,
)

run = agent.run(
    "Write a correct Python function to find the kth largest element, then use the python_exec tool to test it on several inputs including edge cases.",
    reasoning_budget=8192,
)

print(run.final_answer)
run.save("my_code_agent_run.json")

# Inspect every thought
for step in run.steps:
    print(step.reasoning[:300])
```

## What makes this useful

- **Debugging & trust**: You can finally see *why* the model called a tool or reached a conclusion.
- **Eval & datasets**: Every `AgentRun` is a rich JSON with full reasoning traces — gold for creating reasoning datasets or running evals.
- **Demos & talks**: `nemotron-think replay` + terminal recordings = extremely compelling demos.
- **Production agents**: The same loop you use for impressive demos can be the core of real tools (research agents, coding agents, planning agents).
- **Controllability**: Dial `reasoning_budget` and `low_effort` per run or per step.

## Pluggable Tools (easy to extend)

Current defaults (all visible to the model with proper schemas):

- `get_math_answer` — safe calculator
- `get_current_time`
- `python_exec` — execute and observe Python code (with basic guards)
- `web_search` — current web information via DuckDuckGo (no extra keys)

Adding your own tool is 5 lines:

```python
from nemotron_think import VisibleReasoningAgent, Tool

def my_special_tool(x: str) -> str:
    ...

special = Tool(
    name="my_special_tool",
    description="Does the special thing",
    parameters={...json schema...},
    func=my_special_tool,
)

agent = VisibleReasoningAgent(tools=[special, *other_tools])
```

## Project Structure (after `pip install -e .`)

```
nemotron_think/
├── agent.py          # VisibleReasoningAgent + AgentRun/AgentStep
├── tools.py          # Tool dataclass + DEFAULT_TOOLS
├── helpers.py        # Low-level streaming + trace capture (you rarely touch)
├── cli.py            # The `nemotron-think` command
└── __init__.py
```

## Traces

Every `run()` produces a rich `AgentRun` (steps + per-step `ReasoningTrace` + final answer).

They are automatically saved under `traces/`. You can also do `run.save("my.trace.json")`.

These traces are the real value — commit them, share them, build UIs on top of them, use them for fine-tuning data.

## Recommended Use Cases (where this shines)

- Hard logic, math, algorithm design, planning
- Research agents that need to cite current information
- Code agents that write + test + fix (visible reasoning makes the loop trustworthy)
- Anything where you want an audit trail of the model's thoughts

## Environment variables

- `NVIDIA_API_KEY` (required)
- `NVIDIA_MODEL` (optional, defaults to the Ultra path)
- `NVIDIA_BASE_URL`

## Status & Roadmap

This is a focused, useful seed for a production-grade visible reasoning agent framework.

High-value extensions people usually add next:
- More robust sandbox for `python_exec` (e2b, modal, firecracker, etc.)
- Real web browser tool (Playwright + readability)
- Persistence of long-running agent sessions
- LangGraph / CrewAI / AutoGen adapters that surface the thinking
- Web UI for trace visualization + scrubber

## Credits

Built to highlight the capabilities of NVIDIA Nemotron 3 Ultra (the model behind the early `private/nvidia/nemotron-3-ultra-550b-a55b` access and its public successors on integrate.api.nvidia.com).

The streaming helpers originated from early internal walkthrough notebooks for the model and were significantly cleaned up and extended here.

---

**Make the model's thinking visible. Build agents people can actually trust and learn from.**
