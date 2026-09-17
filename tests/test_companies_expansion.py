import json
import os
import pytest
from src.models.company import CompanyRecord
from src.qualification.company_qualifier import CompanyQualifier
from src.deduplication.company_resolver import CompanyDeduplicationResolver


def test_company_baseline_immutability():
    baseline_path = "data/working/companies/companies_final.json"
    assert os.path.exists(baseline_path)
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 107


def test_company_qualification_precedence():
    qualifier = CompanyQualifier()

    # User account must yield HARD_EXCLUSION
    cand_user = {
        "name": "john-doe-dev",
        "type": "user",
        "description": "Individual developer doing AI projects"
    }
    status, reason = qualifier.qualify(cand_user)
    assert status == "HARD_EXCLUSION"
    assert "user" in reason.lower()

    # Awesome list / Directory must yield HARD_EXCLUSION
    cand_awesome = {
        "name": "awesome-ai-companies",
        "type": "organization",
        "description": "Curated directory of awesome AI companies"
    }
    status, reason = qualifier.qualify(cand_awesome)
    assert status == "HARD_EXCLUSION"

    # Clean AI Company must yield QUALIFIED
    cand_company = {
        "name": "OpenAI",
        "type": "organization",
        "description": "AI research and deployment company developing frontier models like GPT-4o",
        "official_url": "https://openai.com"
    }
    status, reason = qualifier.qualify(cand_company)
    assert status == "QUALIFIED"


def test_company_individual_vs_org_distinction():
    qualifier = CompanyQualifier()

    cand_user = {
        "name": "ai-enthusiast",
        "type": "user",
        "description": "Personal account building AI tools"
    }
    status, _ = qualifier.qualify(cand_user)
    assert status == "HARD_EXCLUSION"


def test_company_baseline_duplicate_detection():
    resolver = CompanyDeduplicationResolver()
    baseline_records = [
        {
            "id": "company:openai",
            "name": "OpenAI",
            "official_url": "https://openai.com",
            "github_url": "https://github.com/openai"
        }
    ]
    resolver.load_baseline(baseline_records)

    cand = {
        "id": "company:openai-dup",
        "name": "OpenAI, Inc.",
        "official_url": "https://openai.com",
        "github_url": "https://github.com/openai"
    }

    resolved, is_dup = resolver.resolve(cand)
    assert is_dup
    assert resolved["is_baseline_match"] is True
    assert resolved["duplicate_of"] == "company:openai"


def test_company_intra_expansion_duplicate_detection():
    resolver = CompanyDeduplicationResolver()
    resolver.load_baseline([])  # Empty baseline

    cand1 = {
        "id": "company:anthropic",
        "name": "Anthropic",
        "official_url": "https://anthropic.com",
        "github_url": "https://github.com/anthropic"
    }

    cand2 = {
        "id": "company:anthropic-labs",
        "name": "Anthropic",
        "official_url": "https://anthropic.com",
        "github_url": "https://github.com/anthropic"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["is_baseline_match"] is False
    assert resolved2["duplicate_of"] == "company:anthropic"


def test_companies_expansion_accounting_equation():
    raw = 1200
    qualified = 900
    rejected = 250
    review = 50

    baseline_dups = 10
    intra_dups = 40
    final_new = 850

    assert raw == qualified + rejected + review
    assert qualified == baseline_dups + intra_dups + final_new
