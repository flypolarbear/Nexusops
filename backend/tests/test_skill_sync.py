"""
Skill Sync Service Unit Tests

Tests for parsing SKILL.md files and skill sync functionality.
"""

import pytest

from app.services.skill_sync import parse_skill_md, SkillParseError


class TestParseSkillMd:
    """Tests for SKILL.md parsing"""

    def test_parse_minimal_skill(self):
        """Parse a minimal valid SKILL.md"""
        content = """---
name: test-skill
description: A test skill for unit testing
---
# Test Skill

This is the body content.
"""
        result = parse_skill_md(content)
        
        assert result["name"] == "test-skill"
        assert result["description"] == "A test skill for unit testing"
        assert "Test Skill" in result["content"]
        assert result["license"] is None
        assert result["compatibility"] is None

    def test_parse_full_skill(self):
        """Parse a SKILL.md with all optional fields"""
        content = """---
name: pdf-processing
description: Extract text and tables from PDF files
license: MIT
compatibility: opencode
metadata:
  author: example-org
  version: "1.0"
---
# PDF Processing

## Usage
Use this skill when working with PDF files.
"""
        result = parse_skill_md(content)
        
        assert result["name"] == "pdf-processing"
        assert result["description"] == "Extract text and tables from PDF files"
        assert result["license"] == "MIT"
        assert result["compatibility"] == "opencode"
        assert "PDF Processing" in result["content"]

    def test_parse_missing_frontmatter(self):
        """Should raise error if frontmatter is missing"""
        content = """# No Frontmatter
This has no YAML frontmatter.
"""
        with pytest.raises(SkillParseError) as exc:
            parse_skill_md(content)
        assert "must start with YAML frontmatter" in str(exc.value)

    def test_parse_unclosed_frontmatter(self):
        """Should raise error if frontmatter is not closed"""
        content = """---
name: test-skill
description: Missing closing delimiter
# Content
"""
        with pytest.raises(SkillParseError) as exc:
            parse_skill_md(content)
        assert "not properly closed" in str(exc.value)

    def test_parse_missing_name(self):
        """Should raise error if name is missing"""
        content = """---
description: Missing name field
---
# Content
"""
        with pytest.raises(SkillParseError) as exc:
            parse_skill_md(content)
        assert "'name' field" in str(exc.value)

    def test_parse_missing_description(self):
        """Should raise error if description is missing"""
        content = """---
name: test-skill
---
# Content
"""
        with pytest.raises(SkillParseError) as exc:
            parse_skill_md(content)
        assert "'description' field" in str(exc.value)

    def test_parse_invalid_name_with_spaces(self):
        """Should raise error if name contains spaces"""
        content = """---
name: test skill
description: Name has spaces
---
# Content
"""
        with pytest.raises(SkillParseError) as exc:
            parse_skill_md(content)
        assert "Invalid skill name" in str(exc.value)

    def test_parse_invalid_name_uppercase(self):
        """Should raise error if name contains uppercase"""
        content = """---
name: Test-Skill
description: Name has uppercase
---
# Content
"""
        with pytest.raises(SkillParseError) as exc:
            parse_skill_md(content)
        assert "Invalid skill name" in str(exc.value)

    def test_parse_valid_name_with_hyphens(self):
        """Should accept names with hyphens"""
        content = """---
name: my-awesome-skill-123
description: Valid hyphenated name
---
# Content
"""
        result = parse_skill_md(content)
        assert result["name"] == "my-awesome-skill-123"

    def test_parse_description_truncated(self):
        """Should truncate description to 1024 characters"""
        long_desc = "x" * 2000
        content = f"""---
name: test-skill
description: {long_desc}
---
# Content
"""
        result = parse_skill_md(content)
        assert len(result["description"]) == 1024

    def test_parse_quoted_values(self):
        """Should remove quotes from quoted values"""
        content = '''---
name: test-skill
description: "A quoted description"
license: "MIT"
---
# Content
'''
        result = parse_skill_md(content)
        assert result["description"] == "A quoted description"
        assert result["license"] == "MIT"


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
