<p align="center">
  <img src="assets/header-agent.jpg" width="100%" alt="nemotron-think — Visible Reasoning Agent Framework for NVIDIA Nemotron 3 Ultra">
</p>

<p align="center">
  <strong>🌐 <a href="https://github.com/cobusgreyling/nemotron-think/blob/main/docs/index.html">Open the interactive landing page + live trace demo</a></strong><br>
  <small>
    (Best: clone &amp; <code>open docs/index.html</code> locally. For a free public URL use the one-click Vercel/Netlify buttons below — works with private repos.)
  </small>
</p>

# nemotron-think

**Visible Reasoning Agent Framework for NVIDIA Nemotron 3 Ultra**

[![PyPI](https://img.shields.io/badge/pip%20install-nemotron--think-blue)](https://github.com/cobusgreyling/nemotron-think)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Every step the model takes — its internal reasoning, why it chose a tool, the incremental tool call JSON, the observations — is **logged and surfaced** in real time.

This is not another wrapper. It is purpose-built to showcase (and productionize) the unique strengths of **Nemotron 3 Ultra**:

- `enable_thinking` + controllable `reasoning_budget`
- Extremely high-quality long-horizon reasoning
- Streamed `delta.tool_calls` (watch the arguments being built live)
- Reliable self-correction when you feed tool results back

---

## 🚀 Quickstart

```bash
git clone https://github.com/cobusgreyling/nemotron-think.git
cd nemotron-think
python -m venv .venv && source .venv/bin/activate
pip install -e .

cp .env.example .env
# edit .env and add your NVIDIA API key (nvapi-...)
```

```bash
# Explore built-in tools
nemotron-think tools

# Run a visible reasoning agent (the whole point of the project)
nemotron-think run "A bat and a ball cost $1.10. The bat costs $1 more than the ball. How much does the ball cost? Show your full reasoning and explain the common mistake."

# Use more thinking power + persist the complete trace
nemotron-think run "Research the current best open-source text-to-video models (last 6 months). List the top 3 with licenses, GitHub stars if available, and key differentiators." --budget 8192 --save-trace traces/video_research.json

# Replay any trace later (perfect for demos, talks, no API calls)
nemotron-think replay traces/video_research.json
```

Live terminal output uses color:

- **Green** = model reasoning / thinking tokens
- **Orange** = tool call progress (incremental JSON building)
- Clean final answer

---

## 🌐 Landing Page & Full Documentation

**Important:** GitHub Pages only works for **public** repositories on the free plan. Private repos require a paid plan (Pro+) for Pages. See the official docs: GitHub Pages is available in public repositories with GitHub Free, and in public **and private** repositories only with GitHub Pro, Team, or Enterprise.

### Current options for the showcase

- **View on GitHub** (recommended while repo is private): [docs/index.html](https://github.com/cobusgreyling/nemotron-think/blob/main/docs/index.html) — click the **Raw** button at the top for the full rendered interactive page.
- **Local / fully offline** (best current experience): From the cloned repo, run `open docs/index.html` (or `xdg-open` / double-click). The page is completely self-contained.
- **Free public hosted version (recommended for sharing)**: Deploy the `docs/` folder to Vercel or Netlify (works great with private GitHub repos on the free tier). One-click options below.

#### One-click deploy (free public URL)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fcobusgreyling%2Fnemotron-think&project-name=nemotron-think&repository-name=nemotron-think)
[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/cobusgreyling/nemotron-think)

(After deploying, set the publish directory to `docs` if the UI asks.)

To enable the official `https://cobusgreyling.github.io/nemotron-think/` URL, you must either:
- Make this repository **public**, then enable GitHub Pages (Settings → Pages → Source: `main` / `/docs`), **or**
- Upgrade your GitHub account to Pro (or higher).
- **Official hosted web version**: [https://cobusgreyling.github.io/nemotron-think/](https://cobusgreyling.github.io/nemotron-think/) — enable GitHub Pages (see instructions in `docs/README.md`).
- **Detailed Docs**: see the `docs/` folder:
  - [Getting Started](docs/getting-started.md)
  - [Traces & Replay](docs/traces.md)
  - [API Reference](docs/api-reference.md)
  - [Extending with Custom Tools](docs/extending-tools.md)
  - [Configuration & Environment](docs/configuration.md)

Or view on GitHub: browse the `docs/` directory.

---

## Python API

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
    print(f"Step {step.step} reasoning: {step.reasoning[:300]}...")
```

---

## What makes this useful

| Use Case              | Why nemotron-think shines |
|-----------------------|-----------------------------|
| **Debugging & trust** | Finally see *why* the model called a tool or reached a conclusion |
| **Eval & datasets**   | Every `AgentRun` is rich JSON with full reasoning traces — perfect for creating reasoning datasets or running evals |
| **Demos & talks**     | `nemotron-think replay` + terminal recordings = extremely compelling demos |
| **Production agents** | The same loop you use for impressive demos can be the core of real tools (research, coding, planning agents) |
| **Controllability**   | Dial `reasoning_budget` and `low_effort` per run or per step |

---

## Pluggable Tools

Current defaults (all visible to the model with proper schemas):

- `get_math_answer` — safe calculator
- `get_current_time`
- `python_exec` — execute and observe Python code (with basic guards)
- `web_search` — current web information via DuckDuckGo (no extra keys)

Adding your own tool is ~5 lines:

```python
from nemotron_think import VisibleReasoningAgent, Tool

def my_special_tool(x: str) -> str:
    return f"Special result for {x}"

special = Tool(
    name="my_special_tool",
    description="Does the special thing",
    parameters={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
    func=my_special_tool,
)

agent = VisibleReasoningAgent(tools=[special, *DEFAULT_TOOLS])
```

See full guide: [docs/extending-tools.md](docs/extending-tools.md)

---

## Project Structure

```
nemotron-think/
├── assets/
│   └── header-agent.jpg
├── docs/                    # Full documentation + interactive web landing page (docs/index.html)
├── examples/
│   └── traces/
│       └── math_tool_example.json
├── nemotron_think/
│   ├── __init__.py
│   ├── agent.py          # VisibleReasoningAgent + AgentRun/AgentStep
│   ├── tools.py          # Tool dataclass + DEFAULT_TOOLS
│   ├── helpers.py        # Low-level streaming + trace capture
│   └── cli.py            # The `nemotron-think` command
├── pyproject.toml
├── README.md
└── ...
```

---

## Traces — the real value

Every `run()` produces a rich `AgentRun` (steps + per-step `ReasoningTrace` + final answer).

Traces are automatically saved under `traces/`. You can also `run.save("my.trace.json")`.

These traces are **gold** — commit them, share them, build UIs on top of them, use them for fine-tuning data, or replay for demos without spending tokens.

```bash
nemotron-think list          # see all your local traces
nemotron-think replay path/to/trace.json --no-reasoning
```

See: [docs/traces.md](docs/traces.md)

---

## Recommended Use Cases

- Hard logic, math, algorithm design, planning
- Research agents that need to cite current information
- Code agents that write + test + fix (visible reasoning makes the loop trustworthy)
- Anything where you want an audit trail of the model's thoughts

---

## Environment Variables

- `NVIDIA_API_KEY` (required) — your `nvapi-...` key
- `NVIDIA_MODEL` (optional) — defaults to the Ultra path `private/nvidia/nemotron-3-ultra-550b-a55b`
- `NVIDIA_BASE_URL` (optional)

---

## Status & Roadmap

Focused, useful seed for a production-grade visible reasoning agent framework.

High-value extensions people usually add next:

- More robust sandbox for `python_exec` (e2b, modal, firecracker, etc.)
- Real web browser tool (Playwright + readability)
- Persistence of long-running agent sessions
- LangGraph / CrewAI / AutoGen adapters that surface the thinking
- Web UI for trace visualization + scrubber (the `docs/index.html` is a starting point)

---

## Credits

Built to highlight the capabilities of **NVIDIA Nemotron 3 Ultra** (the model behind the early private access and its public successors on `integrate.api.nvidia.com`).

The streaming helpers originated from early internal walkthrough notebooks for the model and were significantly cleaned up and extended here.

---

**Make the model's thinking visible. Build agents people can actually trust and learn from.**

<p align="center">
  <a href="https://github.com/cobusgreyling/nemotron-think/blob/main/docs/index.html">🌐 Open the interactive landing page & live trace demo</a>
</p>
