"""Entry: `python -m vision_extension` runs the MCP server (no args) or the CLI (with subcommand).

Subcommands: init, presets, config, doctor — see `python -m vision_extension <cmd> --help`.
"""

import sys

CLI_SUBCOMMANDS = {"init", "presets", "config", "doctor", "--version", "--help", "-h"}


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in CLI_SUBCOMMANDS:
        from vision_extension.cli import main as cli_main

        sys.exit(cli_main(sys.argv[1:]))

    from vision_extension.server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
