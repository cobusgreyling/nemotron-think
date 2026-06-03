"""
nemotron-think CLI — the main user interface for the Visible Reasoning Agent Framework.

Install with: pip install -e .
Then:
    nemotron-think --help
    nemotron-think run "your task here" --budget 8192 --save-trace traces/my_run.json
    nemotron-think tools
    nemotron-think replay traces/my_run.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .agent import VisibleReasoningAgent, AgentRun, pretty_print_step
from .tools import DEFAULT_TOOLS, list_tools

console = Console()


def cmd_run(args):
    agent = VisibleReasoningAgent(
        max_steps=args.max_steps,
        default_reasoning_budget=args.budget,
        default_low_effort=args.low_effort,
    )

    run: AgentRun = agent.run(
        task=args.task,
        reasoning_budget=args.budget,
        low_effort=args.low_effort,
        max_steps=args.max_steps,
        save_every_step=args.save_every,
    )

    if args.save_trace:
        run.save(args.save_trace)
    else:
        # Always save a default trace for the user
        default_path = f"traces/{args.task[:40].replace(' ', '_').replace('/', '_')}.json"
        Path("traces").mkdir(exist_ok=True)
        run.save(default_path)

    console.print("\n[bold]Run summary[/bold]")
    console.print(f"  Steps: {len(run.steps)}")
    console.print(f"  Tool calls: {run.total_tool_calls}")
    console.print(f"  Model: {run.model}")


def cmd_tools(_args):
    console.print("[bold cyan]Available tools (pluggable)[/bold cyan]\n")
    console.print(list_tools())


def cmd_replay(args):
    path = Path(args.trace)
    if not path.exists():
        console.print(f"[red]Trace not found: {path}[/red]")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    console.rule(f"Replaying trace: {path}")
    console.print(f"Task: {data.get('task')}")
    console.print(f"Model: {data.get('model')}")

    for step_data in data.get("steps", []):
        # Reconstruct minimal AgentStep for display
        from .agent import AgentStep
        step = AgentStep(
            step=step_data["step"],
            user_message=step_data.get("user_message"),
            reasoning=step_data.get("reasoning", ""),
            content=step_data.get("content", ""),
            tool_calls=step_data.get("tool_calls", []),
            tool_results=step_data.get("tool_results", []),
        )
        pretty_print_step(step, show_reasoning=not args.no_reasoning)

    if data.get("final_answer"):
        console.rule("Final Answer")
        console.print(data["final_answer"])


def cmd_list_runs(_args):
    traces_dir = Path("traces")
    if not traces_dir.exists():
        console.print("No traces directory yet.")
        return
    table = Table(title="Saved Agent Runs")
    table.add_column("File")
    table.add_column("Task (truncated)")
    table.add_column("Steps")
    table.add_column("Tools")

    for f in sorted(traces_dir.glob("*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            task = (d.get("task") or "")[:50]
            table.add_row(str(f), task, str(len(d.get("steps", []))), str(d.get("total_tool_calls", 0)))
        except Exception:
            table.add_row(str(f), "(corrupt)", "-", "-")
    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        prog="nemotron-think",
        description="Visible Reasoning Agent Framework powered by NVIDIA Nemotron 3 Ultra. Every thought is visible."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # run
    p_run = sub.add_parser("run", help="Run the visible reasoning agent on a task")
    p_run.add_argument("task", help="The task / question for the agent")
    p_run.add_argument("--budget", type=int, default=4096, help="reasoning_budget (tokens the model can think)")
    p_run.add_argument("--low-effort", action="store_true", help="Use low_effort mode (faster, cheaper)")
    p_run.add_argument("--max-steps", type=int, default=6, help="Maximum agent turns")
    p_run.add_argument("--save-trace", help="Explicit path to save the full AgentRun JSON")
    p_run.add_argument("--save-every", action="store_true", help="Also save individual step traces")
    p_run.set_defaults(func=cmd_run)

    # tools
    p_tools = sub.add_parser("tools", help="List available tools the agent can use")
    p_tools.set_defaults(func=cmd_tools)

    # replay
    p_replay = sub.add_parser("replay", help="Replay a previously saved agent trace (great for demos)")
    p_replay.add_argument("trace", help="Path to .json trace file")
    p_replay.add_argument("--no-reasoning", action="store_true", help="Hide the internal reasoning parts")
    p_replay.set_defaults(func=cmd_replay)

    # list
    p_list = sub.add_parser("list", help="List saved traces in ./traces/")
    p_list.set_defaults(func=cmd_list_runs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
