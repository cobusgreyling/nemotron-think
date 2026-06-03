# Getting Started

This guide gets you from zero to a running visible-reasoning agent in under 5 minutes.

## Prerequisites

- Python 3.10+
- An NVIDIA API key with access to Nemotron 3 Ultra (or compatible model)
  - Sign up / request access at https://build.nvidia.com/ or the integrate.api.nvidia.com portal
- (Optional but recommended) A modern terminal with color support

## Installation

### From source (recommended for development)

```bash
git clone https://github.com/cobusgreyling/nemotron-think.git
cd nemotron-think

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e .
```

### Via pip (latest from git)

```bash
pip install git+https://github.com/cobusgreyling/nemotron-think.git
```

## Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
NVIDIA_API_KEY=your-nvapi-...-key-here
# NVIDIA_MODEL=private/nvidia/nemotron-3-ultra-550b-a55b   # optional
# NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1      # optional
```

You can also set the variables directly in your shell.

## Verify the CLI works

```bash
nemotron-think --help
nemotron-think tools
```

You should see the four default tools listed.

## Run your first visible agent

```bash
nemotron-think run "A bat and a ball cost $1.10. The bat costs $1 more than the ball. How much does the ball cost? Think step by step out loud."
```

Watch the magic:

- Green text = the model’s visible reasoning (the `enable_thinking` stream)
- Orange text = live tool-call argument building (`delta.tool_calls`)
- Final clean answer when the model decides it is done

## Save and replay traces

```bash
nemotron-think run "Research the top 3 most starred open source LLM evaluation frameworks in 2025." \
  --budget 8192 \
  --save-trace traces/eval-frameworks.json

nemotron-think replay traces/eval-frameworks.json
```

Replays are 100% offline and perfect for:

- Conference demos
- Sharing exact model behavior with teammates
- Building datasets
- Debugging agent logic without burning quota

## Next steps

- Read [Traces & Replay](traces.md) to understand the rich JSON format
- Read [API Reference](api-reference.md) for embedding in your own code
- Read [Extending with Custom Tools](extending-tools.md)
- Open `docs/index.html` in your browser for the interactive landing page + live trace player

## Common issues

**"No NVIDIA API key provided"**

- Make sure `NVIDIA_API_KEY` is set in the environment or `.env` is loaded (the package uses `python-dotenv`).

**Tool calls look truncated or weird**

- The streaming delta accumulation is defensive. If you see issues, open an issue with the exact model + client version.

**Want lower cost / faster responses?**

```bash
nemotron-think run "..." --low-effort --budget 2048
```

## Python one-liner test

```python
from nemotron_think import VisibleReasoningAgent
agent = VisibleReasoningAgent(max_steps=3, default_reasoning_budget=2048)
run = agent.run("What is 15% of 880?")
print(run.final_answer)
```

---

**Tip**: Start with small `reasoning_budget` (1024–4096) for quick experiments, then dial it up for hard problems.
