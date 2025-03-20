from mcp.types import Prompt, PromptArgument, GetPromptResult, PromptMessage, TextContent
from .cache import cache_manager  # Use cache for dynamic section retrieval


async def list_prompts() -> list[Prompt]:
    """
    List available prompts.
    """
    return [
        Prompt(
            name="summarize-docs",
            description="Creates a summary of UV documentation sections",
            arguments=[
                PromptArgument(
                    name="section",
                    description="Documentation section to summarize (e.g., 'cli', 'settings', 'resolver')",
                    required=False,
                )
            ],
        ),
        Prompt(
            name="best-doc-source",
            description="Helps determine the best documentation section to use",
            arguments=[
                PromptArgument(
                    name="query",
                    description="A short query describing the needed information",
                    required=True,
                )
            ],
        ),
        Prompt(
            name="reformat-docs",
            description="Reformats documentation for clarity (e.g., step-by-step, bullet points)",
            arguments=[
                PromptArgument(
                    name="section",
                    description="Documentation section to format",
                    required=True,
                )
            ],
        ),
    ]


async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    """
    if name == "summarize-docs":
        return await handle_summarize_docs(arguments)

    if name == "best-doc-source":
        return await handle_best_doc_source(arguments)

    if name == "reformat-docs":
        return await handle_reformat_docs(arguments)

    raise ValueError(f"Unknown prompt: {name}")


async def handle_summarize_docs(arguments: dict[str, str] | None) -> GetPromptResult:
    """Handles the summarize-docs prompt."""
    # Get available sections dynamically
    sections = list((await cache_manager.get_cached_version()).keys()) or ["cli", "settings", "resolver"]

    section = (arguments or {}).get("section")
    sections_to_summarize = [section] if section in sections else sections

    return GetPromptResult(
        description="Summarize UV documentation sections",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Please summarize the following UV documentation sections: {', '.join(sections_to_summarize)}\n\n"
                    "Sections available:\n" +
                    "\n".join(f"- {section}" for section in sections_to_summarize)
                ),
            )
        ],
    )


async def handle_best_doc_source(arguments: dict[str, str] | None) -> GetPromptResult:
    """Handles best-doc-source prompt, helping the LLM determine where to look for info."""
    query = arguments.get("query", "").strip()

    if not query:
        raise ValueError("Query argument is required for best-doc-source prompt.")

    sections = list((await cache_manager.get_cached_version()).keys()) or ["cli", "settings", "resolver"]

    return GetPromptResult(
        description="Determine the best documentation source",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Based on the following query: '{query}', please determine the best UV documentation section to refer to.\n\n"
                    "Available sections:\n" +
                    "\n".join(f"- {section}" for section in sections)
                ),
            )
        ],
    )


async def handle_reformat_docs(arguments: dict[str, str] | None) -> GetPromptResult:
    """Handles reformat-docs prompt, providing structured output for better readability."""
    section = arguments.get("section", "").strip()

    if not section:
        raise ValueError("Section argument is required for reformat-docs prompt.")

    return GetPromptResult(
        description="Reformat UV documentation for clarity",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Please reformat the documentation for '{section}' to make it more structured and readable. "
                    "Convert long paragraphs into bullet points or step-by-step instructions if applicable."
                ),
            )
        ],
    )
