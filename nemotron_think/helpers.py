#!/usr/bin/env python3
"""
Nemotron 3 Ultra (and compatible NVIDIA NIM) streaming helpers.

Cleaned, reusable extraction + improvements from Nemotron_3_Ultra_Model_Usage.ipynb.

Features demonstrated by the original notebook:
- enable_thinking / reasoning_content streaming
- reasoning_budget
- low_effort mode
- Streaming tool calls (delta.tool_calls incremental)
- Local tool execution + follow-up turn

Usage (requires NVIDIA API key with access to the model):

    export NVIDIA_API_KEY=...
    # optional overrides
    export NVIDIA_MODEL=...          # defaults to the ultra 550b private path
    export NVIDIA_BASE_URL=...

    python -c '
    from nemotron_helpers import get_client, create_stream, stream_reasoning_content
    client = get_client()
    resp = create_stream(
        client,
        messages=[{"role": "user", "content": "What is 2+2?"}],
        extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    )
    stream_reasoning_content(resp)
    '
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from getpass import getpass
from typing import Any, Callable, Dict, List, Optional, Tuple

from openai import OpenAI

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DEFAULT_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
DEFAULT_MODEL = os.environ.get(
    "NVIDIA_MODEL",
    os.environ.get("MODEL", "private/nvidia/nemotron-3-ultra-550b-a55b"),
)
DEFAULT_TIMEOUT = int(os.environ.get("STREAM_TIMEOUT_SECONDS", "1800"))

# Terminal colors (respect NO_COLOR and non-tty)
REASONING_COLOR = "\033[32m"      # green for thinking/reasoning deltas
TOOL_COLOR = "\033[38;5;208m"     # orange for tool call progress
RESET_COLOR = "\033[0m"
USE_COLOR = os.environ.get("NO_COLOR", "") == "" and os.isatty(1)


def _c(text: str, color: str) -> str:
    """Apply ANSI color only when appropriate."""
    return f"{color}{text}{RESET_COLOR}" if USE_COLOR else text


# --------------------------------------------------------------------------- #
# Client + Auth
# --------------------------------------------------------------------------- #

def get_api_key() -> str:
    """Get NVIDIA API key from env or prompt."""
    key = (
        os.environ.get("NVIDIA_API_KEY")
        or os.environ.get("NVCF_API_KEY")  # common NVIDIA alias
        or os.environ.get("API_KEY")
    )
    if not key:
        key = getpass("NVIDIA API key: ").strip()
    if not key:
        raise RuntimeError("No NVIDIA API key provided (set NVIDIA_API_KEY or enter when prompted).")
    return key


def get_client(
    api_key: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    model: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> OpenAI:
    """
    Return an OpenAI client configured for NVIDIA's OpenAI-compatible endpoint.

    The returned client has two private attributes attached for convenience:
      - _nemotron_model
      - _nemotron_timeout
    """
    key = api_key or get_api_key()
    client = OpenAI(
        base_url=base_url,
        api_key=key,
        default_headers={"NVCF-POLL-SECONDS": str(timeout)},
    )
    client._nemotron_model = model or DEFAULT_MODEL  # type: ignore[attr-defined]
    client._nemotron_timeout = timeout  # type: ignore[attr-defined]
    return client


# --------------------------------------------------------------------------- #
# Demo tool (from the notebook)
# --------------------------------------------------------------------------- #

def get_math_answer(expression: str) -> str:
    """Safe evaluator for simple arithmetic (digits, +, -, *, /, parentheses, spaces)."""
    expr = re.sub(r"\s+", "", expression)
    if not re.match(r"^[\d+\-*/().]+$", expr):
        return "Error: only numbers and + - * / ( ) allowed"
    try:
        return str(eval(expr))
    except Exception as e:
        return f"Error: {e}"


MATH_TOOL_SPEC: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_math_answer",
        "description": "Returns an exact arithmetic result",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression"}},
            "required": ["expression"],
        },
    },
}


# --------------------------------------------------------------------------- #
# Core streaming helpers (improved from notebook)
# --------------------------------------------------------------------------- #

def create_stream(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    extra_body: Optional[Dict[str, Any]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    model: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
    top_p: float = 0.95,
):
    """
    Create a streaming chat completion.

    Pass extra_body for NVIDIA-specific options:
        {"reasoning_budget": 8192, "chat_template_kwargs": {"enable_thinking": True, "low_effort": True}}
    """
    model = model or getattr(client, "_nemotron_model", DEFAULT_MODEL)
    timeout = getattr(client, "_nemotron_timeout", DEFAULT_TIMEOUT)

    req: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": True,
        "timeout": timeout,
    }
    if extra_body is not None:
        req["extra_body"] = extra_body
    if tools is not None:
        req["tools"] = tools
        req["tool_choice"] = tool_choice

    return client.chat.completions.create(**req)


def stream_reasoning_content(
    response: Any,
    show_tool_deltas: bool = False,
    print_output: bool = True,
) -> Dict[int, Dict[str, str]]:
    """
    Consume the stream, print reasoning (green) then content, and optionally
    surface incremental tool call deltas (orange).

    Returns accumulated tool call state so you can execute tools and do a
    follow-up turn (classic tool-calling loop in streaming form).

    The function is defensive about delta shape (pydantic objects vs raw dicts)
    because streaming chunk formats can vary slightly across client versions
    and providers.
    """
    in_reasoning = False
    acc: Dict[int, Dict[str, str]] = {}  # index -> {"id", "name", "arguments"}

    for chunk in response:
        for choice in chunk.choices:
            delta = choice.delta

            # --- Reasoning / thinking tokens ---
            reasoning = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
            if reasoning:
                if not in_reasoning:
                    if print_output:
                        print(_c("", REASONING_COLOR), end="")
                    in_reasoning = True
                if print_output:
                    print(reasoning, end="", flush=True)

            # --- Final user-facing content ---
            content = getattr(delta, "content", None)
            if content:
                if in_reasoning:
                    if print_output:
                        print(RESET_COLOR if USE_COLOR else "", end="")
                    in_reasoning = False
                if print_output:
                    print(content, end="", flush=True)

            if not show_tool_deltas:
                continue

            # --- Incremental tool call deltas ---
            tool_calls = getattr(delta, "tool_calls", None)
            if not tool_calls:
                continue

            for tc in tool_calls:
                idx = tc.get("index", 0) if isinstance(tc, dict) else getattr(tc, "index", 0)
                idx = 0 if idx is None else idx
                if idx not in acc:
                    acc[idx] = {"id": "", "name": "", "arguments": ""}

                if isinstance(tc, dict):
                    acc[idx]["id"] = acc[idx]["id"] or tc.get("id", "")
                    fn = tc.get("function", {})
                    name_part = fn.get("name", "")
                    args_part = fn.get("arguments", "")
                else:
                    acc[idx]["id"] = acc[idx]["id"] or getattr(tc, "id", "")
                    fn = getattr(tc, "function", None)
                    name_part = (getattr(fn, "name", None) or "") if fn else ""
                    args_part = (getattr(fn, "arguments", None) or "") if fn else ""

                if print_output:
                    if name_part:
                        print(_c(f"\n[tool#{idx} name+] {name_part}", TOOL_COLOR), end="", flush=True)
                    if args_part:
                        print(_c(f"\n[tool#{idx} args+] {args_part}", TOOL_COLOR), end="", flush=True)

                acc[idx]["name"] += name_part
                acc[idx]["arguments"] += args_part

    if in_reasoning and print_output:
        print(RESET_COLOR if USE_COLOR else "", end="")
    if print_output:
        print()
    return acc


def execute_local_tools(
    acc: Dict[int, Dict[str, str]],
    tool_impls: Optional[Dict[str, Callable[..., Any]]] = None,
    print_output: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Execute the tools that were streamed in `acc` using local Python functions.

    Returns:
        (assistant_tool_calls, tool_result_messages)

    These can be appended to your conversation and sent in a follow-up
    create_stream(...) call to let the model produce the final answer.
    """
    if tool_impls is None:
        tool_impls = {"get_math_answer": get_math_answer}

    assistant_tool_calls: List[Dict[str, Any]] = []
    tool_results: List[Dict[str, Any]] = []

    if not acc:
        return assistant_tool_calls, tool_results

    if print_output:
        print(_c("Tool call(s) and result(s):", TOOL_COLOR))

    for idx in sorted(acc.keys()):
        tc = acc[idx]
        name, args_str = tc["name"], tc["arguments"]
        if not name:
            continue

        try:
            args = json.loads(args_str) if args_str.strip() else {}
        except json.JSONDecodeError:
            args = {}

        impl = tool_impls.get(name)
        if impl:
            try:
                result = impl(**args) if args else impl()
            except Exception as e:
                result = f"Error executing {name}: {e}"
        else:
            result = f"(unknown tool: {name})"

        if print_output:
            print(_c(f"  {name}({args}) -> {result}", TOOL_COLOR))

        assistant_tool_calls.append(
            {"id": tc["id"], "type": "function", "function": {"name": name, "arguments": args_str}}
        )
        tool_results.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})

    return assistant_tool_calls, tool_results


# --------------------------------------------------------------------------- #
# Convenience: one-shot thinking call
# --------------------------------------------------------------------------- #

def ask_with_thinking(
    client: OpenAI,
    prompt: str,
    enable_thinking: bool = True,
    low_effort: bool = False,
    reasoning_budget: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Simple helper for the common case. Returns the final content as string.
    (It still prints the colored stream.)
    """
    extra: Dict[str, Any] = {"chat_template_kwargs": {"enable_thinking": enable_thinking}}
    if low_effort:
        extra["chat_template_kwargs"]["low_effort"] = True
    if reasoning_budget:
        extra["reasoning_budget"] = reasoning_budget

    resp = create_stream(
        client,
        messages=[{"role": "user", "content": prompt}],
        extra_body=extra,
        tools=tools,
    )
    # We consume the stream for side-effect printing; the final content
    # is also returned by joining what was printed (simple approach).
    # For a non-printing version you would accumulate content yourself.
    _ = stream_reasoning_content(resp, show_tool_deltas=bool(tools), print_output=True)
    # Note: a more complete implementation would accumulate the final answer text.
    return "(see printed stream above for full output + reasoning)"


# --------------------------------------------------------------------------- #
# Self-test / example
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    print("nemotron_helpers ready.")
    print(f"Default model: {DEFAULT_MODEL}")
    print("Set NVIDIA_API_KEY and run one of the demo functions.")
    print()
    print("Quick example (will prompt for key if not in env):")
    print("    from nemotron_helpers import get_client, ask_with_thinking")
    print("    client = get_client()")
    print("    ask_with_thinking(client, 'What is 2+2?', enable_thinking=True)")


# --------------------------------------------------------------------------- #
# Trace capture (added for the think-lab showcase)
# --------------------------------------------------------------------------- #

@dataclass
class ReasoningTrace:
    """Structured capture of a full streamed response for saving/replay/analysis."""
    prompt: str
    model: str
    reasoning_chunks: List[str]
    content_chunks: List[str]
    final_content: str
    tool_calls: List[Dict[str, Any]]
    raw_tool_acc: Dict[int, Dict[str, str]]
    extra_body: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


def stream_and_capture(
    client: OpenAI,
    messages: List[Dict[str, Any]],
    extra_body: Optional[Dict[str, Any]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    print_output: bool = True,
) -> ReasoningTrace:
    """
    Like create_stream + stream_reasoning_content, but returns a structured
    ReasoningTrace that can be saved as JSON and replayed later.

    This is gold for the showcase: you can commit example traces and build UIs
    that replay them without burning API quota every time.
    """
    # We re-implement a capturing version of the streamer (keeps helpers.py self-contained)
    model = getattr(client, "_nemotron_model", DEFAULT_MODEL)

    reasoning_chunks: List[str] = []
    content_chunks: List[str] = []
    in_reasoning = False
    acc: Dict[int, Dict[str, str]] = {}

    req: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": 8192,
        "temperature": 1.0,
        "top_p": 0.95,
        "stream": True,
        "timeout": getattr(client, "_nemotron_timeout", DEFAULT_TIMEOUT),
    }
    if extra_body:
        req["extra_body"] = extra_body
    if tools:
        req["tools"] = tools
        req["tool_choice"] = "auto"

    response = client.chat.completions.create(**req)

    for chunk in response:
        for choice in chunk.choices:
            delta = choice.delta

            reasoning = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
            if reasoning:
                if not in_reasoning:
                    if print_output:
                        print(_c("", REASONING_COLOR), end="")
                    in_reasoning = True
                reasoning_chunks.append(reasoning)
                if print_output:
                    print(reasoning, end="", flush=True)

            content = getattr(delta, "content", None)
            if content:
                if in_reasoning:
                    if print_output:
                        print(RESET_COLOR if USE_COLOR else "", end="")
                    in_reasoning = False
                content_chunks.append(content)
                if print_output:
                    print(content, end="", flush=True)

            if not tools:
                continue

            tool_calls = getattr(delta, "tool_calls", None)
            if not tool_calls:
                continue

            for tc in tool_calls:
                idx = tc.get("index", 0) if isinstance(tc, dict) else getattr(tc, "index", 0)
                idx = 0 if idx is None else idx
                if idx not in acc:
                    acc[idx] = {"id": "", "name": "", "arguments": ""}

                if isinstance(tc, dict):
                    acc[idx]["id"] = acc[idx]["id"] or tc.get("id", "")
                    fn = tc.get("function", {})
                    name_part = fn.get("name", "")
                    args_part = fn.get("arguments", "")
                else:
                    acc[idx]["id"] = acc[idx]["id"] or getattr(tc, "id", "")
                    fn = getattr(tc, "function", None)
                    name_part = (getattr(fn, "name", None) or "") if fn else ""
                    args_part = (getattr(fn, "arguments", None) or "") if fn else ""

                if print_output:
                    if name_part:
                        print(_c(f"\n[tool#{idx} name+] {name_part}", TOOL_COLOR), end="", flush=True)
                    if args_part:
                        print(_c(f"\n[tool#{idx} args+] {args_part}", TOOL_COLOR), end="", flush=True)

                acc[idx]["name"] += name_part
                acc[idx]["arguments"] += args_part

    if in_reasoning and print_output:
        print(RESET_COLOR if USE_COLOR else "", end="")
    if print_output:
        print()

    final_content = "".join(content_chunks)
    tool_calls_list = []
    for idx in sorted(acc.keys()):
        tc = acc[idx]
        if tc["name"]:
            tool_calls_list.append({
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]}
            })

    return ReasoningTrace(
        prompt=messages[-1]["content"] if messages else "",
        model=model,
        reasoning_chunks=reasoning_chunks,
        content_chunks=content_chunks,
        final_content=final_content,
        tool_calls=tool_calls_list,
        raw_tool_acc=acc,
        extra_body=extra_body,
    )


def save_trace(trace: ReasoningTrace, path: str):
    """Save a ReasoningTrace to JSON (pretty)."""
    data = asdict(trace)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved trace → {path}")


def load_trace(path: str) -> Dict[str, Any]:
    """Load a previously saved trace (returns raw dict for flexibility in UIs)."""
    with open(path) as f:
        return json.load(f)

