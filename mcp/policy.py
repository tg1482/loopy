from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomli as tomllib


@dataclass(frozen=True)
class ShellPolicy:
    root_dir: Path
    timeout_ms: int
    max_output_bytes: int
    allow_commands: set[str]
    deny_commands: set[str]
    env_allowlist: set[str]


def _load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _parse_commands(config: dict, key: str) -> set[str]:
    value = config.get(key, {})
    commands = value.get("commands", [])
    return {str(cmd).strip() for cmd in commands if str(cmd).strip()}


def _parse_env_allowlist(config: dict) -> set[str]:
    env_config = config.get("env", {})
    allowlist = env_config.get("allowlist", [])
    return {str(name).strip() for name in allowlist if str(name).strip()}


def _resolve_root_dir(raw: str | None, base_dir: Path) -> Path:
    if not raw:
        return base_dir.resolve()
    root = Path(raw)
    if not root.is_absolute():
        root = (base_dir / root).resolve()
    return root


def load_policy(path: Path | None) -> ShellPolicy:
    if path is None:
        env_path = os.environ.get("LOOPY_MCP_POLICY")
        path = Path(env_path) if env_path else Path.cwd() / "loopy-shell.policy.toml"

    if not path.exists():
        raise FileNotFoundError(f"policy file not found: {path}")

    config = _load_toml(path)
    root_dir = _resolve_root_dir(config.get("root_dir"), path.parent)
    timeout_ms = int(config.get("timeout_ms", 120000))
    max_output_bytes = int(config.get("max_output_bytes", 50000))

    allow_commands = _parse_commands(config, "allow")
    deny_commands = _parse_commands(config, "deny")
    env_allowlist = _parse_env_allowlist(config)

    if not allow_commands:
        raise ValueError("policy must define allow.commands")

    return ShellPolicy(
        root_dir=root_dir,
        timeout_ms=timeout_ms,
        max_output_bytes=max_output_bytes,
        allow_commands=allow_commands,
        deny_commands=deny_commands,
        env_allowlist=env_allowlist,
    )
