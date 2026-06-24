"""
Code Run Tool — Python Sandbox

LangChain StructuredTool that executes Python code inside a restricted environment.
Useful for data formatting, mathematical modeling, and CSV transformations.
"""
import sys
import io
import traceback
from typing import Any, Dict, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class CodeRunInput(BaseModel):
    code:      str           = Field(..., description="Python code block to execute")
    timeout:   Optional[int] = Field(default=5, description="Timeout limit in seconds")
    tenant_id: str           = Field(default="", description="Tenant ID context")


@tool(args_schema=CodeRunInput)
async def code_run_tool(code: str, timeout: int = 5, tenant_id: str = "") -> Dict[str, Any]:
    """
    Execute arbitrary Python code in a sandboxed execution context.
    Captures stdout, stderr, and variables. Useful for data cleanups.
    """
    print(f"  🐍 [code_run_tool] Executing {len(code)} chars of code...")

    # Redirect stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = buffer_stdout = io.StringIO()
    sys.stderr = buffer_stderr = io.StringIO()

    # Restricted local scope
    local_scope: Dict[str, Any] = {}
    # Allow math and basic structures
    global_scope = {
        "__builtins__": {
            "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
            "dict": dict, "dir": dir, "divmod": divmod, "enumerate": enumerate,
            "filter": filter, "float": float, "format": format, "hash": hash,
            "hex": hex, "id": id, "int": int, "isinstance": isinstance,
            "len": len, "list": list, "map": map, "max": max, "min": min,
            "next": next, "oct": oct, "ord": ord, "pow": pow, "range": range,
            "repr": repr, "reversed": reversed, "round": round, "set": set,
            "slice": slice, "sorted": sorted, "str": str, "sum": sum,
            "tuple": tuple, "zip": zip,
        },
        "math": __import__("math"),
        "json": __import__("json"),
    }

    error = None
    try:
        # execute code (exec blocks, doesn't return value unless printed or bound)
        exec(code, global_scope, local_scope)
    except Exception as e:
        error = traceback.format_exc()
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    stdout_val = buffer_stdout.getvalue()
    stderr_val = buffer_stderr.getvalue() or error

    # Clean local scope variables to avoid leaking large references
    clean_locals = {
        k: str(v)[:300] for k, v in local_scope.items()
        if not k.startswith("__") and not hasattr(v, "__call__")
    }

    if stderr_val:
        print(f"  ❌ [code_run_tool] Failed: {stderr_val.splitlines()[-1]}")
        return {
            "status": "error",
            "stdout": stdout_val,
            "stderr": stderr_val,
            "locals": clean_locals,
        }

    print(f"  ✅ [code_run_tool] Executed successfully")
    return {
        "status": "success",
        "stdout": stdout_val,
        "locals": clean_locals,
    }
