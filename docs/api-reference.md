# API Reference

## Core exports

```python
from nemotron_think import (
    VisibleReasoningAgent,
    AgentRun,
    AgentStep,
    Tool,
    DEFAULT_TOOLS,
    ReasoningTrace,
)
```

## VisibleReasoningAgent

The main class.

### `__init__(...)`

```python
agent = VisibleReasoningAgent(
    tools: Optional[List[Tool]] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    max_steps: int = 6,
    default_reasoning_budget: Optional[int] = 4096,
    default_low_effort: bool = False,
)
```

- `tools` — list of `Tool` objects. Defaults to the four built-in tools.
- `model` / `api_key` / `base_url` — override the NVIDIA endpoint (normally read from env + sensible defaults inside `get_client`).
- `max_steps` — safety cap on the ReAct-style loop.
- `default_reasoning_budget` — tokens the model is allowed to spend thinking per turn (passed via `reasoning_budget` in extra_body).
- `default_low_effort` — when True, adds `low_effort: true` to `chat_template_kwargs`.

### `run(...) -> AgentRun`

```python
run = agent.run(
    task: str,
    reasoning_budget: Optional[int] = None,
    low_effort: Optional[bool] = None,
    max_steps: Optional[int] = None,
    save_every_step: bool = False,
    trace_dir: str = "traces",
) -> AgentRun
```

Executes the visible reasoning loop:

1. Sends the current conversation + tools + thinking flags.
2. Streams and prints reasoning (green) + content + live tool deltas (orange).
3. If the model emitted tool calls, executes them locally and feeds results back.
4. Repeats until the model produces a final answer with no tool calls, or `max_steps` is reached.

Returns a fully populated `AgentRun`.

Extra options:

- `save_every_step=True` also writes individual low-level `ReasoningTrace` JSON files (advanced debugging).

### Other methods / helpers

- `pretty_print_step(step: AgentStep, show_reasoning: bool = True)` — utility used by the CLI replay command. Safe to call yourself for custom display.

## AgentRun

Dataclass representing a complete execution.

### Fields

| Field            | Type              | Description |
|------------------|-------------------|-----------|
| task             | str               | The original user task |
| model            | str               | Model identifier used |
| steps            | List[AgentStep]   | Every turn the agent took |
| final_answer     | str               | The last content the model emitted when it stopped using tools |
| total_tool_calls | int               | Count of tool invocations across all steps |
| config           | Dict[str, Any]    | The reasoning_budget, low_effort, max_steps that were active |
| created_at       | str               | ISO timestamp |

### Methods

- `to_json() -> str` — pretty JSON string
- `save(path: str)` — writes the JSON to disk and prints a green confirmation (uses rich)

## AgentStep

One full turn of the agent.

### Fields

- `step: int`
- `user_message: Optional[str]` — only present on step 1
- `reasoning: str` — concatenated visible reasoning tokens
- `content: str` — concatenated final content for this turn (often empty when tools were used)
- `tool_calls: List[Dict]`
- `tool_results: List[Dict]`
- `trace: Optional[ReasoningTrace]`
- `timestamp: str`

## Tool

Lightweight dataclass for pluggable tools.

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]   # JSON Schema "properties" object
    func: Callable[..., Any]

    def to_openai_spec(self) -> Dict[str, Any]:
        ...
```

See [Extending with Custom Tools](extending-tools.md) for examples.

## ReasoningTrace (low-level)

Captured directly from the streaming response. Useful when you want the raw chunk lists.

```python
@dataclass
class ReasoningTrace:
    prompt: str
    model: str
    reasoning_chunks: List[str]
    content_chunks: List[str]
    final_content: str
    tool_calls: List[Dict]
    raw_tool_acc: Dict[int, Dict[str, str]]
    extra_body: Optional[Dict] = None
    timestamp: str
```

Helper functions in `nemotron_think.helpers`:

- `stream_and_capture(...) -> ReasoningTrace`
- `save_trace(trace, path)`
- `load_trace(path) -> dict`

Most users interact with the higher-level `AgentRun` / `AgentStep` instead.

## Client helpers (advanced)

If you want to build your own loops on top of the streaming primitives:

```python
from nemotron_think.helpers import (
    get_client,
    create_stream,
    stream_reasoning_content,
    execute_local_tools,
)
```

These are what power the agent under the hood.

## Environment / configuration

See [Configuration](configuration.md).

## Full source

All implementation lives in four small files under `nemotron_think/`. The whole library (excluding tests) is < 1200 LOC. Easy to read and fork.
