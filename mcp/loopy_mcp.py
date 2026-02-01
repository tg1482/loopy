from __future__ import annotations

import argparse
from pathlib import Path

from policy import load_policy
from server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Loopy MCP shell server")
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="Path to policy TOML (defaults to $LOOPY_MCP_POLICY or ./loopy-shell.policy.toml)",
    )
    args = parser.parse_args()

    policy = load_policy(args.policy)
    mcp = create_server(policy)
    mcp.run()


if __name__ == "__main__":
    main()
