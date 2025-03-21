from difflib import get_close_matches
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server import Server
from .cache import cache_manager

async def list_tools() -> list[Tool]:
    """
    List all available tools.
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
        ),
        Tool(
            name="search-documentation",
            description="Search UV documentation using fuzzy matching to find the 3 best matching resources",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"],
            },
        )
    ]

async def call_tool(
    name: str, 
    arguments: dict | None,
    server: Server
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    Handle all tool execution requests.
    """
    if name == "update-cache":
        force_update = (arguments or {}).get("force", False)
        try:
            if not force_update and await cache_manager.is_cache_valid():
                return [
                    TextContent(
                        type="text",
                        text="Cache is up to date with current UV version",
                    )
                ]

            version_info = await cache_manager.fetch_current_version()
            
            sections = {
                "cli": cache_manager.fetch_cli_documentation,
                "settings": cache_manager.fetch_settings_documentation,
                "resolver": cache_manager.fetch_resolver_documentation
            }
            
            await cache_manager.update_version(version_info)
            
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
            
    elif name == "search-documentation":
        if not arguments or "query" not in arguments:
            raise ValueError("Missing required argument: query")

        def calculate_relevance(resource: dict, keywords: list[str]) -> float:
            """Calculate relevance score based on exact and fuzzy matches."""
            score = 0.0
            search_text = resource["search_text"].lower()
            section = resource["section"]
            name = resource["name"].lower()
            
            # First pass: Check if any keywords match the section or name exactly
            for keyword in keywords:
                # Highest priority: exact section match
                if keyword == section:
                    score += 3.0
                elif keyword in section:
                    score += 2.0
                
                # High priority: command/setting name match
                if keyword == name:
                    score += 2.0
                elif keyword in name:
                    score += 1.0
            
            # Second pass: Look for keyword matches in description and content
            for keyword in keywords:
                # Check for matches at word boundaries
                if f" {keyword} " in f" {search_text} ":
                    score += 0.75
                # Check for general content matches
                elif keyword in search_text:
                    score += 0.5
            
            # Third pass: Add fuzzy matching for non-exact matches
            if score < 1.0:  # Only do fuzzy matching if we haven't found good matches
                for keyword in keywords:
                    matches = get_close_matches(keyword, [name, section], n=1, cutoff=0.6)
                    if matches:
                        score += 0.25
            
            return score

        query = arguments["query"]
        all_resources = []
        sections = ["cli", "settings", "resolver"]

        # Collect all resources and their paths
        for section in sections:
            section_data = await cache_manager.get_cached_section(section)
            if "elements" in section_data:
                for element in section_data["elements"]:
                    name = element["name"]
                    description = element["description"]
                    # Get all subsection titles
                    subsections = []
                    if "documentation" in element:
                        for doc in element["documentation"]:
                            if "title" in doc and doc["title"] not in ["General", "Options"]:
                                subsections.append(doc["title"])
                    
                    subsection_text = ", ".join(subsections)
                    resource_path = f"uv-docs://{section}/{name.lower()}"
                    
                    # Include content from documentation sections
                    content_text = ""
                    if "documentation" in element:
                        for doc in element["documentation"]:
                            if "content" in doc:
                                # Join content items but limit length to avoid overwhelming matches
                                content = " ".join(str(item) for item in doc["content"][:3])
                                content_text += " " + content
                    
                    search_text = f"{name} {description} {subsection_text} {content_text}"
                    
                    all_resources.append({
                        "path": resource_path,
                        "name": name,
                        "description": description,
                        "search_text": search_text,
                        "section": section,
                        # Store original text for better relevance calculation
                        "content": content_text
                    })

        # Split query into keywords and normalize
        keywords = [k.lower() for k in query.split()]

        # Calculate relevance scores for all resources
        results = []
        for resource in all_resources:
            if (score := calculate_relevance(resource, keywords)) > 0.25:
                results.append((
                    score,
                    f"Resource: {resource['path']}\nName: {resource['name']}\nDescription: {resource['description']}"
                ))

        # Sort by relevance score and take top 3
        results.sort(reverse=True)
        top_results = results[:3] if results else []

        if not top_results:
            return [TextContent(type="text", text="No matching resources found.")]

        formatted_results = [result[1] for result in top_results]
        return [TextContent(type="text", text="Best matching resources:\n\n" + "\n\n".join(formatted_results))]

        
    else:
        raise ValueError(f"Unknown tool: {name}")