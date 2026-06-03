"""
VisibleReasoningAgent — the core of the Nemotron Think framework.

Every step the model takes (reasoning, tool planning, observations) is captured
in a structured trace so you can see exactly what the model was "thinking".

Designed specifically to showcase Nemotron 3 Ultra's strengths:
- enable_thinking + reasoning_budget
- Beautiful streamed tool call deltas
- High quality multi-step planning + self-correction
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .helpers import (
    get_client,
    create_stream,
    stream_reasoning_content,
    execute_local_tools,
    ReasoningTrace,
    stream_and_capture,
    save_trace as save_trace_helper,
)
from .tools import Tool, DEFAULT_TOOLS, get_tool_specs, get_tool_map


console = Console()


@dataclass
class AgentStep:
    """One full turn: the model's visible reasoning + any tool use + observation."""
    step: int
    user_message: Optional[str]
    reasoning: str
    content: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    trace: Optional[ReasoningTrace] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AgentRun:
    """Complete record of an agent execution. Serializable for traces, evals, UI."""
    task: str
    model: str
    steps: List[AgentStep] = field(default_factory=list)
    final_answer: str = ""
    total_tool_calls: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())
        console.print(f"[green]Saved full agent trace → {path}[/green]")


class VisibleReasoningAgent:
    """
    A multi-step agent that forces the model to show its work.

    Usage:
        agent = VisibleReasoningAgent(tools=[...])
        run = agent.run("Research the latest open source video models and summarize the top 3", 
                        reasoning_budget=8192)
        print(run.final_answer)
        run.save("my_research.trace.json")
    """

    def __init__(
        self,
        tools: Optional[List[Tool]] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_steps: int = 6,
        default_reasoning_budget: Optional[int] = 4096,
        default_low_effort: bool = False,
    ):
        self.tools = tools or DEFAULT_TOOLS
        self.tool_specs = get_tool_specs(self.tools)
        self.tool_map = get_tool_map(self.tools)
        self.max_steps = max_steps
        self.default_reasoning_budget = default_reasoning_budget
        self.default_low_effort = default_low_effort

        # Only pass explicit values so get_client uses its good defaults (NVIDIA endpoint)
        client_kwargs = {}
        if api_key is not None:
            client_kwargs["api_key"] = api_key
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        if model is not None:
            client_kwargs["model"] = model

        self.client = get_client(**client_kwargs)
        self.model = getattr(self.client, "_nemotron_model", model or "private/nvidia/nemotron-3-ultra-550b-a55b")

    def _build_extra_body(self, reasoning_budget: Optional[int] = None, low_effort: Optional[bool] = None) -> Dict[str, Any]:
        budget = reasoning_budget if reasoning_budget is not None else self.default_reasoning_budget
        le = low_effort if low_effort is not None else self.default_low_effort
        extra: Dict[str, Any] = {"chat_template_kwargs": {"enable_thinking": True}}
        if le:
            extra["chat_template_kwargs"]["low_effort"] = True
        if budget:
            extra["reasoning_budget"] = budget
        return extra

    def run(
        self,
        task: str,
        reasoning_budget: Optional[int] = None,
        low_effort: Optional[bool] = None,
        max_steps: Optional[int] = None,
        save_every_step: bool = False,
        trace_dir: str = "traces",
    ) -> AgentRun:
        """
        Run the agent on a task. Every thought is visible in the live output.
        Returns a rich AgentRun object you can inspect, save, or replay.
        """
        max_steps = max_steps or self.max_steps
        extra = self._build_extra_body(reasoning_budget, low_effort)

        run = AgentRun(
            task=task,
            model=self.model,
            config={
                "reasoning_budget": reasoning_budget or self.default_reasoning_budget,
                "low_effort": low_effort or self.default_low_effort,
                "max_steps": max_steps,
            },
        )

        messages: List[Dict[str, Any]] = [{"role": "user", "content": task}]
        step_num = 0

        console.rule(f"[bold cyan]VisibleReasoningAgent starting[/bold cyan]")
        console.print(Panel(task, title="Task", style="cyan"))

        while step_num < max_steps:
            step_num += 1
            console.rule(f"[bold]Step {step_num}[/bold]")

            # --- Call the model with full thinking + tools enabled ---
            trace = stream_and_capture(
                self.client,
                messages=messages,
                extra_body=extra,
                tools=self.tool_specs,
                print_output=True,
            )

            # Extract what the model "said" and did
            reasoning_text = "".join(trace.reasoning_chunks) if trace.reasoning_chunks else ""
            content_text = trace.final_content or "".join(trace.content_chunks)

            step = AgentStep(
                step=step_num,
                user_message=task if step_num == 1 else None,
                reasoning=reasoning_text,
                content=content_text,
                tool_calls=trace.tool_calls,
                tool_results=[],
                trace=trace,
            )

            # --- If the model decided to use tools, execute them visibly ---
            if trace.tool_calls:
                console.print("\n[bold orange1]Executing tools...[/bold orange1]")
                assistant_tool_calls, tool_results = execute_local_tools(
                    trace.raw_tool_acc,
                    tool_impls=self.tool_map,
                    print_output=True,
                )
                step.tool_results = tool_results

                # Feed results back into the conversation for the next turn
                messages.append({"role": "assistant", "content": None, "tool_calls": assistant_tool_calls})
                messages.extend(tool_results)

                run.total_tool_calls += len(tool_results)
            else:
                # No more tool calls — this is the final answer
                run.final_answer = content_text
                run.steps.append(step)
                break

            run.steps.append(step)

            if save_every_step:
                os.makedirs(trace_dir, exist_ok=True)
                step_path = os.path.join(trace_dir, f"step_{step_num:02d}.json")
                save_trace_helper(trace, step_path)

        if not run.final_answer and run.steps:
            run.final_answer = run.steps[-1].content

        console.rule("[bold green]Agent finished[/bold green]")
        console.print(Panel(run.final_answer[:800] + ("..." if len(run.final_answer) > 800 else ""),
                            title="Final Answer", style="green"))

        return run


def pretty_print_step(step: AgentStep, show_reasoning: bool = True):
    """Utility for nice terminal rendering of a step (used by CLI replay etc)."""
    console.print(f"\n[bold]Step {step.step}[/bold]")
    if step.reasoning and show_reasoning:
        console.print(Panel(step.reasoning[:1200], title="Model Reasoning (visible)", style="green"))
    if step.content:
        console.print(Panel(step.content[:800], title="Model Content", style="white"))
    if step.tool_calls:
        console.print("[orange1]Tool calls made:[/orange1]")
        for tc in step.tool_calls:
            fn = tc.get("function", {})
            console.print(f"  • {fn.get('name')}({fn.get('arguments')})")
    if step.tool_results:
        console.print("[orange1]Observations:[/orange1]")
        for obs in step.tool_results:
            console.print(f"  {obs.get('content', '')[:300]}")
