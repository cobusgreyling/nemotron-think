# nemotron-think Documentation

Welcome to the documentation for **nemotron-think** — the Visible Reasoning Agent Framework for NVIDIA Nemotron 3 Ultra.

## What is this?

`nemotron-think` makes the model's internal thinking process **visible** at every step:

- The chain-of-thought / reasoning tokens the model produces before deciding what to do
- The incremental construction of tool call arguments (you literally watch JSON being written token-by-token)
- The observations that come back from tools
- The final answer after self-correction

All of this is captured into rich, replayable, serializable `AgentRun` objects.

## Quick links

- [Getting Started](getting-started.md)
- [Traces & Replay](traces.md)
- [API Reference](api-reference.md)
- [Extending with Custom Tools](extending-tools.md)
- [Configuration & Environment](configuration.md)

## Interactive landing page

For the best first experience, open the self-contained landing page in your browser:

```bash
# from the repo root
open docs/index.html        # macOS
xdg-open docs/index.html    # Linux
start docs/index.html       # Windows
```

It includes:

- Hero with project positioning
- Feature highlights
- Fully interactive trace replay of the included math example (no API key needed)
- One-click copy install commands
- Embedded code examples

## Philosophy

Most agent frameworks hide the model's reasoning. `nemotron-think` does the opposite: it treats the visible reasoning as a first-class product feature.

This is only possible because of the special capabilities of the Nemotron 3 Ultra family:

- Native `enable_thinking` + `reasoning_content` / `reasoning` delta streaming
- Explicit `reasoning_budget` control
- Excellent long-horizon coherence and self-correction when tool results are fed back

The framework is intentionally small and focused. The entire core is a few hundred lines. The goal is to be the thinnest possible layer that makes these capabilities usable and showcaseable.

## Contributing

Issues and PRs are welcome. Especially valuable:

- More robust example traces (hard problems + beautiful reasoning)
- Improvements to the trace replay UI in `docs/index.html`
- Additional safe, zero-config tools
- Better sandboxing stories for `python_exec`
- Adapters for popular agent frameworks that preserve the visible thinking

## License

MIT — see [LICENSE](../LICENSE) at the repo root.

---

**Make the model's thinking visible.**
