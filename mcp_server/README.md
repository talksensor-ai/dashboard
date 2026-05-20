# Mac Mini Control MCP Server

A Model Context Protocol (MCP) server written in Python using FastMCP. It allows an AI coding assistant (like Claude Desktop, Cline, or Antigravity) running locally on your laptop or PC to securely manage files, run commands, and control the pipeline on the remote Mac Mini over SSH.

## Features / Tools Exposed

- **`run_command(cmd: str)`**: Run any terminal command inside `/Users/ai/talk` on the Mac Mini.
- **`read_file(path: str)`**: Read contents of a file on the Mac Mini.
- **`write_file(path: str, content: str)`**: Write or overwrite a file on the Mac Mini.
- **`list_dir(path: str)`**: List files and directories on the Mac Mini.
- **`run_pipeline_day(day: str)`**: Trigger the `daily_cache_worker.py` pipeline for a specific day in the background on the Mac Mini.
- **`get_pipeline_status()`**: Check status of active pipeline processes and see the tail of the logs.

---

## How to Configure in Your Local Client

To use this server, add it to your local MCP config file (e.g., `claude_desktop_config.json` or Cline settings). 

### Configuration JSON Block

```json
{
  "mcpServers": {
    "mac-mini-manager": {
      "command": "ssh",
      "args": [
        "ai@100.123.93.21",
        "/Users/ai/talk/.venv/bin/python",
        "/Users/ai/talk/mcp_server/mcp_server.py",
        "run"
      ]
    }
  }
}
```

### Requirements on Mac Mini
1. Tailscale or VPN connection must be active (IP `100.123.93.21` reachable).
2. SSH keys configured so that `ssh ai@100.123.93.21` connects automatically without asking for a password in the terminal.
3. The virtual environment `.venv` with `mcp` SDK installed.
