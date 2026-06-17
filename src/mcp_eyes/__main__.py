"""Entry point: dispatch between server and init subcommand."""

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        from mcp_eyes.init_template import main as init_main

        sys.exit(init_main(sys.argv[2:]))
    from mcp_eyes.server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
