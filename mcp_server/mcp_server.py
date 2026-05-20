import os
import subprocess
import shutil
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Define MCP server named MacMiniManager
mcp = FastMCP("MacMiniManager")

BASE_DIR = "/Users/ai/talk"

def _resolve_path(path: str) -> str:
    """Resolves relative paths to BASE_DIR, keeps absolute paths."""
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(BASE_DIR, path))

@mcp.tool()
def run_command(cmd: str) -> str:
    """Run a terminal command on the Mac Mini within the project directory.

    Args:
        cmd: The shell command to run (e.g. 'git status', 'ls -lh').
    """
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            cwd=BASE_DIR
        )
        output = f"Exit code: {res.returncode}\n"
        if res.stdout:
            output += f"--- STDOUT ---\n{res.stdout}\n"
        if res.stderr:
            output += f"--- STDERR ---\n{res.stderr}\n"
        return output
    except Exception as e:
        return f"Error executing command: {e}"

@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file on the Mac Mini.

    Args:
        path: Path to the file (absolute or relative to project root).
    """
    full_path = _resolve_path(path)
    if not os.path.exists(full_path):
        return f"Error: File not found at {full_path}"
    if os.path.isdir(full_path):
        return f"Error: {full_path} is a directory. Use list_dir instead."
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write or overwrite a file on the Mac Mini.

    Args:
        path: Path to the file (absolute or relative to project root).
        content: The text content to write.
    """
    full_path = _resolve_path(path)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {full_path}"
    except Exception as e:
        return f"Error writing file: {e}"

@mcp.tool()
def list_dir(path: str = ".") -> str:
    """List directory contents on the Mac Mini.

    Args:
        path: Directory path (absolute or relative to project root, default: project root).
    """
    full_path = _resolve_path(path)
    if not os.path.exists(full_path):
        return f"Error: Path not found at {full_path}"
    if not os.path.isdir(full_path):
        return f"Error: {full_path} is a file, not a directory."
    try:
        entries = os.listdir(full_path)
        entries.sort()
        lines = []
        for entry in entries:
            entry_path = os.path.join(full_path, entry)
            is_dir = os.path.isdir(entry_path)
            size = os.path.getsize(entry_path) if not is_dir else 0
            kind = "DIR" if is_dir else "FILE"
            lines.append(f"{kind:<5} {entry:<35} {size:>10} bytes")
        return "\n".join(lines) if lines else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"

@mcp.tool()
def run_pipeline_day(day: str) -> str:
    """Trigger the daily cache worker pipeline for a specific day in the background on the Mac Mini.

    Args:
        day: The target day formatted as YYYY-MM-DD (e.g. '2026-05-10').
    """
    python_bin = os.path.join(BASE_DIR, ".venv", "bin", "python")
    script_path = os.path.join(BASE_DIR, "pipeline", "daily_cache_worker.py")
    log_path = os.path.join(BASE_DIR, "pipeline_run_mcp.log")

    if not os.path.exists(python_bin):
        return f"Error: Python binary not found at {python_bin}"
    if not os.path.exists(script_path):
        return f"Error: Script not found at {script_path}"

    cmd = f"nohup {python_bin} {script_path} --day {day} > {log_path} 2>&1 &"
    try:
        # Run process in background detached
        subprocess.Popen(cmd, shell=True, preexec_fn=os.setpgrp)
        return f"Pipeline started in background for day: {day}.\nLogs are written to: {log_path}"
    except Exception as e:
        return f"Error launching pipeline: {e}"

@mcp.tool()
def get_pipeline_status() -> str:
    """Check the status of any active pipeline processes and return the tail of the log file on the Mac Mini."""
    try:
        # Check active python process running daily_cache_worker
        ps_res = subprocess.run(
            "ps aux | grep daily_cache_worker.py | grep -v grep",
            shell=True,
            text=True,
            capture_output=True
        )
        
        status = "=== Active Pipeline Processes ===\n"
        if ps_res.stdout.strip():
            status += ps_res.stdout + "\n"
        else:
            status += "No active pipeline processes running.\n\n"

        # Check log file
        log_path = os.path.join(BASE_DIR, "pipeline_run_mcp.log")
        if not os.path.exists(log_path):
            log_path = os.path.join(BASE_DIR, "pipeline_run_v5.log") # Fallback to previous log

        if os.path.exists(log_path):
            status += f"=== Log File tail ({os.path.basename(log_path)}) ===\n"
            tail_res = subprocess.run(
                f"tail -n 50 {log_path}",
                shell=True,
                text=True,
                capture_output=True
            )
            status += tail_res.stdout
        else:
            status += "No log file found."
            
        return status
    except Exception as e:
        return f"Error checking pipeline status: {e}"

if __name__ == "__main__":
    mcp.run()
