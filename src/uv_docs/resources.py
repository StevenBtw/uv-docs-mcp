import json
from pydantic import AnyUrl
from mcp.types import Resource

from .cache import cache_manager

# Top-level documentation sections
DOCUMENTATION_SECTIONS = ["cli", "settings", "resolver"]

# Default elements for each section
DEFAULT_SECTION_ELEMENTS = {
    "cli": [
        "uv",
        "uv-run",
        "uv-init",
        "uv-add",
        "uv-remove",
        "uv-sync",
        "uv-lock",
        "uv-export",
        "uv-tree",
        "uv-tool",
        "uv-python",
        "uv-pip",
        "uv-venv",
        "uv-build",
        "uv-publish",
        "uv-cache",
        "uv-self",
        "uv-version",
        "uv-generate-shell-completion",
        "uv-pip-show",
        "uv-pip-tree", 
        "uv-pip-check",
        "uv-cache-clean",
        "uv-cache-prune",
        "uv-cache-dir",
        "uv-self-update",
        "uv-help"
    ],
    "settings": [
        "build-constraint-dependencies",
        "conflicts",
        "constraint-dependencies",
        "default-groups",
        "dev-dependencies",
        "environments",
        "index",
        "managed",
        "override-dependencies",
        "package",
        "required-environments",
        "sources",
        "workspace",
        "exclude",
        "members",
        "allow-insecure-host",
        "cache-dir",
        "cache-keys",
        "check-url",
        "compile-bytecode",
        "concurrent-builds",
        "concurrent-downloads",
        "concurrent-installs",
        "config-settings",
        "dependency-metadata",
        "exclude-newer",
        "extra-index-url",
        "find-links",
        "fork-strategy",
        "index",
        "index-strategy",
        "index-url",
        "keyring-provider",
        "link-mode",
        "native-tls",
        "no-binary",
        "no-binary-package",
        "no-build",
        "no-build-isolation",
        "no-build-isolation-package",
        "no-build-package",
        "no-cache",
        "no-index",
        "no-sources",
        "offline",
        "prerelease",
        "preview",
        "publish-url",
        "pypy-install-mirror",
        "python-downloads",
        "python-install-mirror",
        "python-preference",
        "reinstall",
        "reinstall-package",
        "required-version",
        "resolution",
        "trusted-publishing",
        "upgrade",
        "upgrade-package",
        "pip",
        "pip-all-extras",
        "pip-allow-empty-requirements",
        "pip-annotation-style",
        "pip-break-system-packages",
        "pip-compile-bytecode",
        "pip-config-settings",
        "pip-custom-compile-command",
        "pip-dependency-metadata",
        "pip-emit-build-options",
        "pip-emit-find-links",
        "pip-emit-index-annotation",
        "pip-emit-index-url",
        "pip-emit-marker-expression",
        "pip-exclude-newer",
        "pip-extra",
        "pip-extra-index-url",
        "pip-find-links",
        "pip-fork-strategy",
        "pip-generate-hashes",
        "pip-group",
        "pip-index-strategy",
        "pip-index-url",
        "pip-keyring-provider",
        "pip-link-mode",
        "pip-no-annotate",
        "pip-no-binary",
        "pip-no-build",
        "pip-no-build-isolation",
        "pip-no-build-isolation-package",
        "pip-no-deps",
        "pip-no-emit-package",
        "pip-no-extra",
        "pip-no-header",
        "pip-no-index",
        "pip-no-sources",
        "pip-no-strip-extras",
        "pip-no-strip-markers",
        "pip-only-binary",
        "pip-output-file",
        "pip-prefix",
        "pip-prerelease",
        "pip-python",
        "pip-python-platform",
        "pip-python-version",
        "pip-reinstall",
        "pip-reinstall-package",
        "pip-require-hashes",
        "pip-resolution",
        "pip-strict",
        "pip-system",
        "pip-target",
        "pip-universal",
        "pip-upgrade",
        "pip-upgrade-package",
        "pip-verify-hashes"
    ],
    "resolver": [
        "resolver",
        "forking",
        "wheel-tags",
        "marker-and-wheel-tag-filtering",
        "requires-python",
        "prioritization"
    ]
}

async def list_resources() -> list[Resource]:
    """List available documentation resources."""
    resources = []
    for section in DOCUMENTATION_SECTIONS:
        resource = Resource(
            uri=AnyUrl(f"uv-docs://{section}"),
            name=f"UV {section.title()} Documentation",
            description=f"Documentation for UV's {section} functionality",
            mimeType="application/json; charset=utf-8",
        )
        resources.append(resource)
    return resources

async def read_resource(uri: AnyUrl) -> str:
    """Read a documentation section by its URI."""
    if uri.scheme != "uv-docs":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    section = uri.host
    if section not in DOCUMENTATION_SECTIONS:
        raise ValueError(f"Unknown documentation section: {section}")

    # Return cached content if available
    cached_content = await cache_manager.get_cached_section(section)
    if cached_content:
        return json.dumps(cached_content, indent=2)

    # Fall back to default section listing
    default_content = {
        "type": "documentation_section",
        "section": section,
        "elements": []
    }

    for element in DEFAULT_SECTION_ELEMENTS[section]:
        default_content["elements"].append({
            "name": element,
            "description": f"Documentation for {element}"
        })

    return json.dumps(default_content, indent=2)
