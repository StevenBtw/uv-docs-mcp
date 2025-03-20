import json
import os
import unicodedata
from pathlib import Path
import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from typing import Any, Dict, List, TypedDict, Optional

class DocumentationSection(TypedDict):
    title: str
    content: List[str]
    
class SubSection(TypedDict):
    title: str
    content: List[str]

DocumentationType = List[SubSection]

class CacheManager:
    """Manages UV documentation cache storage and retrieval."""
    
    def __init__(self):
        # Use XDG Base Directory standard for cache location
        if os.name == 'nt':  # Windows
            cache_root = Path(os.environ.get('LOCALAPPDATA', '~/AppData/Local')).expanduser()
        else:  # Unix-like
            cache_root = Path(os.environ.get('XDG_CACHE_HOME', '~/.cache')).expanduser()
        
        self.cache_dir = cache_root / 'uv-docs'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.version_file = self.cache_dir / 'version.json'

    async def initialize(self) -> None:
        """Initialize the cache with current version if it doesn't exist."""
        try:
            # Create initial version file if it doesn't exist
            if not self.version_file.exists():
                version_info = await self.fetch_current_version()
                await self.update_version(version_info)
                
                # Fetch all documentation sections
                sections = {
                    "cli": self.fetch_cli_documentation,
                    "settings": self.fetch_settings_documentation,
                    "resolver": self.fetch_resolver_documentation
                }
                
                for section, fetch_func in sections.items():
                    section_docs = await fetch_func()
                    await self.update_section(section, section_docs)
                
            print(f"Cache initialized at {self.cache_dir}")
        except Exception as e:
            print(f"Failed to initialize cache: {e}")
            # Ensure version file exists even if fetch fails
            if not self.version_file.exists():
                await self.update_version({"version": "unknown"})

    async def get_cached_version(self) -> Dict[str, str]:
        """Get the cached UV version information."""
        try:
            if self.version_file.exists():
                async with aiofiles.open(self.version_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    async def update_version(self, version_info: Dict[str, str]) -> None:
        """Update the cached version information."""
        async with aiofiles.open(self.version_file, 'w') as f:
            await f.write(json.dumps(version_info))

    def get_section_cache_path(self, section: str) -> Path:
        """Get the cache file path for a specific documentation section."""
        return self.cache_dir / f'{section}.json'

    async def get_cached_section(self, section: str) -> Dict[str, Any]:
        """Get cached content for a specific documentation section."""
        cache_path = self.get_section_cache_path(section)
        try:
            if cache_path.exists():
                async with aiofiles.open(cache_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    async def update_section(self, section: str, content: Dict[str, Any]) -> None:
        """Update the cache for a specific documentation section."""
        cache_path = self.get_section_cache_path(section)
        async with aiofiles.open(cache_path, 'w') as f:
            await f.write(json.dumps(content, indent=2))

    async def clear_cache(self) -> None:
        """Clear all cached documentation."""
        for file in self.cache_dir.glob('*.json'):
            file.unlink()
            
    async def is_cache_valid(self) -> bool:
        """Check if the cache is valid by comparing versions."""
        try:
            current_version = await self.fetch_current_version()
            cached_version = await self.get_cached_version()
            return cached_version.get('version') == current_version.get('version')
        except Exception:
            return False

    async def fetch_current_version(self) -> Dict[str, str]:
        """Fetch current UV version from docs website."""
        async with aiohttp.ClientSession() as session:
            # Try to get version from PyPI as it's more reliable
            async with session.get('https://pypi.org/pypi/uv/json') as response:
                if response.status == 200:
                    data = await response.json()
                    if 'info' in data and 'version' in data['info']:
                        return {'version': data['info']['version']}

            # Fallback to docs website if PyPI fails
            async with session.get('https://docs.astral.sh/uv/reference/cli/') as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for version in breadcrumb or navigation
                version_text = None
                for elem in soup.select('p, span, div'):
                    if 'version' in elem.get_text().lower():
                        version_text = elem.get_text()
                        break
                if version_text and ' ' in version_text:
                    version = version_text.split()[-1]  # Get last word which should be version
                    return {'version': version.strip()}
        return {'version': 'unknown'}

    def clean_text(self, text: str) -> str:
        """Clean text by normalizing Unicode characters and replacing special characters."""
        text = unicodedata.normalize("NFKC", text)  # Normalize Unicode characters
        # Handle curly quotes and other special characters
        replacements = {
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u2013': '-',   # En dash
            '\n': ' ',       # Newline
            '\t': ' '       # Tab
        }
        for old, new in replacements.items():
            if old in text:
                text = text.replace(old, new)
        text = ' '.join(text.split())  # Normalize multiple spaces
        return text.strip()

    def clean_code(self, text: str) -> str:
        """Clean code text while preserving newlines and indentation."""
        text = unicodedata.normalize("NFKC", text)  # Normalize Unicode characters
        text = text.replace('\t', '    ')  # Convert tabs to spaces
        return text.strip()

    async def fetch_cli_documentation(self) -> Dict[str, Any]:
        """Fetch CLI documentation from the website."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://docs.astral.sh/uv/reference/cli/') as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                content = soup.select_one('.md-content')
                
                if not content:
                    return {}
                
                elements = []
                for section in content.find_all('h2'):
                    command_name = self.clean_text(section.get_text(strip=True))
                    description = self.clean_text(section.find_next('p').get_text(strip=True) 
                                            if section.find_next('p') else "")

                    # Initialize documentation as a structured list
                    documentation = []
                    current_subsection: Optional[SubSection] = None
                    general_content = []
                    options_content = []

                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name != 'h2':
                        if next_elem.name in ['h3', 'h4']:
                            # Store previous general content if it has data
                            if general_content:
                                documentation.append({"title": "General", "content": general_content})
                                general_content = []

                            # Create a new subsection for h3/h4 headers
                            current_subsection = {
                                "title": self.clean_text(next_elem.get_text(strip=True)),
                                "content": []
                            }
                            documentation.append(current_subsection)

                        elif next_elem.name in ['p', 'pre', 'ul', 'ol']:
                            text = self.clean_text(next_elem.get_text(strip=True))
                            if current_subsection:
                                current_subsection.setdefault("content", []).append(text)
                            else:
                                general_content.append(text)

                        elif next_elem.name == 'dl':  # Handling options
                            for dt, dd in zip(next_elem.find_all('dt'), next_elem.find_all('dd')):
                                option_name = self.clean_text(dt.get_text(strip=True))
                                option_desc = self.clean_text(dd.get_text(strip=True))
                                options_content.append(f"{option_name}: {option_desc}")

                        next_elem = next_elem.find_next_sibling()

                    # Append remaining general content
                    if general_content:
                        documentation.append({"title": "General", "content": general_content})

                    # Append options as a single section if present
                    if options_content:
                        documentation.append({"title": "Options", "content": options_content})

                    # Remove empty sections
                    documentation = [section for section in documentation if section["content"]]

                    elements.append({
                        "name": command_name,
                        "description": description,
                        "documentation": documentation
                    })

                return {
                    "type": "documentation_section",
                    "section": "cli",
                    "elements": elements
                }

    async def fetch_settings_documentation(self) -> Dict[str, Any]:
        """Fetch settings documentation from the website."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://docs.astral.sh/uv/reference/settings/') as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                content = soup.select_one('.md-content')

                if not content:
                    return {}

                elements = []
                for section in content.find_all('h2'):
                    setting_name = self.clean_text(section.get_text(strip=True))
                    description = self.clean_text(
                        section.find_next('p').get_text(strip=True) if section.find_next('p') else ""
                    )

                    documentation = []
                    current_subsection: Optional[SubSection] = None
                    general_content = []

                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name != 'h2':
                        if next_elem.name in ['h3', 'h4']:
                            if general_content:
                                documentation.append({"title": "General", "content": general_content})
                                general_content = []

                            current_subsection = {
                                "title": self.clean_text(next_elem.get_text(strip=True)),
                                "content": []
                            }
                            documentation.append(current_subsection)

                        elif next_elem.name in ['p', 'ul', 'ol']:
                            text = self.clean_text(next_elem.get_text(strip=True))
                            if current_subsection:
                                current_subsection["content"].append(text)
                            else:
                                general_content.append(text)

                        elif next_elem.name == "div" and any(c in next_elem.get("class", []) for c in ["highlight", "highlight-default"]):
                            # Extract example from code block
                            pre_tag = next_elem.find("pre")
                            if pre_tag:
                                example_text = self.clean_code(pre_tag.get_text("\n", strip=True))
                                if current_subsection is not None:
                                    current_subsection["content"].append(f"Example:\n{example_text}")
                                else:
                                    general_content.append(f"Example:\n{example_text}")

                        next_elem = next_elem.find_next_sibling()

                    if general_content:
                        documentation.append({"title": "General", "content": general_content})

                    documentation = [section for section in documentation if section["content"]]

                    elements.append({
                        "name": setting_name,
                        "description": description,
                        "documentation": documentation
                    })

                return {
                    "type": "documentation_section",
                    "section": "settings",
                    "elements": elements
                }

    async def fetch_resolver_documentation(self) -> Dict[str, Any]:
        """Fetch resolver documentation from the website."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://docs.astral.sh/uv/reference/resolver-internals/') as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Ensure we are selecting the correct container
                content = soup.select_one('.md-content')

                if not content:
                    return {}

                elements = []
                sections = content.find_all('h2')

                if not sections:
                    return {}
                for section in sections:
                    resolver_name = self.clean_text(section.get_text(strip=True))

                    # Try to get the description (handle cases where it's inside .admonition)
                    description = ""
                    description_elem = section.find_next_sibling()

                    # Look for description in all content until next h2
                    while description_elem and description_elem.name not in ['h2', 'h3', 'h4']:
                        if description_elem.name == "p":
                            description += " " + self.clean_text(description_elem.get_text(strip=True))
                        elif description_elem.name == "div" and "admonition" in description_elem.get("class", []):
                            description += " " + self.clean_text(description_elem.get_text(strip=True))
                        elif description_elem.name in ['ul', 'ol']:  # Handle bullet lists
                            for li in description_elem.find_all('li'):
                                description += "\n- " + self.clean_text(li.get_text(strip=True))
                        description_elem = description_elem.find_next_sibling()

                    documentation = []
                    current_subsection: Optional[SubSection] = None
                    general_content = []

                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name != 'h2':
                        if next_elem.name in ['h3', 'h4']:
                            if general_content:
                                documentation.append({"title": "General", "content": general_content})
                                general_content = []

                            current_subsection = {
                                "title": self.clean_text(next_elem.get_text(strip=True)),
                                "content": []
                            }
                            documentation.append(current_subsection)

                        elif next_elem.name in ['p', 'ul', 'ol']:
                            text = self.clean_text(next_elem.get_text(strip=True))
                            if current_subsection:
                                current_subsection["content"].append(text)
                            else:
                                general_content.append(text)

                        elif next_elem.name == "div" and any(c in next_elem.get("class", []) for c in ["highlight", "highlight-default"]):
                            # Extract example from code block
                            pre_tag = next_elem.find("pre")
                            if pre_tag:
                                example_text = self.clean_code(pre_tag.get_text("\n", strip=True))
                                if current_subsection is not None:
                                    current_subsection["content"].append(f"Example:\n{example_text}")
                                else:
                                    general_content.append(f"Example:\n{example_text}")

                        next_elem = next_elem.find_next_sibling()

                    if general_content:
                        documentation.append({"title": "General", "content": general_content})

                    documentation = [section for section in documentation if section["content"]]

                    elements.append({
                        "name": resolver_name,
                        "description": description.strip(),
                        "documentation": documentation
                    })


                return {
                    "type": "documentation_section",
                    "section": "resolver",
                    "elements": elements
                }

# Global cache manager instance
cache_manager = CacheManager()