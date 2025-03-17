from mcp.types import Prompt, PromptArgument, GetPromptResult, PromptMessage, TextContent
from .resources import DOCUMENTATION_SECTIONS

async def list_prompts() -> list[Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        Prompt(
            name="summarize-docs",
            description="Creates a summary of UV documentation sections",
            arguments=[
                PromptArgument(
                    name="section",
                    description="Documentation section to summarize",
                    required=False,
                )
            ],
        )
    ]

async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    The prompt includes documentation sections with optional filtering.
    """
    if name != "summarize-docs":
        raise ValueError(f"Unknown prompt: {name}")

    section = (arguments or {}).get("section")
    sections_to_summarize = [section] if section in DOCUMENTATION_SECTIONS else DOCUMENTATION_SECTIONS

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