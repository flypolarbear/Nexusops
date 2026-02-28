"""
NexusOps - Visual Test Specification Loader

This module provides utilities for loading visual test specifications from Markdown files.
OpenCode uses these specs to execute visual tests using its built-in browser and vision capabilities.

Usage:
    from tests.visual.framework import load_all_specs, load_spec
    
    # Load all specs
    specs = load_all_specs()
    
    # Load specific spec
    dashboard_spec = load_spec("dashboard")
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ScreenshotSpec:
    """Screenshot capture specification"""
    name: str
    action: str
    wait_for: str


@dataclass
class AssertionSpec:
    """Visual assertion specification"""
    category: str  # aesthetics, interaction, functionality
    name: str
    expected: str
    checks: list[str] = field(default_factory=list)


@dataclass
class VisualTestSpec:
    """Complete visual test specification for a page"""
    name: str
    url: str
    viewport_width: int = 1920
    viewport_height: int = 1080
    prerequisites: list[str] = field(default_factory=list)
    screenshots: list[ScreenshotSpec] = field(default_factory=list)
    assertions: list[AssertionSpec] = field(default_factory=list)
    error_states: list[dict] = field(default_factory=list)


def parse_markdown_spec(file_path: Path) -> VisualTestSpec:
    """Parse a Markdown visual test specification file."""
    content = file_path.read_text()
    name = file_path.stem
    
    # Extract URL
    url_match = re.search(r"## URL\n[`']?([^`\n]+)[`']?", content)
    url = url_match.group(1).strip() if url_match else "/"
    
    # Extract viewport
    viewport_width = 1920
    viewport_height = 1080
    viewport_match = re.search(r"## Viewport\n- Width: (\d+)\n- Height: (\d+)", content)
    if viewport_match:
        viewport_width = int(viewport_match.group(1))
        viewport_height = int(viewport_match.group(2))
    
    # Extract prerequisites
    prerequisites = []
    prereq_match = re.search(r"## Prerequisites\n([\s\S]*?)(?=\n---|\n## )", content)
    if prereq_match:
        prereq_text = prereq_match.group(1)
        prerequisites = [
            line.strip()[2:]  # Remove "- " prefix
            for line in prereq_text.strip().split("\n")
            if line.strip().startswith("- ")
        ]
    
    # Extract screenshots
    screenshots = []
    screenshot_pattern = r"### Screenshot \d+: (.+?)\n- \*\*Action\*\*: ([^\n]+)\n- \*\*Wait for\*\*: ([^\n]+)"
    for match in re.finditer(screenshot_pattern, content):
        screenshots.append(ScreenshotSpec(
            name=match.group(1).strip(),
            action=match.group(2).strip(),
            wait_for=match.group(3).strip(),
        ))
    
    # Extract assertions
    assertions = []
    assertion_pattern = r"#### ([AFI]\d+): (.+?)\n- \*\*Expected\*\*: ([^\n]+)\n- \*\*Check\*\?:\n([\s\S]*?)(?=\n#### |\n---|\n## |$)"
    for match in re.finditer(assertion_pattern, content):
        assertion_id = match.group(1)
        assertion_name = match.group(2).strip()
        expected = match.group(3).strip()
        checks_text = match.group(4)
        
        # Determine category from ID prefix
        if assertion_id.startswith("A"):
            category = "aesthetics"
        elif assertion_id.startswith("I"):
            category = "interaction"
        elif assertion_id.startswith("F"):
            category = "functionality"
        else:
            category = "unknown"
        
        checks = [
            line.strip()[2:]  # Remove "- " prefix
            for line in checks_text.strip().split("\n")
            if line.strip().startswith("- ")
        ]
        
        assertions.append(AssertionSpec(
            category=category,
            name=assertion_name,
            expected=expected,
            checks=checks,
        ))
    
    return VisualTestSpec(
        name=name,
        url=url,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        prerequisites=prerequisites,
        screenshots=screenshots,
        assertions=assertions,
    )


def load_spec(spec_name: str) -> Optional[VisualTestSpec]:
    """Load a specific visual test specification by name."""
    specs_dir = Path(__file__).parent / "specs"
    spec_file = specs_dir / f"{spec_name}.md"
    
    if spec_file.exists():
        return parse_markdown_spec(spec_file)
    return None


def load_all_specs() -> list[VisualTestSpec]:
    """Load all visual test specifications."""
    specs_dir = Path(__file__).parent / "specs"
    specs = []
    
    for spec_file in specs_dir.glob("*.md"):
        if spec_file.name != "README.md":
            specs.append(parse_markdown_spec(spec_file))
    
    return specs


def get_available_specs() -> list[str]:
    """Get list of available spec names."""
    specs_dir = Path(__file__).parent / "specs"
    return [
        f.stem
        for f in specs_dir.glob("*.md")
        if f.stem != "README"
    ]


# Convenience exports
__all__ = [
    "VisualTestSpec",
    "ScreenshotSpec", 
    "AssertionSpec",
    "load_spec",
    "load_all_specs",
    "get_available_specs",
]
