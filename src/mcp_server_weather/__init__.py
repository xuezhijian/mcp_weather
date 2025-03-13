from .server import serve


def main():
    """MCP Time Server - Time and timezone conversion functionality for MCP"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to handle weather queries"
    )
    parser.add_argument("--key", type=str, help="和风天气API Key, eg: xxxxx")

    args = parser.parse_args()
    asyncio.run(serve(args.location))


if __name__ == "__main__":
    main()
