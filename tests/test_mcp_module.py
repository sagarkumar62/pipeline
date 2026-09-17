import pytest
import os
import json
import hashlib
from src.models.mcp import MCPRecord
from src.models.tool import ToolRecord
from src.models.repository import RepositoryRecord
from src.extraction.mcp_extractor import MCPExtractor
from src.qualification.mcp_qualifier import MCPQualifier
from src.deduplication.mcp_resolver import MCPDeduplicationResolver


def test_mcp_record_validation():
    rec = MCPRecord.create_canonical(
        name="Filesystem MCP Server",
        server_name="server-filesystem",
        package_name="@modelcontextprotocol/server-filesystem",
        repository_url="https://github.com/modelcontextprotocol/servers",
        description="Official Model Context Protocol server for local filesystem access.",
        transport=["stdio"],
        capabilities=["tools", "resources"],
        license="MIT"
    )
    assert rec.name == "Filesystem MCP Server"
    assert rec.entity_type == "MCP"
    assert rec.package_name == "@modelcontextprotocol/server-filesystem"
    assert "stdio" in rec.transport
    assert "tools" in rec.capabilities


def test_mcp_required_identity_fields():
    rec = MCPRecord.create_canonical(
        name="Fetch MCP",
        maintainer="modelcontextprotocol",
        repository_url="https://github.com/modelcontextprotocol/server-fetch"
    )
    assert rec.entity_type == "MCP"
    assert rec.id == "mcp:modelcontextprotocol/server-fetch"
    assert rec.url == "https://github.com/modelcontextprotocol/server-fetch"


def test_mcp_qualification_hierarchy():
    qualifier = MCPQualifier()
    candidate = {
        "name": "sqlite-mcp-server",
        "description": "Model Context Protocol server for SQLite databases",
        "topics": ["mcp-server", "sqlite"],
        "archived": False,
        "fork": False
    }
    status, reason = qualifier.qualify(candidate)
    assert status == "QUALIFIED"


def test_mcp_hard_exclusion_precedence():
    qualifier = MCPQualifier()
    # Awesome list repository mentioning MCP (positive signal MUST NOT override hard exclusion)
    awesome_item = {
        "name": "awesome-mcp-servers",
        "description": "A curated list of awesome Model Context Protocol (MCP) servers and tools",
        "topics": ["awesome", "mcp"],
        "stars": 5000,
        "archived": False
    }
    status, reason = qualifier.qualify(awesome_item)
    assert status == "HARD_EXCLUSION"
    assert "Awesome" in reason or "hard negative" in reason


def test_mcp_review_precedence():
    qualifier = MCPQualifier()
    # Fork of MCP repo requiring upstream review
    fork_item = {
        "name": "server-postgres",
        "description": "Forked Model Context Protocol server for PostgreSQL",
        "topics": ["mcp"],
        "fork": True
    }
    status, reason = qualifier.qualify(fork_item)
    assert status == "REVIEW_REQUIRED"
    assert "fork" in reason.lower()


def test_mcp_positive_qualification():
    qualifier = MCPQualifier()
    valid_mcp = {
        "name": "git-mcp-server",
        "description": "MCP server enabling AI assistants to inspect Git repositories",
        "topics": ["mcp-server"]
    }
    status, reason = qualifier.qualify(valid_mcp)
    assert status == "QUALIFIED"


def test_mcp_provenance_completeness():
    extractor = MCPExtractor()
    raw = {
        "name": "mcp-server-git",
        "owner": {"login": "modelcontextprotocol"},
        "html_url": "https://github.com/modelcontextprotocol/servers",
        "description": "Git MCP server implementation",
        "_discovery_query": "topic:mcp-server",
        "_discovery_source": "GitHub MCP Search"
    }
    rec = extractor.to_record(raw)
    assert rec.discovery_source.name == "GitHub MCP Search"
    assert len(rec.evidence_sources) == 1
    assert rec.evidence_sources[0].url == "https://github.com/modelcontextprotocol/servers"


def test_mcp_deterministic_deduplication():
    resolver = MCPDeduplicationResolver()
    rec1 = {
        "id": "mcp:modelcontextprotocol/server-git",
        "package_name": "@modelcontextprotocol/server-git",
        "repository_url": "https://github.com/modelcontextprotocol/servers"
    }
    rec2 = {
        "id": "mcp:modelcontextprotocol/server-git",
        "package_name": "@modelcontextprotocol/server-git",
        "repository_url": "https://github.com/modelcontextprotocol/servers"
    }
    res1, dup1 = resolver.resolve(rec1)
    assert not dup1

    res2, dup2 = resolver.resolve(rec2)
    assert dup2
    assert res2["duplicate_of"] == "mcp:modelcontextprotocol/server-git"


def test_mcp_repository_identity_deduplication():
    resolver = MCPDeduplicationResolver()
    rec1 = {
        "id": "mcp:myorg/custom-mcp",
        "repository_url": "https://github.com/myorg/custom-mcp"
    }
    rec2 = {
        "id": "mcp:myorg/custom-mcp-alt",
        "repository_url": "https://github.com/myorg/custom-mcp"
    }
    resolver.resolve(rec1)
    resolved2, dup2 = resolver.resolve(rec2)
    assert dup2
    assert resolved2["match_method"] == "exact_repository_url"


def test_mcp_package_identity_handling():
    resolver = MCPDeduplicationResolver()
    rec1 = {
        "id": "mcp:pkg:server-memory",
        "package_name": "@modelcontextprotocol/server-memory"
    }
    rec2 = {
        "id": "mcp:pkg:server-memory-copy",
        "package_name": "@modelcontextprotocol/server-memory"
    }
    resolver.resolve(rec1)
    resolved2, dup2 = resolver.resolve(rec2)
    assert dup2
    assert resolved2["match_method"] == "exact_package_identifier"


def test_mcp_cross_source_duplicate_merging():
    resolver = MCPDeduplicationResolver()
    github_item = {
        "id": "mcp:modelcontextprotocol/servers",
        "repository_url": "https://github.com/modelcontextprotocol/servers"
    }
    registry_item = {
        "id": "mcp:modelcontextprotocol/servers",
        "repository_url": "https://github.com/modelcontextprotocol/servers"
    }
    resolver.resolve(github_item)
    res2, dup2 = resolver.resolve(registry_item)
    assert dup2


def test_mcp_distinction_between_separate_entities():
    resolver = MCPDeduplicationResolver()
    rec1 = {
        "id": "mcp:orgA/postgres-mcp",
        "maintainer": "orgA",
        "name": "postgres-mcp",
        "repository_url": "https://github.com/orgA/postgres-mcp"
    }
    rec2 = {
        "id": "mcp:orgB/postgres-mcp",
        "maintainer": "orgB",
        "name": "postgres-mcp",
        "repository_url": "https://github.com/orgB/postgres-mcp"
    }
    resolver.resolve(rec1)
    res2, dup2 = resolver.resolve(rec2)
    assert not dup2


def test_mcp_official_website_verification_semantics():
    rec = MCPRecord.create_canonical(
        name="Puppeteer MCP Server",
        repository_url="https://github.com/modelcontextprotocol/servers",
        official_url="https://modelcontextprotocol.io"
    )
    assert rec.official_url == "https://modelcontextprotocol.io"


def test_mcp_github_not_official_website_rule():
    rec = MCPRecord.create_canonical(
        name="Slack MCP Server",
        repository_url="https://github.com/modelcontextprotocol/servers"
    )
    assert "github.com" in rec.repository_url


def test_mcp_social_preview_not_verified_logo():
    rec = MCPRecord.create_canonical(
        name="Memory MCP",
        repository_url="https://github.com/modelcontextprotocol/servers"
    )
    assert rec.logo_verified is False
    assert rec.logo_url is None


def test_mcp_description_grounding():
    extractor = MCPExtractor()
    raw = {
        "name": "server-brave-search",
        "owner": "modelcontextprotocol",
        "html_url": "https://github.com/modelcontextprotocol/servers",
        "description": "Brave Search API integration for Model Context Protocol."
    }
    rec = extractor.to_record(raw)
    assert rec.description == "Brave Search API integration for Model Context Protocol."


def test_mcp_missing_evidence_handling():
    extractor = MCPExtractor()
    raw = {
        "name": "generic-repo",
        "owner": "testuser",
        "html_url": "https://github.com/testuser/generic-repo",
        "description": "Some repository without transport or capabilities keywords"
    }
    rec = extractor.to_record(raw)
    assert rec.transport == []
    assert rec.capabilities == []
    assert rec.supported_clients == []


def test_mcp_category_handling():
    rec = MCPRecord.create_canonical(
        name="Postgres MCP",
        repository_url="https://github.com/modelcontextprotocol/servers",
        categories=["MCP", "Databases"]
    )
    assert "MCP" in rec.categories
    assert "Databases" in rec.categories


def test_mcp_malformed_source_record_handling():
    extractor = MCPExtractor()
    raw = {
        "name": None,
        "owner": None,
        "html_url": None
    }
    extracted = extractor.extract(raw)
    assert extracted["name"] == ""


def test_mcp_rate_limit_retry_configuration():
    from src.discovery.mcp_discovery import MCPAdapter
    adapter = MCPAdapter(per_page=15, max_pages_per_query=1)
    assert adapter.per_page == 15
    assert adapter.max_pages_per_query == 1


def test_protected_tools_dataset_integrity():
    tools_json_path = "data/exports/tools.json"
    if os.path.exists(tools_json_path):
        with open(tools_json_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "4520014C9A1676F9090BE806087A92AC0E12FEF3D3136A95860CFF48388FF2A1"


def test_protected_repository_dataset_integrity():
    repos_final_path = "data/working/repositories/repositories_final.json"
    if os.path.exists(repos_final_path):
        with open(repos_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "176D5DEEEC8063FC4684C058B5E758649E57375ACE6AB5ADA05A4ECE43FB8465"
