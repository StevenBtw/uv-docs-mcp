from pydantic import AnyUrl
from mcp.types import Resource

from .cache import cache_manager

DOCUMENTATION_SECTIONS = ["cli", "settings", "resolver", "versioning"]

# Default elements if no cache is available
DEFAULT_SECTION_ELEMENTS = {
    "cli": ["install", "sync", "add", "venv"],
    "settings": ["index-url", "requirements", "python-version"],
    "resolver": ["strategy", "constraints", "conflicts"]
}

async def list_resources() -> list[Resource]:
    """
    List available documentation resources.
    Each section is exposed as a resource with a uv-docs:// URI scheme.
    """
    resources = []
    
    for section in DOCUMENTATION_SECTIONS:
        resources.append(
            Resource(
                uri=AnyUrl(f"uv-docs://{section}"),
                name=f"UV {section.title()} Documentation",
                description=f"Documentation for UV's {section} functionality",
                mimeType="application/json",
            )
        )
    
    return resources

async def read_resource(uri: AnyUrl) -> str:
    """
    Read a specific documentation section's content by its URI.
    Returns cached content if available, falls back to defaults if not cached.
    """
    if uri.scheme != "uv-docs":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    section = uri.host
    if section not in DOCUMENTATION_SECTIONS:
        raise ValueError(f"Unknown documentation section: {section}")

    # Try to get cached content
    cached_content = await cache_manager.get_cached_section(section)
    if cached_content:
        return cached_content

    # Fall back to default content if no cache available
    default_elements = DEFAULT_SECTION_ELEMENTS.get(section, [])
    return {
        "type": "documentation_section",
        "section": section,
        "elements": [
            {
                "name": element,
                "description": f"Documentation for {element}"
            }
            for element in default_elements
        ]
    }