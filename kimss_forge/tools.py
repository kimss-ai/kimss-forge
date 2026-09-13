"""Tool registration for the local agent loop."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, get_args, get_origin, get_type_hints


def _json_type(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is list or annotation is list:
        return "array"
    if origin is dict or annotation is dict:
        return "object"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation is str or annotation is Any or annotation is inspect.Parameter.empty:
        return "string"
    # Optional[T] / Union
    args = get_args(annotation)
    if args:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _json_type(non_none[0])
    return "string"


@dataclass
class Tool:
    """A callable tool with an OpenAI-compatible function schema."""

    name: str
    description: str
    parameters: Dict[str, Any]
    fn: Callable[..., Any]

    def openai_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def call(self, arguments: Dict[str, Any] | str | None) -> str:
        if arguments is None:
            args: Dict[str, Any] = {}
        elif isinstance(arguments, str):
            try:
                args = json.loads(arguments) if arguments.strip() else {}
            except json.JSONDecodeError:
                args = {"raw": arguments}
        else:
            args = dict(arguments)
        result = self.fn(**args) if args else self.fn()
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result, default=str)
        except TypeError:
            return str(result)


def tool(
    fn: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Any:
    """Decorator (or wrapper) that turns a Python function into a Tool."""

    def _wrap(f: Callable[..., Any]) -> Tool:
        hints = {}
        try:
            hints = get_type_hints(f)
        except Exception:
            hints = getattr(f, "__annotations__", {}) or {}
        sig = inspect.signature(f)
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for pname, param in sig.parameters.items():
            if pname in ("self", "cls"):
                continue
            ann = hints.get(pname, param.annotation)
            properties[pname] = {
                "type": _json_type(ann),
                "description": pname.replace("_", " "),
            }
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        schema = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }
        if required:
            schema["required"] = required
        doc = (description or inspect.getdoc(f) or f.__name__).strip()
        return Tool(
            name=(name or f.__name__).strip(),
            description=doc.split("\n")[0].strip(),
            parameters=schema,
            fn=f,
        )

    if fn is not None:
        return _wrap(fn)
    return _wrap


def coerce_tools(tools: Optional[List[Any]]) -> List[Tool]:
    """Normalize a list of Tool instances or @tool-decorated callables."""
    out: List[Tool] = []
    for t in tools or []:
        if isinstance(t, Tool):
            out.append(t)
        elif callable(t):
            out.append(tool(t))
        else:
            raise TypeError(f"Unsupported tool type: {type(t)!r}")
    return out
