"""Entry: `python -m mcp_eyes` runs the MCP server (no args) or the CLI (with subcommand).

Subcommands: init, presets, config, doctor — see `python -m mcp_eyes <cmd> --help`.
"""

import sys

CLI_SUBCOMMANDS = {"init", "presets", "config", "doctor", "--version", "--help", "-h"}


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in CLI_SUBCOMMANDS:
        from mcp_eyes.cli import main as cli_main

        sys.exit(cli_main(sys.argv[1:]))

    from mcp_eyes.server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
