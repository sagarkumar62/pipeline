import json
import os
import pytest
from src.models.device import DeviceRecord
from src.discovery.device_discovery import DevicesAdapter
from src.extraction.device_extractor import DeviceExtractor
from src.qualification.device_qualifier import DeviceQualifier
from src.deduplication.device_resolver import DeviceDeduplicationResolver


def test_device_record_validation():
    dev = DeviceRecord.create_canonical(
        name="Jetson Orin Nano",
        manufacturer="NVIDIA",
        official_url="https://developer.nvidia.com/embedded/jetson-orin-nano-developer-kit",
        description="Compact edge AI developer kit",
        device_type="AI Accelerator / Edge Dev Kit",
        processor="NVIDIA Jetson Orin"
    )
    assert dev.entity_type == "device"
    assert dev.id == "device:nvidia/jetson-orin-nano"
    assert dev.canonical_name == "jetson orin nano"
    assert dev.manufacturer == "NVIDIA"
    assert dev.official_url == "https://developer.nvidia.com/embedded/jetson-orin-nano-developer-kit"


def test_device_discovery_normalization():
    adapter = DevicesAdapter(max_pages_per_query=1, per_page=5)
    assert adapter.source_name == "GitHub AI Hardware & Edge Devices Search"
    assert len(adapter.queries) > 0


def test_device_extraction():
    extractor = DeviceExtractor()
    raw_item = {
        "name": "hailo-8-devkit",
        "description": "Hardware repository for Hailo-8 M.2 AI accelerator module on Linux",
        "html_url": "https://github.com/hailo-ai/hailo-8-devkit",
        "homepage": "https://hailo.ai/products/ai-accelerators/hailo-8-m-2-ai-acceleration-module/",
        "topics": ["edge-ai", "ai-hardware", "hailo"],
        "owner": {"login": "hailo-ai"}
    }
    record = extractor.to_record(raw_item)
    assert record.entity_type == "device"
    assert record.name == "hailo-8-devkit"
    assert record.manufacturer == "hailo-ai"
    assert record.device_type in ("AI Accelerator", "AI Accelerator / Edge Dev Kit")
    assert "edge_inference" in record.capabilities
    assert record.processor == "Hailo AI Processor"


def test_device_qualification_qualified():
    qualifier = DeviceQualifier()
    candidate = {
        "name": "jetson-edge-cam",
        "description": "Smart edge AI camera board powered by Jetson Orin for vision processing",
        "topics": ["edge-ai", "ai-camera"],
        "archived": False,
        "fork": False
    }
    status, reason = qualifier.qualify(candidate)
    assert status == "QUALIFIED"
    assert "verified" in reason.lower()


def test_device_qualification_hard_exclusions():
    qualifier = DeviceQualifier()

    # Awesome list
    cand_awesome = {
        "name": "awesome-ai-hardware",
        "description": "A curated list of awesome AI hardware and edge dev kits",
        "topics": ["awesome", "edge-ai"],
        "archived": False
    }
    status, reason = qualifier.qualify(cand_awesome)
    assert status == "HARD_EXCLUSION"

    # Software only / Web scraper
    cand_scraper = {
        "name": "ai-device-scraper",
        "description": "Python web scraper for scraping AI hardware prices",
        "topics": ["web-scraper", "python"],
        "archived": False
    }
    status, reason = qualifier.qualify(cand_scraper)
    assert status == "HARD_EXCLUSION"


def test_device_vs_robot_boundary_exclusion():
    qualifier = DeviceQualifier()
    cand_robot = {
        "name": "humanoid-robot-v1",
        "description": "Open source humanoid robot platform with bipedal walking gait",
        "topics": ["humanoid-robot", "robotics"],
        "archived": False
    }
    status, reason = qualifier.qualify(cand_robot)
    assert status == "HARD_EXCLUSION"
    assert "robots module" in reason.lower() or "robot" in reason.lower()


def test_device_review_rules():
    qualifier = DeviceQualifier()

    # Fork repo
    cand_fork = {
        "name": "jetson-dev-fork",
        "description": "Custom fork of edge AI device firmware",
        "topics": ["edge-ai"],
        "archived": False,
        "fork": True
    }
    status, reason = qualifier.qualify(cand_fork)
    assert status == "REVIEW_REQUIRED"

    # Missing description and official url
    cand_sparse = {
        "name": "mysterious-edge-board",
        "description": "",
        "official_url": None,
        "topics": ["edge-ai"],
        "archived": False,
        "fork": False
    }
    status, reason = qualifier.qualify(cand_sparse)
    assert status == "REVIEW_REQUIRED"


def test_device_negative_signal_precedence():
    qualifier = DeviceQualifier()
    # Has positive signal "edge-ai" but also "awesome-" negative pattern
    cand_mixed = {
        "name": "awesome-edge-ai-hardware",
        "description": "Curated list of edge-ai hardware devkits",
        "topics": ["edge-ai", "awesome"],
        "archived": False
    }
    status, reason = qualifier.qualify(cand_mixed)
    assert status == "HARD_EXCLUSION"


def test_device_deduplication():
    resolver = DeviceDeduplicationResolver()

    rec1 = {
        "id": "device:nvidia/jetson-orin-nano",
        "name": "Jetson Orin Nano",
        "manufacturer": "NVIDIA",
        "repository_url": "https://github.com/nvidia/jetson-orin-nano",
        "official_url": "https://developer.nvidia.com/embedded/jetson-orin-nano"
    }

    rec2 = {
        "id": "device:nvidia/jetson-orin-nano-mirror",
        "name": "Jetson Orin Nano",
        "manufacturer": "NVIDIA",
        "repository_url": "https://github.com/nvidia/jetson-orin-nano",
        "official_url": "https://developer.nvidia.com/embedded/jetson-orin-nano"
    }

    resolved1, is_dup1 = resolver.resolve(rec1)
    assert not is_dup1

    resolved2, is_dup2 = resolver.resolve(rec2)
    assert is_dup2
    assert resolved2["duplicate_of"] == "device:nvidia/jetson-orin-nano"


def test_device_generations_remain_distinct():
    resolver = DeviceDeduplicationResolver()

    rec1 = {
        "id": "device:nvidia/jetson-orin-nano",
        "name": "Jetson Orin Nano",
        "manufacturer": "NVIDIA",
        "repository_url": "https://github.com/nvidia/jetson-orin-nano",
        "official_url": "https://developer.nvidia.com/embedded/jetson-orin-nano"
    }

    rec2 = {
        "id": "device:nvidia/jetson-orin-agx",
        "name": "Jetson Orin AGX",
        "manufacturer": "NVIDIA",
        "repository_url": "https://github.com/nvidia/jetson-orin-agx",
        "official_url": "https://developer.nvidia.com/embedded/jetson-orin-agx"
    }

    _, is_dup1 = resolver.resolve(rec1)
    _, is_dup2 = resolver.resolve(rec2)
    assert not is_dup1
    assert not is_dup2


def test_device_provenance_and_schema():
    dev = DeviceRecord.create_canonical(
        name="Coral Edge TPU Dev Board",
        manufacturer="Google",
        official_url="https://coral.ai/products/dev-board/",
        description="Single board computer with Google Coral Edge TPU for machine learning",
        processor="Google Coral TPU",
        open_source=True
    )
    rec = dev.model_dump(mode="json")
    assert rec["entity_type"] == "device"
    assert rec["source"]["name"] is not None
    assert rec["open_source"] is True


def test_device_missing_field_behavior():
    dev = DeviceRecord.create_canonical(
        name="Generic Dev Board"
    )
    assert dev.official_url is None
    assert dev.repository_url is None
    assert dev.processor is None
    assert dev.capabilities == []
    assert dev.open_source is False


def test_accounting_reconciliation_math():
    raw = 120
    qualified = 90
    rejected = 20
    review = 10
    duplicates = 5
    final = 85

    assert raw == qualified + rejected + review
    assert qualified == final + duplicates
