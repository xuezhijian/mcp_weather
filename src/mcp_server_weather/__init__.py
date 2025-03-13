from .server import serve


def main():
    """MCP Time Server - Time and timezone conversion functionality for MCP"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to handle weather queries"
    )
    parser.add_argument("--location", type=str, help="Location, eg: 广州 天河")

    args = parser.parse_args()
    asyncio.run(serve(args.location))


if __name__ == "__main__":
    main()
