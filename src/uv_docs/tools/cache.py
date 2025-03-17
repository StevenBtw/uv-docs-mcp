from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server import Server

from ..cache import cache_manager

async def list_cache_tools() -> list[Tool]:
    """
    List available cache-related tools.
    """
    return [
        Tool(
            name="update-cache",
            description="Update documentation cache if version has changed",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Force cache update regardless of version",
                        "default": False
                    }
                },
                "required": []
            },
        )
    ]

async def call_cache_tool(
    name: str, 
    arguments: dict | None,
    server: Server
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    Handle cache-related tool execution requests.
    """
    if name != "update-cache":
        raise ValueError(f"Unknown cache tool: {name}")

    force_update = (arguments or {}).get("force", False)
    
    try:
        # Check if cache needs updating
        if not force_update and await cache_manager.is_cache_valid():
            return [
                TextContent(
                    type="text",
                    text="Cache is up to date with current UV version",
                )
            ]

        # Fetch current version and all documentation sections
        version_info = await cache_manager.fetch_current_version()
        
        sections = {
            "cli": cache_manager.fetch_cli_documentation,
            "settings": cache_manager.fetch_settings_documentation,
            "resolver": cache_manager.fetch_resolver_documentation
        }
        
        # Update version first
        await cache_manager.update_version(version_info)
        
        # Update each section
        update_results = []
        for section, fetch_func in sections.items():
            try:
                section_docs = await fetch_func()
                await cache_manager.update_section(section, section_docs)
                update_results.append(
                    f"- {section.title()}: {len(section_docs.get('elements', []))} elements cached"
                )
            except Exception as e:
                update_results.append(f"- {section.title()}: Failed to update ({str(e)})")
        
        return [
            TextContent(
                type="text",
                text=(
                    f"Cache updated successfully:\n"
                    f"- UV Version: {version_info['version']}\n"
                    f"{chr(10).join(update_results)}"
                ),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Failed to update cache: {str(e)}",
            )
        ]