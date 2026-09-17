import pytest
from src.models.tool import VerificationResult, VerificationEvidence
from src.validation.validator import ValidationGate


def test_validation_gate_accessible_verified():
    gate = ValidationGate()
    record = {
        "name": "Test Tool",
        "url": "https://test.com",
        "source_name": "Official Seed",
        "source_url": "https://test.com",
        "source_trust_level": "HIGH",
        "description": "This is a valid test description long enough.",
        "description_grounded": True,
        "categories": ["Developer Tools"]
    }
    
    vr = VerificationResult(
        verification_status="ACCESSIBLE_VERIFIED",
        accessible=True,
        official_domain_match=True
    )
    
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is True
    assert reason is None
    assert record["quality_score"] > 0
    assert record["verification_status"] == "ACCESSIBLE_VERIFIED"


def test_validation_gate_access_blocked_with_high_trust_source():
    gate = ValidationGate()
    record = {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "source_name": "GitHub API",
        "source_url": "https://github.com/openai/chatgpt",
        "source_trust_level": "HIGH",
        "description": "Conversational AI assistant powered by OpenAI GPT-4o models.",
        "description_grounded": True,
        "categories": ["AI Assistants"]
    }
    
    vr = VerificationResult(
        verification_status="ACCESS_BLOCKED",
        http_status=403,
        accessible=False,
        official_domain_match=True,
        reason="HTTP 403"
    )
    vr.evidence.append(VerificationEvidence(
        type="DOMAIN_MATCH", source="GitHub API", value="Match", result=True
    ))
    
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is True
    assert record["verification_status"] == "ACCESS_BLOCKED"


def test_validation_gate_access_blocked_with_medium_trust_rejected():
    gate = ValidationGate()
    record = {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "source_name": "Curated Seed Directory",
        "source_url": "https://example.com/seed",
        "source_trust_level": "MEDIUM",
        "description": "Conversational AI assistant powered by OpenAI GPT-4o models.",
        "description_grounded": True,
        "categories": ["AI Assistants"]
    }
    
    vr = VerificationResult(
        verification_status="ACCESS_BLOCKED",
        http_status=403,
        accessible=False,
        official_domain_match=True,
        reason="HTTP 403"
    )
    
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is False
    assert "insufficient source trust" in reason.lower()


def test_validation_gate_rejects_ungrounded_description():
    gate = ValidationGate()
    record = {
        "name": "Test Tool",
        "url": "https://test.com",
        "source_name": "Official Seed",
        "source_url": "https://test.com",
        "source_trust_level": "HIGH",
        "description": "Some generic fabricated text description.",
        "description_grounded": False,  # Not grounded in source
        "categories": ["Developer Tools"]
    }
    
    vr = VerificationResult(
        verification_status="ACCESSIBLE_VERIFIED",
        accessible=True,
        official_domain_match=True
    )
    
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is False
    assert "not grounded" in reason.lower()


def test_validation_gate_rejects_identity_mismatch():
    gate = ValidationGate()
    record = {
        "name": "Fake Tool",
        "url": "https://faketool.com",
        "source_name": "Some Directory",
        "source_url": "https://directory.com/fake",
        "source_trust_level": "LOW",
        "description": "This tool is totally fake and not real.",
        "description_grounded": True,
        "categories": ["Tools"]
    }
    
    vr = VerificationResult(
        verification_status="IDENTITY_MISMATCH",
        accessible=True,
        official_domain_match=False
    )
    
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is False
    assert "Identity Verification Failed" in reason


def test_validation_gate_rejects_missing_description():
    gate = ValidationGate()
    record = {
        "name": "Test Tool",
        "url": "https://test.com",
        "source_name": "Seed",
        "source_url": "https://test.com",
        "source_trust_level": "MEDIUM",
        "description": "",  # Missing desc
        "description_grounded": False,
        "categories": ["Tools"]
    }
    
    vr = VerificationResult(verification_status="ACCESSIBLE_VERIFIED")
    
    is_valid, reason = gate.validate(record, vr)
    assert is_valid is False
    assert "Description missing" in reason
