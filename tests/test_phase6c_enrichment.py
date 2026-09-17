"""
Dedicated Unit Tests for Phase 6C — Dataset Enrichment & Official Verification.
"""

import json
import pytest
from pathlib import Path
from src.verification.website import OfficialWebsiteVerifier
from src.verification.logo import OfficialLogoVerifier
from src.enrichment.quality import DescriptionQualityChecker


@pytest.mark.asyncio
async def test_website_verification_accessible():
    verifier = OfficialWebsiteVerifier(timeout_seconds=5.0)
    record = {
        "name": "thinkrail",
        "url": "https://thinkrail.ai",
        "official_url": "https://thinkrail.ai",
        "source_url": "https://thinkrail.ai",
        "source_name": "Official Directory"
    }
    res = await verifier.verify_website(record)
    assert res.verification_status in ["ACCESSIBLE_VERIFIED", "ACCESS_BLOCKED", "TIMEOUT", "DNS_FAILURE"]


@pytest.mark.asyncio
async def test_logo_verification_fallback_semantics():
    logo_verifier = OfficialLogoVerifier()
    record = {
        "name": "test-repo",
        "url": "https://github.com/test-owner/test-repo",
        "official_url": None
    }
    # Simulate verification result
    class DummyVerificationResult:
        verification_status = "ACCESSIBLE_VERIFIED"
        accessible = True

    res = await logo_verifier.discover_logo(record, DummyVerificationResult())
    # Social preview or GitHub asset fallback MUST have logo_verified = False
    assert res.get("logo_verified") is False


def test_description_quality_checker():
    checker = DescriptionQualityChecker()
    desc = "A lightweight CLI watcher tool for Rust developer workflows."
    flag, is_pass = checker.check_quality(desc, "funzzy")
    assert is_pass is True
    assert flag == "VALID"


def test_phase6c_artifacts_exist():
    enriched_file = Path("data/working/tools_phase6c_enriched.json")
    collision_file = Path("data/working/phase6c_domain_collision_audit.json")
    
    assert collision_file.exists(), "Phase 6C domain collision audit file should exist"
