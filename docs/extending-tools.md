# Extending with Custom Tools

The `Tool` abstraction is deliberately minimal so you can add domain-specific capabilities in just a few lines.

## The Tool dataclass

```python
from nemotron_think import Tool

def my_tool(arg1: str, count: int = 3) -> str:
    """Does something useful."""
    ...

my_tool_def = Tool(
    name="my_tool",
    description="Short description the model sees. Be precise about when to use it.",
    parameters={
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "What arg1 means"},
            "count": {"type": "integer", "description": "Optional count"},
        },
        "required": ["arg1"],
    },
    func=my_tool,
)
```

- `parameters` is the **inner** JSON Schema object that goes under `function.parameters` in the OpenAI tool spec.
- The `func` receives **keyword arguments** after the model’s JSON is parsed. You can use defaults.

## Passing tools to the agent

```python
from nemotron_think import VisibleReasoningAgent, DEFAULT_TOOLS

agent = VisibleReasoningAgent(
    tools=[my_tool_def, *DEFAULT_TOOLS]
)
```

You can also completely replace the defaults:

```python
agent = VisibleReasoningAgent(tools=[my_tool_def, another_tool])
```

## Real-world example: a file reader (read-only)

```python
import os
from nemotron_think import Tool, VisibleReasoningAgent

def read_text_file(path: str, max_chars: int = 8000) -> str:
    if not os.path.exists(path):
        return f"ERROR: file not found: {path}"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars)
        return content if content else "(empty file)"
    except Exception as e:
        return f"ERROR reading {path}: {e}"

file_tool = Tool(
    name="read_text_file",
    description="Read the contents of a UTF-8 text file on the local filesystem (read-only). Use for inspecting code, logs, configs, or documentation that the user has explicitly allowed.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative path to the file"},
            "max_chars": {"type": "integer", "description": "Maximum characters to return (default 8000)"},
        },
        "required": ["path"],
    },
    func=lambda path, max_chars=8000: read_text_file(path, int(max_chars)),
)

agent = VisibleReasoningAgent(tools=[file_tool, *DEFAULT_TOOLS])
```

## Important safety notes

The default `python_exec` tool has very basic guards (it refuses obvious dangerous patterns). It is **not** a hardened sandbox.

When you add tools that touch the filesystem, network, or execute code:

- Document the risks clearly in the tool `description`.
- Consider running the whole agent inside a container / firejail / gvisor / e2b-style sandbox for untrusted tasks.
- For production, add allow-lists, path scoping, rate limits, and human-in-the-loop confirmation for dangerous actions.

## Tool result format

Whatever your `func` returns is turned into a string and sent back to the model as a `role: "tool"` message. The model sees it in the next reasoning turn.

Return values should be:

- Concise when possible (the model has context limits)
- Informative on error (include the error message)
- Structured when it helps the model (JSON, markdown tables, etc.)

## Observing tool use in traces

When a custom tool is called, it appears in `step.tool_calls` and `step.tool_results` exactly like the built-ins. The `trace` sub-object records the exact arguments the model streamed.

This makes custom tools first-class citizens for evals and replay.

## Advanced: dynamic tool sets

You can create different `VisibleReasoningAgent` instances with different tool lists for different phases of a workflow (e.g. a “research” agent vs a “coder” agent) and even swap them mid-run if you maintain the message history yourself.

## Contributing new default tools

If you have a generally useful, safe, zero-config tool that would benefit most users, open a PR. We prefer tools that:

- Require no extra API keys
- Are read-only or have clear side-effect boundaries
- Return compact, high-signal observations
- Have excellent `description` text (this is the most important part for the model)

See current defaults in `nemotron_think/tools.py`.

---

Custom tools are how you turn the generic visible-reasoning engine into a **domain expert agent**.
