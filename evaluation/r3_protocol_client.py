"""Deliver unfiltered test calls through the actual MCP protocol server."""
import asyncio

from mcp.shared.memory import create_connected_server_and_client_session
from mcp_surface.server import create_mcp_server


def protocol_call(surface, tool, arguments):
    async def invoke():
        async with create_connected_server_and_client_session(create_mcp_server(surface)) as session:
            response = await session.call_tool(tool, arguments)
            if response.structuredContent is None:
                raise RuntimeError("MCP protocol did not return structured control-plane response")
            return response.structuredContent
    return asyncio.run(invoke())
