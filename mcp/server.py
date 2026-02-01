from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess

from mcp.server.mcpserver import MCPServer

from policy import ShellPolicy


@dataclass(frozen=True)
class ShellResult:
    stdout: str
    stderr: str
    exit_code: int
    truncated_stdout: bool
    truncated_stderr: bool


def _command_name(tokens: list[str]) -> str:
    if not tokens:
        raise ValueError("empty command")
    return Path(tokens[0]).name


def _ensure_allowed(policy: ShellPolicy, name: str) -> None:
    if name in policy.deny_commands:
        raise ValueError(f"command denied: {name}")
    if name not in policy.allow_commands:
        raise ValueError(f"command not allowed: {name}")


def _resolve_cwd(policy: ShellPolicy, cwd: str | None) -> Path:
    base = policy.root_dir
    if cwd:
        candidate = Path(cwd)
        if not candidate.is_absolute():
            candidate = base / candidate
        base = candidate
    resolved = base.resolve()
    if not resolved.is_dir():
        raise ValueError(f"cwd is not a directory: {resolved}")
    if not resolved.is_relative_to(policy.root_dir):
        raise ValueError(f"cwd is outside root_dir: {resolved}")
    return resolved


def _build_env(policy: ShellPolicy, extra: dict[str, str] | None) -> dict[str, str]:
    env = {
        name: value
        for name, value in os.environ.items()
        if name in policy.env_allowlist
    }
    if not extra:
        return env

    for name in extra:
        if name not in policy.env_allowlist:
            raise ValueError(f"env var not allowed: {name}")
    env.update({name: str(value) for name, value in extra.items()})
    return env


def _truncate(text: str, max_bytes: int) -> tuple[str, bool]:
    if max_bytes <= 0:
        return "", True
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text, False
    return data[:max_bytes].decode("utf-8", errors="ignore"), True


def _run_command(
    policy: ShellPolicy,
    cmd: str,
    cwd: str | None,
    env: dict[str, str] | None,
    timeout_ms: int | None,
) -> ShellResult:
    tokens = shlex.split(cmd)
    name = _command_name(tokens)
    _ensure_allowed(policy, name)

    resolved_cwd = _resolve_cwd(policy, cwd)
    resolved_env = _build_env(policy, env)

    timeout = policy.timeout_ms / 1000
    if timeout_ms is not None:
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        timeout = min(timeout_ms / 1000, timeout)

    result = subprocess.run(
        tokens,
        cwd=resolved_cwd,
        env=resolved_env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )

    stdout, truncated_stdout = _truncate(result.stdout, policy.max_output_bytes)
    stderr, truncated_stderr = _truncate(result.stderr, policy.max_output_bytes)

    return ShellResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=result.returncode,
        truncated_stdout=truncated_stdout,
        truncated_stderr=truncated_stderr,
    )


def create_server(policy: ShellPolicy) -> MCPServer:
    mcp = MCPServer("loopy-shell")

    @mcp.tool()
    def shell_run(
        cmd: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_ms: int | None = None,
    ) -> ShellResult:
        return _run_command(policy, cmd, cwd, env, timeout_ms)

    return mcp
