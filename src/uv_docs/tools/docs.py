from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server import Server
from ..cache import cache_manager

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
                        "enum": ["cli", "settings", "resolver"],
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

    # Get cached documentation for the section
    section_docs = await cache_manager.get_cached_section(section)
    
    if not section_docs or "elements" not in section_docs:
        return [
            TextContent(
                type="text",
                text=f"No documentation found for section: {section}",
            )
        ]

    # Find the requested element
    element_doc = next(
        (e for e in section_docs["elements"] if e["name"].lower() == element.lower()),
        None
    )

    if not element_doc:
        return [
            TextContent(
                type="text",
                text=f"No documentation found for element '{element}' in section '{section}'",
            )
        ]

    # Format documentation content
    content = [f"# {element_doc['name']}\n"]
    content.append(f"{element_doc['description']}\n")

    for section in element_doc["documentation"]:
        content.append(f"\n## {section['title']}")
        content.extend([f"\n{line}" for line in section["content"]])

    return [TextContent(type="text", text="\n".join(content))]