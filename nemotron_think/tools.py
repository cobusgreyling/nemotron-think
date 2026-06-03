"""
First-class Tool abstraction + a set of useful default tools for Nemotron 3 Ultra agents.

Tools are defined with:
- name, description, parameters JSON schema (for the model's function calling)
- python callable that executes it

The agent will surface the full reasoning before and after tool use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema for "parameters"
    func: Callable[..., Any]

    def to_openai_spec(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# -----------------------------
# Built-in useful tools
# -----------------------------

def _get_math_answer(expression: str) -> str:
    """Safe arithmetic evaluator. Supports + - * / ( ) and numbers."""
    import re
    expr = re.sub(r"\s+", "", expression)
    if not re.match(r"^[\d+\-*/().]+$", expr):
        return "Error: only numbers and + - * / ( ) allowed"
    try:
        return str(eval(expr))
    except Exception as e:
        return f"Error: {e}"


def _get_current_time() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _python_exec(code: str, timeout: float = 10.0) -> str:
    """
    Execute Python code safely-ish (subprocess + temp file, timeout, basic guard).
    Returns the captured output.
    WARNING: Not a hardened sandbox. Use only for trusted/demo code in controlled environments.
    """
    import subprocess
    import sys
    import tempfile
    import os

    dangerous = ["import os", "import subprocess", "import sys", "__import__", "open(", "socket", "requests.get", "urllib.request"]
    cl = code.lower()
    for d in dangerous:
        if d in cl:
            return f"REFUSED: code contains risky pattern '{d}'. Use a safer approach or ask the user to run it."

    # Write user code to a temp .py file and run it (much more robust for indentation / quotes)
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "agent_code.py")
        with open(script, "w") as f:
            f.write(code)

        try:
            proc = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp,
            )
            out = proc.stdout
            err = proc.stderr
            if proc.returncode != 0 and not out and not err:
                err = f"Process exited with code {proc.returncode}"
            result = (out + "\n" + err).strip()
            return result or "(no output)"
        except subprocess.TimeoutExpired:
            return f"ERROR: timed out after {timeout}s"
        except Exception as e:
            return f"ERROR running code: {e}"


def _web_search(query: str, max_results: int = 6) -> str:
    """Simple web search via DuckDuckGo (no API key). Returns formatted results."""
    import re
    import urllib.parse
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return f"Search error: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for res in soup.select(".result")[:max_results]:
        a = res.select_one(".result__a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if href.startswith("/"):
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                href = urllib.parse.unquote(m.group(1))
        snip = ""
        if (s := res.select_one(".result__snippet")):
            snip = s.get_text(" ", strip=True)
        results.append(f"- {title}\n  {href}\n  {snip[:280]}")

    if not results:
        return f"No good results. Try: https://duckduckgo.com/?q={urllib.parse.quote(query)}"
    return "Search results:\n" + "\n\n".join(results)


# Register the default tools
DEFAULT_TOOLS: List[Tool] = [
    Tool(
        name="get_math_answer",
        description="Returns the exact result of a simple arithmetic expression. Use for any calculation.",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression using + - * / ( )"}},
            "required": ["expression"],
        },
        func=_get_math_answer,
    ),
    Tool(
        name="get_current_time",
        description="Returns current UTC time as ISO string. Useful for time-sensitive tasks.",
        parameters={"type": "object", "properties": {}},
        func=_get_current_time,
    ),
    Tool(
        name="python_exec",
        description="Execute a snippet of Python code and return stdout/stderr. Great for testing algorithms, data processing, or small computations. Do NOT use for network or file system side effects unless intended.",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "number", "description": "Max seconds to allow (default 10)"},
            },
            "required": ["code"],
        },
        func=lambda code, timeout=10.0: _python_exec(code, float(timeout)),
    ),
    Tool(
        name="web_search",
        description="Search the web for current information. Returns titles, links and snippets. Use for research, facts, latest news, libraries, etc.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "How many results (1-10)"},
            },
            "required": ["query"],
        },
        func=lambda query, max_results=6: _web_search(query, int(max_results)),
    ),
]


def get_tool_specs(tools: Optional[List[Tool]] = None) -> List[Dict[str, Any]]:
    tools = tools or DEFAULT_TOOLS
    return [t.to_openai_spec() for t in tools]


def get_tool_map(tools: Optional[List[Tool]] = None) -> Dict[str, Callable]:
    tools = tools or DEFAULT_TOOLS
    return {t.name: t.func for t in tools}


def list_tools(tools: Optional[List[Tool]] = None) -> str:
    tools = tools or DEFAULT_TOOLS
    out = []
    for t in tools:
        params = json.dumps(t.parameters, indent=2)
        out.append(f"• {t.name}\n  {t.description}\n  params: {params}")
    return "\n\n".join(out)
