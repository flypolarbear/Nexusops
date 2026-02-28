"""
NexusOps - Skill Sync Service

Syncs skills from skills.sh marketplace (GitHub) to local skill registry.
"""

import re
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AgentSkill, AgentSkillBinding
from app.core.config import settings


class SkillParseError(Exception):
    """Error parsing SKILL.md file"""
    pass


class SkillSyncError(Exception):
    """Error syncing skill from GitHub"""
    pass


def parse_skill_md(content: str) -> Dict[str, Any]:
    """
    Parse SKILL.md content into frontmatter and body.
    
    SKILL.md format:
    ---
    name: skill-name
    description: What this skill does
    license: MIT
    compatibility: opencode
    metadata:
      author: example-org
      version: "1.0"
    ---
    # Markdown content here...
    
    Returns:
        dict with keys: name, description, content, frontmatter, license, compatibility, metadata
    """
    # Check for YAML frontmatter
    if not content.startswith("---"):
        raise SkillParseError("SKILL.md must start with YAML frontmatter (---)")
    
    # Find the closing ---
    fm_end = content.find("---", 3)
    if fm_end == -1:
        raise SkillParseError("YAML frontmatter not properly closed")
    
    fm_raw = content[3:fm_end].strip()
    body = content[fm_end + 3:].strip()
    
    # Parse YAML frontmatter (simple key-value parsing)
    frontmatter = {}
    current_key = None
    current_indent = 0
    nested_dict = None
    
    for line in fm_raw.split("\n"):
        if not line.strip():
            continue
        
        # Check indentation
        indent = len(line) - len(line.lstrip())
        line = line.strip()
        
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            
            # Remove quotes from value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            
            if indent > 0 and nested_dict is not None:
                # Nested value
                nested_dict[key] = value if value else {}
                if not value:
                    current_nested_key = key
            else:
                # Top-level key
                frontmatter[key] = value if value else {}
                current_key = key
                nested_dict = None
                
                if not value:
                    # Start of nested dict
                    nested_dict = frontmatter[key]
        elif current_key and nested_dict is not None:
            # Continue nested dict
            nested_dict[current_key] = nested_dict.get(current_key, "") + " " + line
    
    # Extract required fields
    name = frontmatter.get("name")
    if not name:
        raise SkillParseError("SKILL.md must have 'name' field in frontmatter")
    
    description = frontmatter.get("description")
    if not description:
        raise SkillParseError("SKILL.md must have 'description' field in frontmatter")
    
    # Validate name format (lowercase, numbers, hyphens only)
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        raise SkillParseError(f"Invalid skill name '{name}': must be lowercase with hyphens only")
    
    return {
        "name": name,
        "description": description[:1024],  # Truncate to max length
        "content": content,
        "frontmatter": frontmatter,
        "license": frontmatter.get("license"),
        "compatibility": frontmatter.get("compatibility"),
        "skill_metadata": frontmatter.get("metadata", {}),
    }


class SkillSyncService:
    """Service for syncing skills from GitHub/skills.sh"""
    
    GITHUB_RAW_URL = "https://raw.githubusercontent.com"
    GITHUB_API_URL = "https://api.github.com"
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    async def fetch_skill_from_github(
        self,
        owner: str,
        repo: str,
        skill_path: str = "",
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Fetch a SKILL.md file from GitHub.
        
        Args:
            owner: GitHub owner/organization
            repo: Repository name
            skill_path: Path to skill directory (empty if skill is at root)
            branch: Git branch (default: main)
        
        Returns:
            Parsed skill data
        """
        # Construct URL to SKILL.md
        if skill_path:
            url = f"{self.GITHUB_RAW_URL}/{owner}/{repo}/{branch}/{skill_path}/SKILL.md"
        else:
            url = f"{self.GITHUB_RAW_URL}/{owner}/{repo}/{branch}/SKILL.md"
        
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            content = response.text
        except httpx.HTTPStatusError as e:
            # Try 'master' branch if 'main' fails
            if branch == "main":
                return await self.fetch_skill_from_github(owner, repo, skill_path, "master")
            raise SkillSyncError(f"Failed to fetch skill from {url}: {e}")
        except httpx.RequestError as e:
            raise SkillSyncError(f"Network error fetching skill: {e}")
        
        # Parse the SKILL.md content
        skill_data = parse_skill_md(content)
        skill_data["source_repo"] = f"{owner}/{repo}"
        skill_data["source_url"] = f"https://github.com/{owner}/{repo}"
        skill_data["skill_path"] = skill_path
        
        return skill_data
    
    async def list_skills_in_repo(
        self,
        owner: str,
        repo: str,
        branch: str = "main"
    ) -> List[str]:
        """
        List all skills in a GitHub repository.
        
        Returns:
            List of skill paths (relative paths to skill directories)
        """
        # Try to get repo contents via API
        url = f"{self.GITHUB_API_URL}/repos/{owner}/{repo}/contents"
        
        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                contents = response.json()
                skill_paths = []
                
                for item in contents:
                    if item["type"] == "dir":
                        # Check if this directory has a SKILL.md
                        skill_url = f"{self.GITHUB_RAW_URL}/{owner}/{repo}/{branch}/{item['name']}/SKILL.md"
                        try:
                            check = await self.http_client.head(skill_url)
                            if check.status_code == 200:
                                skill_paths.append(item["name"])
                        except:
                            pass
                    elif item["type"] == "file" and item["name"] == "SKILL.md":
                        # Skill at root
                        skill_paths.append("")
                
                return skill_paths
        except:
            pass
        
        return []
    
    async def sync_skill(
        self,
        owner: str,
        repo: str,
        skill_path: str = "",
        branch: str = "main"
    ) -> AgentSkill:
        """
        Sync a single skill from GitHub to the database.
        
        Returns:
            Created or updated AgentSkill
        """
        # Fetch skill data
        skill_data = await self.fetch_skill_from_github(owner, repo, skill_path, branch)
        
        # Generate skill ID
        if skill_path:
            skill_id = f"{owner}/{repo}/{skill_path}"
        else:
            skill_id = f"{owner}/{repo}/{skill_data['name']}"
        
        # Check if skill already exists
        stmt = select(AgentSkill).where(AgentSkill.id == skill_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing skill
            existing.name = skill_data["name"]
            existing.description = skill_data["description"]
            existing.content = skill_data["content"]
            existing.frontmatter = skill_data["frontmatter"]
            existing.license = skill_data.get("license")
            existing.compatibility = skill_data.get("compatibility")
            existing.skill_metadata = skill_data.get("skill_metadata")
            existing.source_url = skill_data["source_url"]
            existing.updated_at = datetime.utcnow()
            skill = existing
        else:
            # Create new skill
            skill = AgentSkill(
                id=skill_id,
                name=skill_data["name"],
                description=skill_data["description"],
                source_repo=skill_data["source_repo"],
                source_url=skill_data["source_url"],
                content=skill_data["content"],
                frontmatter=skill_data["frontmatter"],
                license=skill_data.get("license"),
                compatibility=skill_data.get("compatibility"),
                skill_metadata=skill_data.get("skill_metadata"),
                status="active",
                install_count=0,
            )
            self.session.add(skill)
        
        await self.session.commit()
        await self.session.refresh(skill)
        
        return skill
    
    async def sync_repo(self, owner: str, repo: str, branch: str = "main") -> List[AgentSkill]:
        """
        Sync all skills from a GitHub repository.
        
        Returns:
            List of synced AgentSkill objects
        """
        # List all skills in repo
        skill_paths = await self.list_skills_in_repo(owner, repo, branch)
        
        if not skill_paths:
            # Try syncing root SKILL.md
            try:
                skill = await self.sync_skill(owner, repo, "", branch)
                return [skill]
            except SkillSyncError:
                return []
        
        # Sync each skill
        synced = []
        for skill_path in skill_paths:
            try:
                skill = await self.sync_skill(owner, repo, skill_path, branch)
                synced.append(skill)
            except (SkillSyncError, SkillParseError) as e:
                # Log error but continue with other skills
                print(f"Warning: Failed to sync {owner}/{repo}/{skill_path}: {e}")
        
        return synced
    
    async def bind_skill_to_agent(
        self,
        skill_id: str,
        agent_id: str,
        priority: int = 0
    ) -> AgentSkillBinding:
        """
        Bind a skill to an agent.
        
        Returns:
            Created or updated AgentSkillBinding
        """
        binding_id = f"{agent_id}:{skill_id}"
        
        # Check if binding exists
        stmt = select(AgentSkillBinding).where(AgentSkillBinding.id == binding_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.enabled = True
            existing.priority = priority
            binding = existing
        else:
            binding = AgentSkillBinding(
                id=binding_id,
                agent_id=agent_id,
                skill_id=skill_id,
                enabled=True,
                priority=priority,
            )
            self.session.add(binding)
        
        await self.session.commit()
        await self.session.refresh(binding)
        
        return binding
    
    async def get_skills_for_agent(self, agent_id: str) -> List[AgentSkill]:
        """
        Get all skills bound to a specific agent.
        
        Returns:
            List of AgentSkill objects
        """
        stmt = (
            select(AgentSkill)
            .join(AgentSkillBinding, AgentSkill.id == AgentSkillBinding.skill_id)
            .where(AgentSkillBinding.agent_id == agent_id)
            .where(AgentSkillBinding.enabled == True)
            .where(AgentSkill.status == "active")
            .order_by(AgentSkillBinding.priority.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def list_skills(
        self,
        status: Optional[str] = None,
        source_repo: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentSkill]:
        """
        List all skills with optional filters.
        
        Returns:
            List of AgentSkill objects
        """
        stmt = select(AgentSkill)
        
        if status:
            stmt = stmt.where(AgentSkill.status == status)
        if source_repo:
            stmt = stmt.where(AgentSkill.source_repo == source_repo)
        
        stmt = stmt.order_by(AgentSkill.install_count.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# Convenience function for parsing skill ID
def parse_skill_id(skill_id: str) -> Dict[str, str]:
    """
    Parse a skill ID into its components.
    
    Args:
        skill_id: Skill ID in format "owner/repo/skill-name" or "owner/repo"
    
    Returns:
        dict with keys: owner, repo, skill_path
    """
    parts = skill_id.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid skill ID: {skill_id}")
    
    owner = parts[0]
    repo = parts[1]
    skill_path = "/".join(parts[2:]) if len(parts) > 2 else ""
    
    return {"owner": owner, "repo": repo, "skill_path": skill_path}
