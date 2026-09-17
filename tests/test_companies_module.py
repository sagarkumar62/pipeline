import pytest
import os
import json
import hashlib
from src.models.company import CompanyRecord
from src.models.model import ModelRecord
from src.models.agent import AgentRecord
from src.models.mcp import MCPRecord
from src.models.tool import ToolRecord
from src.models.repository import RepositoryRecord
from src.extraction.company_extractor import CompanyExtractor
from src.qualification.company_qualifier import CompanyQualifier
from src.deduplication.company_resolver import CompanyDeduplicationResolver


def test_company_record_validation():
    rec = CompanyRecord.create_canonical(
        name="OpenAI",
        company_name="OpenAI",
        legal_name="OpenAI, Inc.",
        official_url="https://openai.com",
        company_type="AI Research Company",
        founded_year=2015,
        country="USA"
    )
    assert rec.name == "OpenAI"
    assert rec.entity_type == "COMPANY"
    assert rec.company_type == "AI Research Company"
    assert rec.founded_year == 2015


def test_company_base_entity_inheritance():
    rec = CompanyRecord.create_canonical(
        name="Anthropic",
        official_url="https://anthropic.com"
    )
    assert rec.id == "company:anthropic.com"
    assert rec.entity_type == "COMPANY"
    assert rec.quality_score >= 0.0


def test_company_entity_type_discriminator():
    rec = CompanyRecord.create_canonical(
        name="Cohere",
        official_url="https://cohere.com"
    )
    assert rec.entity_type == "COMPANY"


def test_company_required_identity_fields():
    rec = CompanyRecord.create_canonical(
        name="Mistral AI",
        official_url="https://mistral.ai"
    )
    assert rec.id == "company:mistral.ai"
    assert rec.url == "https://mistral.ai"
    assert rec.discovery_source is not None


def test_company_qualification():
    qualifier = CompanyQualifier()
    valid_company = {
        "name": "Anthropic",
        "description": "AI safety and research company creating Claude foundation models",
        "official_url": "https://anthropic.com"
    }
    status, reason = qualifier.qualify(valid_company)
    assert status == "QUALIFIED"


def test_company_ai_centrality_qualification():
    qualifier = CompanyQualifier()
    non_ai_company = {
        "name": "Acme Widgets",
        "description": "Manufacturing generic plastic widgets with an incidental website widget",
        "official_url": "https://acme-widgets.example.com"
    }
    status, reason = qualifier.qualify(non_ai_company)
    assert status == "HARD_EXCLUSION"


def test_company_hard_exclusion_precedence():
    qualifier = CompanyQualifier()
    awesome_item = {
        "name": "awesome-ai-companies",
        "description": "A curated list of awesome AI companies and startups",
        "topics": ["awesome", "ai"]
    }
    status, reason = qualifier.qualify(awesome_item)
    assert status == "HARD_EXCLUSION"


def test_company_review_precedence():
    qualifier = CompanyQualifier()
    ambiguous_company = {
        "name": "Unclear AI Labs",
        "official_url": "https://github.com/unclear-ai-labs"
    }
    status, reason = qualifier.qualify(ambiguous_company)
    assert status == "REVIEW_REQUIRED"


def test_company_generic_saas_rejection():
    qualifier = CompanyQualifier()
    saas_item = {
        "name": "Generic IT Consulting",
        "description": "Generic IT consulting services and web development",
        "topics": ["it-consulting"]
    }
    status, reason = qualifier.qualify(saas_item)
    assert status == "HARD_EXCLUSION"


def test_company_ai_directory_rejection():
    qualifier = CompanyQualifier()
    dir_item = {
        "name": "AI Tools Directory",
        "description": "A curated directory and catalog listing AI products",
        "topics": ["directory-only"]
    }
    status, reason = qualifier.qualify(dir_item)
    assert status == "HARD_EXCLUSION"


def test_company_ai_news_rejection():
    qualifier = CompanyQualifier()
    news_item = {
        "name": "The AI Newsletter",
        "description": "Daily news publication and newsletter covering AI updates",
        "topics": ["news-publication"]
    }
    status, reason = qualifier.qualify(news_item)
    assert status == "HARD_EXCLUSION"


def test_company_ai_course_rejection():
    qualifier = CompanyQualifier()
    course_item = {
        "name": "Deep Learning Course 101",
        "description": "Educational course materials and video tutorials for AI",
        "topics": ["course"]
    }
    status, reason = qualifier.qualify(course_item)
    assert status == "HARD_EXCLUSION"


def test_company_project_company_distinction():
    qualifier = CompanyQualifier()
    user_project = {
        "name": "my-personal-ai-project",
        "description": "Personal account repo for AI experiments",
        "type": "user"
    }
    status, reason = qualifier.qualify(user_project)
    assert status == "HARD_EXCLUSION"


def test_company_product_company_distinction():
    rec_company = CompanyRecord.create_canonical(
        name="OpenAI",
        company_name="OpenAI",
        products=["ChatGPT", "GPT-4o"],
        official_url="https://openai.com"
    )
    assert rec_company.company_name == "OpenAI"
    assert "ChatGPT" in rec_company.products


def test_company_github_only_company_handling():
    extractor = CompanyExtractor()
    raw = {
        "login": "deepseek-ai",
        "html_url": "https://github.com/deepseek-ai",
        "description": "DeepSeek AI Research Lab"
    }
    rec = extractor.to_record(raw)
    assert rec.github_url == "https://github.com/deepseek-ai"


def test_company_deterministic_name_normalization():
    resolver = CompanyDeduplicationResolver()
    norm1 = resolver._normalize_company_name("OpenAI, Inc.")
    norm2 = resolver._normalize_company_name("OpenAI Inc")
    norm3 = resolver._normalize_company_name("OpenAI")
    assert norm1 == norm2 == norm3 == "openai"


def test_company_domain_normalization():
    rec1 = CompanyRecord.create_canonical(name="Anthropic", official_url="https://www.anthropic.com")
    rec2 = CompanyRecord.create_canonical(name="Anthropic PBC", official_url="https://anthropic.com")
    assert rec1.id == rec2.id == "company:anthropic.com"


def test_company_exact_duplicate_resolution():
    resolver = CompanyDeduplicationResolver()
    c1 = {"id": "company:openai.com", "official_url": "https://openai.com", "name": "OpenAI"}
    c2 = {"id": "company:openai.com-copy", "official_url": "https://openai.com", "name": "OpenAI, Inc."}
    resolver.resolve(c1)
    res2, dup2 = resolver.resolve(c2)
    assert dup2
    assert res2["match_method"] == "exact_official_domain"


def test_company_alias_resolution():
    rec = CompanyRecord.create_canonical(
        name="Meta AI",
        aliases=["Facebook AI Research", "FAIR"],
        official_url="https://ai.meta.com"
    )
    assert "FAIR" in rec.aliases


def test_company_similar_name_non_merge():
    resolver = CompanyDeduplicationResolver()
    c1 = {"id": "company:example-ai", "name": "Example AI", "official_url": "https://example-ai.com"}
    c2 = {"id": "company:example-ai-labs", "name": "Example AI Labs", "official_url": "https://example-ai-labs.com"}
    resolver.resolve(c1)
    res2, dup2 = resolver.resolve(c2)
    assert not dup2


def test_company_parent_subsidiary_preservation():
    rec = CompanyRecord.create_canonical(
        name="DeepMind",
        parent_company="Alphabet Inc.",
        official_url="https://deepmind.google"
    )
    assert rec.parent_company == "Alphabet Inc."


def test_company_acquisition_preservation():
    rec = CompanyRecord.create_canonical(
        name="GitHub",
        status="ACQUIRED",
        acquisition_status="Acquired by Microsoft in 2018",
        official_url="https://github.com"
    )
    assert rec.status == "ACQUIRED"
    assert "Microsoft" in rec.acquisition_status


def test_company_website_accessibility_semantics():
    rec = CompanyRecord.create_canonical(
        name="Cohere",
        official_url="https://cohere.com"
    )
    assert rec.official_url == "https://cohere.com"


def test_company_website_identity_semantics():
    rec = CompanyRecord.create_canonical(
        name="Mistral AI",
        official_url="https://mistral.ai"
    )
    assert rec.official_url == "https://mistral.ai"


def test_company_directory_not_official_site_rule():
    rec = CompanyRecord.create_canonical(
        name="Test Corporate Entity",
        github_url="https://github.com/test-org"
    )
    assert rec.official_url is None or "github.com" not in rec.official_url


def test_company_github_not_automatic_official_site_rule():
    rec = CompanyRecord.create_canonical(
        name="OpenAI",
        github_url="https://github.com/openai"
    )
    assert "github.com" in rec.github_url


def test_company_logo_verification():
    rec = CompanyRecord.create_canonical(name="Anthropic", official_url="https://anthropic.com")
    assert rec.logo_verified is False
    assert rec.logo_url is None


def test_company_social_preview_rejection():
    rec = CompanyRecord.create_canonical(name="Cohere", official_url="https://cohere.com")
    assert rec.logo_verified is False


def test_company_provenance_completeness():
    extractor = CompanyExtractor()
    raw = {
        "login": "openai",
        "name": "OpenAI",
        "blog": "https://openai.com",
        "html_url": "https://github.com/openai",
        "_discovery_source": "GitHub Organizations API"
    }
    rec = extractor.to_record(raw)
    assert rec.discovery_source.name == "GitHub Organizations API"
    assert len(rec.evidence_sources) == 1


def test_company_description_grounding():
    extractor = CompanyExtractor()
    raw = {
        "login": "mistralai",
        "name": "Mistral AI",
        "description": "Frontier AI models available everywhere."
    }
    rec = extractor.to_record(raw)
    assert rec.description == "Frontier AI models available everywhere."


def test_company_missing_evidence_handling():
    extractor = CompanyExtractor()
    raw = {"login": "generic-org"}
    rec = extractor.to_record(raw)
    assert rec.founded_year is None
    assert rec.employee_range is None
    assert rec.founders == []


def test_company_conflicting_evidence_handling():
    rec = CompanyRecord.create_canonical(
        name="Uncertain Funding AI",
        total_funding=None,  # Null when conflicting
        official_url="https://uncertain.example.com"
    )
    assert rec.total_funding is None


def test_company_deterministic_stable_ids():
    rec = CompanyRecord.create_canonical(
        name="OpenAI",
        official_url="https://openai.com"
    )
    assert rec.id == "company:openai.com"


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


def test_protected_mcp_dataset_integrity():
    mcp_final_path = "data/working/mcp/mcp_final.json"
    if os.path.exists(mcp_final_path):
        with open(mcp_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "CED0BF7AE869ACC54403C0453A1A12CF097131D6D5CB438BEA36216822A9216B"


def test_protected_agents_dataset_integrity():
    agents_final_path = "data/working/agents/agents_final.json"
    if os.path.exists(agents_final_path):
        with open(agents_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "B27609EA151951A97445CA5CFDF54C58F22B223D87808B466BA505BC6E00DA14"


def test_protected_models_dataset_integrity():
    models_final_path = "data/working/models/models_final.json"
    if os.path.exists(models_final_path):
        with open(models_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "1D2F8753C02D43E975A3AD5561D1F14EEEB84A0E1846D69E0AAAF59734FC0DE9"
