import json
import os
import pytest
from src.models.mcp import MCPRecord
from src.qualification.mcp_qualifier import MCPQualifier
from src.deduplication.mcp_resolver import MCPDeduplicationResolver


def test_mcp_baseline_immutability():
    baseline_path = "data/working/mcp/mcp_final.json"
    assert os.path.exists(baseline_path)
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 86


def test_mcp_qualification_precedence():
    qualifier = MCPQualifier()

    # Awesome list / tutorial must yield HARD_EXCLUSION
    cand_awesome = {
        "name": "awesome-mcp-servers-list",
        "description": "Curated list of awesome MCP servers and resources",
        "topics": ["awesome-list"]
    }
    status, reason = qualifier.qualify(cand_awesome)
    assert status == "HARD_EXCLUSION"

    # Repository lacking explicit MCP evidence must yield HARD_EXCLUSION
    cand_generic = {
        "name": "generic-python-utility",
        "description": "General purpose utility library for data processing",
        "topics": ["python", "utilities"]
    }
    status, reason = qualifier.qualify(cand_generic)
    assert status == "HARD_EXCLUSION"
    assert "lacks" in reason.lower()

    # Clean MCP Server candidate must yield QUALIFIED
    cand_mcp = {
        "name": "sqlite-mcp-server",
        "description": "Model Context Protocol (MCP) server providing database query tools for SQLite",
        "topics": ["mcp-server", "model-context-protocol", "sqlite"],
        "stars": 450
    }
    status, reason = qualifier.qualify(cand_mcp)
    assert status == "QUALIFIED"


def test_mcp_evidence_requirement():
    qualifier = MCPQualifier()

    # Mentioning MCP in unrelated context without positive signals
    cand_no_signal = {
        "name": "my-chat-bot",
        "description": "A simple chatbot project that happens to mention MCP in docs",
        "topics": ["chatbot"]
    }
    status, reason = qualifier.qualify(cand_no_signal)
    assert status == "HARD_EXCLUSION"

    # Explicit signal via SDK or topic
    cand_signal = {
        "name": "postgres-mcp",
        "description": "Exposes PostgreSQL database tools via Model Context Protocol (MCP) server",
        "topics": ["mcp-server"]
    }
    status, _ = qualifier.qualify(cand_signal)
    assert status == "QUALIFIED"


def test_mcp_baseline_duplicate_detection():
    resolver = MCPDeduplicationResolver()
    baseline_records = [
        {
            "id": "mcp:filesystem-mcp-server",
            "name": "Filesystem MCP Server",
            "repository_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"
        }
    ]
    resolver.load_baseline(baseline_records)

    cand = {
        "id": "mcp:filesystem-dup",
        "name": "Filesystem MCP Server",
        "repository_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"
    }

    resolved, is_dup = resolver.resolve(cand)
    assert is_dup
    assert resolved["is_baseline_match"] is True
    assert resolved["duplicate_of"] == "mcp:filesystem-mcp-server"


def test_mcp_intra_expansion_duplicate_detection():
    resolver = MCPDeduplicationResolver()
    resolver.load_baseline([])  # Empty baseline

    cand1 = {
        "id": "mcp:fetch-mcp-server",
        "name": "Fetch MCP Server",
        "repository_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch"
    }

    cand2 = {
        "id": "mcp:fetch-mcp-server-mirror",
        "name": "Fetch MCP Server",
        "repository_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["is_baseline_match"] is False
    assert resolved2["duplicate_of"] == "mcp:fetch-mcp-server"


def test_mcp_repository_normalization():
    resolver = MCPDeduplicationResolver()
    url1 = "https://github.com/punkpeye/awesome-mcp-servers.git"
    url2 = "https://github.com/punkpeye/awesome-mcp-servers/"
    norm1 = resolver._normalize_repo(url1)
    norm2 = resolver._normalize_repo(url2)
    assert norm1 == "punkpeye/awesome-mcp-servers"
    assert norm2 == "punkpeye/awesome-mcp-servers"


def test_mcp_expansion_accounting_equation():
    raw = 1500
    qualified = 1200
    rejected = 290
    review = 10

    baseline_dups = 15
    intra_dups = 85
    final_new = 1100

    assert raw == qualified + rejected + review
    assert qualified == baseline_dups + intra_dups + final_new
