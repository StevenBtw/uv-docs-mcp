import asyncio

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from .resources import list_resources, read_resource
from .prompts import list_prompts, get_prompt
from .tools import list_tools, call_tool
from .cache import cache_manager

server = Server("uv-docs")

@server.list_resources()
async def handle_list_resources() -> list:
    return await list_resources()

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    return await read_resource(uri)

@server.list_prompts()
async def handle_list_prompts() -> list:
    return await list_prompts()

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None):
    return await get_prompt(name, arguments)

@server.list_tools()
async def handle_list_tools() -> list:
    return await list_tools()

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None):
    return await call_tool(name, arguments, server)

async def main():
    # Initialize cache before starting server
    print("Initializing documentation cache...")
    await cache_manager.initialize()
    
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="uv-docs",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())