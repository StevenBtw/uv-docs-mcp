from .cache import list_cache_tools, call_cache_tool
from .docs import list_doc_tools, call_doc_tool
from .search import list_search_tools, call_search_tool

async def list_all_tools():
    """Combine tool listings from all modules."""
    cache_tools = await list_cache_tools()
    doc_tools = await list_doc_tools()
    search_tools = await list_search_tools()
    
    return [
        *cache_tools,
        *doc_tools,
        *search_tools
    ]

async def call_tool(name: str, arguments: dict | None, server):
    """Route tool calls to appropriate handler."""
    if name == "update-cache":
        return await call_cache_tool(name, arguments, server)
    elif name in ["get-documentation"]:
        return await call_doc_tool(name, arguments, server)
    elif name in ["search-documentation"]:
        return await call_search_tool(name, arguments, server)
    else:
        raise ValueError(f"Unknown tool: {name}")