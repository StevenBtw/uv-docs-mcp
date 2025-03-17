from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server import Server

async def list_doc_tools() -> list[Tool]:
    """
    List available documentation-related tools.
    """
    return [
        Tool(
            name="get-documentation",
            description="Get full documentation for a specific UV documentation element",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": ["cli", "settings", "resolver", "versioning"],
                        "description": "Documentation section"
                    },
                    "element": {
                        "type": "string",
                        "description": "Documentation element within the section"
                    }
                },
                "required": ["section", "element"],
            },
        )
    ]

async def call_doc_tool(
    name: str, 
    arguments: dict | None,
    server: Server
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    Handle documentation-related tool execution requests.
    """
    if name != "get-documentation":
        raise ValueError(f"Unknown documentation tool: {name}")

    if not arguments or "section" not in arguments or "element" not in arguments:
        raise ValueError("Missing required arguments: section and element")

    section = arguments["section"]
    element = arguments["element"]

    # Placeholder: In real implementation, this would fetch documentation content
    return [
        TextContent(
            type="text",
            text=f"Documentation for {section} element '{element}' would be returned here",
        )
    ]