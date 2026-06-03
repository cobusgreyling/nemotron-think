# Configuration & Environment

## Required

| Variable          | Description                          | Example |
|-------------------|--------------------------------------|---------|
| `NVIDIA_API_KEY`  | Your NVIDIA API key (nvapi-...)      | `nvapi-abc123...` |

## Optional

| Variable           | Description                                      | Default |
|--------------------|--------------------------------------------------|---------|
| `NVIDIA_MODEL`     | Model identifier to use                          | `private/nvidia/nemotron-3-ultra-550b-a55b` |
| `NVIDIA_BASE_URL`  | OpenAI-compatible endpoint base                  | `https://integrate.api.nvidia.com/v1` |
| `STREAM_TIMEOUT_SECONDS` | Overall timeout for a single streaming call | `1800` (30 min) |

## .env file

The package loads a `.env` file from the current working directory using `python-dotenv` (already a dependency).

Example (committed as `.env.example`):

```env
NVIDIA_API_KEY=your-nvapi-key-here
# NVIDIA_MODEL=private/nvidia/nemotron-3-ultra-550b-a55b
# NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

## Programmatic overrides

You can pass credentials directly when constructing the agent (useful for multi-tenant or testing):

```python
agent = VisibleReasoningAgent(
    api_key="nvapi-...",
    base_url="https://integrate.api.nvidia.com/v1",
    model="private/nvidia/nemotron-3-ultra-550b-a55b",
)
```

Any value passed to the constructor takes precedence over environment variables.

## Reasoning budget & low effort

These are **per-run** (or per-step) controls exposed both on the CLI and in the Python API:

```bash
nemotron-think run "..." --budget 8192
nemotron-think run "..." --low-effort --budget 1024
```

In Python:

```python
run = agent.run(
    task="...",
    reasoning_budget=8192,
    low_effort=False,
)
```

Inside the implementation these become:

```json
{
  "reasoning_budget": 8192,
  "chat_template_kwargs": {
    "enable_thinking": true,
    "low_effort": false
  }
}
```

- Higher `reasoning_budget` → the model can produce more thinking tokens before it has to act or answer. Great for hard planning / research.
- `low_effort: true` → trades some quality for speed / lower cost (model-dependent behavior).

## Rich output & colors

The CLI and agent use the `rich` library for beautiful panels and rules.

- Color is automatically disabled when `NO_COLOR` is set or stdout is not a TTY.
- Reasoning is printed in green, tool progress in orange (256-color).

You can force plain output for logging/CI:

```bash
NO_COLOR=1 nemotron-think run "..."
```

## Timeouts

Long-horizon agents with high reasoning budgets can take a long time. The default 30-minute per-call timeout is generous. You can lower it via `STREAM_TIMEOUT_SECONDS` if desired.

## Logging / observability (future)

Currently all “logs” are the colored live stream + the saved `AgentRun` JSON.

For production you can:

- Capture `run.to_json()` and ship it to your observability backend
- Wrap `stream_and_capture` yourself and add OpenTelemetry spans
- Add a small exporter (the sister project `agent-failure-analyzer` in the same org has OTLP exporters you could adapt)

## Multiple keys / switching models

If you work with several NVIDIA projects, use direnv, shell aliases, or a small wrapper:

```bash
alias nemotron-ultra='NVIDIA_MODEL=... NVIDIA_API_KEY=... nemotron-think'
```

Or create lightweight agent factories in your own code.

## Security notes

- Never commit real API keys.
- The `.gitignore` already ignores `.env`.
- Tools you add can be dangerous — see the safety section in [Extending with Custom Tools](extending-tools.md).
