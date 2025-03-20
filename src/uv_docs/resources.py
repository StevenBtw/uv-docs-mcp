import json
from pydantic import AnyUrl
from mcp.types import Resource
from .cache import cache_manager

DOCUMENTATION_SECTIONS = ["cli", "settings", "resolver"]

async def list_resources() -> list[Resource]:
    """List all available documentation sections and their nested resources."""
    resources = []
    
    # Get base sections
    for section in DOCUMENTATION_SECTIONS:
        resources.append(
            Resource(
                uri=AnyUrl(f"uv-docs://{section}"),
                name=f"UV {section.title()} Documentation",
                description=f"Documentation for UV's {section} functionality",
                mimeType="application/json; charset=utf-8",
            )
        )
        
        # Add commands and their subsections as resources
        cached_content = await cache_manager.get_cached_section(section)
        if cached_content and "elements" in cached_content:
            for element in cached_content["elements"]:
                cmd_uri = element["name"].lower().replace(" ", "-")
                resources.append(
                    Resource(
                        uri=AnyUrl(f"uv-docs://{section}/{cmd_uri}"),
                        name=element["name"],
                        description=element["description"],
                        mimeType="application/json; charset=utf-8",
                    )
                )
                
                # Add command subsections as resources
                if "documentation" in element:
                    for doc_section in element["documentation"]:
                        section_uri = doc_section["title"].lower().replace(" ", "-")
                        resources.append(
                            Resource(
                                uri=AnyUrl(f"uv-docs://{section}/{cmd_uri}/{section_uri}"),
                                name=f"{element['name']} - {doc_section['title']}",
                                description=f"{doc_section['title']} documentation for {element['name']}",
                                mimeType="application/json; charset=utf-8",
                            )
                        )
    
    return resources

async def read_resource(uri: AnyUrl) -> str:
    """Retrieve documentation dynamically from cache, supporting hierarchical lookups."""
    if uri.scheme != "uv-docs":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    # Parse the path parts
    parts = uri.host.split("/") if uri.host else []
    if uri.path and uri.path != "/":
        parts.extend(p for p in uri.path[1:].split("/") if p)

    if not parts:
        raise ValueError("Invalid resource path")

    section = parts[0]
    cached_content = await cache_manager.get_cached_section(section)
    if not cached_content:
        raise FileNotFoundError(f"Cache for '{section}' not found or empty.")

    # Level 1: Base section - return list of commands
    if len(parts) == 1:
        return json.dumps({
            "type": "section",
            "name": section,
            "commands": [
                {
                    "name": el["name"],
                    "description": el["description"],
                    "uri": f"uv-docs://{section}/{el['name'].lower().replace(' ', '-')}"
                }
                for el in cached_content.get("elements", [])
            ]
        }, indent=2)

    # Level 2/3: Command-specific documentation
    cmd_name = parts[1].replace("-", " ")
    if section == "cli":
        if not cmd_name.startswith("uv "):
            cmd_name = f"uv {cmd_name}"

    # Find the requested command
    command = None
    for element in cached_content.get("elements", []):
        if element["name"].lower() == cmd_name.lower():
            command = element
            break

    if not command:
        raise ValueError(f"Command '{cmd_name}' not found")

    # Level 2: Return command metadata and available sections
    if len(parts) == 2:
        return json.dumps({
            "type": "command",
            "name": command["name"],
            "description": command["description"],
            "sections": [
                {
                    "title": section["title"],
                    "uri": f"uv-docs://{parts[0]}/{parts[1]}/{section['title'].lower().replace(' ', '-')}"
                }
                for section in command.get("documentation", [])
            ]
        }, indent=2)

    # Level 3: Return specific section of command documentation
    subsection = parts[2].replace("-", " ")
    for doc_section in command.get("documentation", []):
        if doc_section["title"].lower() == subsection.lower():
            return json.dumps({
                "type": "section",
                "command": command["name"],
                "section": doc_section["title"],
                "content": doc_section.get("content", [])
            }, indent=2)

    raise ValueError(f"Section '{subsection}' not found in command '{cmd_name}'")
