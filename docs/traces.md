# Traces & Replay

One of the most powerful features of `nemotron-think` is that **every agent execution is fully captured** as a rich, serializable JSON document called an `AgentRun`.

## Why traces matter

- **Auditability** — you can see every reasoning token the model produced before it decided to call a tool or answer.
- **Reproducibility** — `nemotron-think replay` gives you the exact same terminal experience without any API calls.
- **Dataset creation** — the `reasoning` + `tool_calls` + `observations` triples are perfect for supervised fine-tuning or preference data.
- **Eval & research** — run hundreds of tasks, save the traces, then analyze reasoning quality, tool-use patterns, self-correction rate, etc.
- **Demos** — record your terminal while replaying a great trace; the audience sees the thinking process live.

## The data model (simplified)

```json
{
  "task": "...",
  "model": "private/nvidia/nemotron-3-ultra-550b-a55b",
  "steps": [
    {
      "step": 1,
      "user_message": "...",
      "reasoning": "The full visible thinking the model streamed...",
      "content": "Partial or final content the model produced (often empty when using tools)",
      "tool_calls": [ { "id": "...", "function": { "name": "web_search", "arguments": "..." } } ],
      "tool_results": [ { "role": "tool", "tool_call_id": "...", "content": "..." } ],
      "trace": { /* the low-level ReasoningTrace captured from the stream */ },
      "timestamp": "..."
    }
  ],
  "final_answer": "The last content the model produced when it stopped calling tools.",
  "total_tool_calls": 3,
  "config": { "reasoning_budget": 8192, ... },
  "created_at": "..."
}
```

The inner `trace` object (a `ReasoningTrace`) contains the raw chunked streams:

- `reasoning_chunks`
- `content_chunks`
- `final_content`
- `raw_tool_acc` (the incremental argument building state)

## Automatic saving

The CLI always saves a trace for you:

```bash
nemotron-think run "your task here"
# → traces/your_task_here.json   (sanitized filename)
```

You can override the location:

```bash
nemotron-think run "..." --save-trace my-special-run.json
```

From Python:

```python
run = agent.run("...")
run.save("experiments/hard_problem_042.json")
```

## Listing and managing traces

```bash
nemotron-think list
```

Shows a nice table of all traces in `./traces/`.

## Replaying

```bash
nemotron-think replay traces/hard_problem_042.json
nemotron-think replay traces/hard_problem_042.json --no-reasoning   # hide the green thinking parts
```

Replay reconstructs the `AgentStep` objects and uses the same pretty-printing logic as live runs.

## Working with traces programmatically

```python
import json
from nemotron_think.helpers import load_trace   # or just json.load

with open("traces/math_tool_example.json") as f:
    data = json.load(f)

for step in data["steps"]:
    print("Reasoning length:", len(step["reasoning"]))
    if step["tool_calls"]:
        print("Tools used:", [t["function"]["name"] for t in step["tool_calls"]])
```

The package also exposes:

```python
from nemotron_think import ReasoningTrace
# (ReasoningTrace is the dataclass used internally)
```

## Best practices

1. **Commit good traces** — put high-quality examples under `examples/traces/` (they are not git-ignored).
2. **Name traces descriptively** — include task keywords or a short slug.
3. **Version your traces** — if you change the agent loop or model, store them under dated folders or add a `agent_version` field.
4. **Use for regression** — before a big refactor, save a golden set of traces and add a test that replays them and asserts the final answer + tool sequence is stable.
5. **Build on top** — the JSON is deliberately simple. You can feed it straight into a Gradio/Streamlit UI, a trace visualizer, or a fine-tuning pipeline.

## Example trace included

See `examples/traces/math_tool_example.json` — a minimal single-step trace that uses `get_math_answer`.

Load it with the replay command:

```bash
nemotron-think replay examples/traces/math_tool_example.json
```

## Future ideas (community)

- Trace diffing tool (`nemotron-think diff trace1.json trace2.json`)
- Trace search / semantic index over reasoning
- Export to Hugging Face `datasets` format
- Web UI with step scrubber and token highlighting (the `docs/index.html` landing page is a first step toward this)

---

Traces turn ephemeral agent runs into durable, shareable, analyzable artifacts. This is one of the biggest reasons to use `nemotron-think` instead of a generic ReAct loop.
