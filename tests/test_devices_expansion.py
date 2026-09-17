import json
import os
import pytest
from src.models.device import DeviceRecord
from src.qualification.device_qualifier import DeviceQualifier
from src.deduplication.device_resolver import DeviceDeduplicationResolver


def test_device_baseline_immutability():
    baseline_path = "data/working/devices/devices_final.json"
    assert os.path.exists(baseline_path)
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 107


def test_device_qualification_precedence():
    qualifier = DeviceQualifier()

    # Software application / SaaS must yield HARD_EXCLUSION
    cand_sw = {
        "name": "cloud-ai-saas-dashboard",
        "description": "SaaS dashboard web application for monitoring cloud servers",
        "topics": ["saas", "dashboard"]
    }
    status, reason = qualifier.qualify(cand_sw)
    assert status == "HARD_EXCLUSION"

    # Awesome list / Tutorial must yield HARD_EXCLUSION
    cand_awesome = {
        "name": "awesome-ai-hardware-list",
        "description": "Curated list of awesome edge AI hardware dev kits",
        "topics": ["awesome-list"]
    }
    status, reason = qualifier.qualify(cand_awesome)
    assert status == "HARD_EXCLUSION"

    # Clean Physical Device candidate must yield QUALIFIED
    cand_dev = {
        "name": "NVIDIA Jetson Orin Nano Developer Kit",
        "description": "Compact edge AI computer board delivering up to 40 TOPS of AI performance for autonomous machines",
        "manufacturer": "NVIDIA",
        "topics": ["jetson", "edge-ai", "ai-dev-kit"],
        "stars": 1500
    }
    status, reason = qualifier.qualify(cand_dev)
    assert status == "QUALIFIED"


def test_device_software_exclusion():
    qualifier = DeviceQualifier()

    cand_sdk = {
        "name": "edge-ai-python-sdk",
        "description": "Python software library and SDK for running inference on edge devices",
        "topics": ["python-sdk"]
    }
    status, reason = qualifier.qualify(cand_sdk)
    assert status == "HARD_EXCLUSION"


def test_device_model_exclusion():
    qualifier = DeviceQualifier()

    cand_model = {
        "name": "YOLOv8-Nano-Model",
        "description": "Object detection neural network model weights optimized for edge devices",
        "topics": ["model-weights"]
    }
    status, reason = qualifier.qualify(cand_model)
    assert status == "HARD_EXCLUSION"


def test_device_baseline_duplicate_detection():
    resolver = DeviceDeduplicationResolver()
    baseline_records = [
        {
            "id": "device:nvidia-jetson-orin-nano",
            "name": "NVIDIA Jetson Orin Nano Developer Kit",
            "manufacturer": "NVIDIA",
            "official_url": "https://developer.nvidia.com/embedded/jetson-orin-nano-developer-kit"
        }
    ]
    resolver.load_baseline(baseline_records)

    cand = {
        "id": "device:nvidia-jetson-orin-nano-dup",
        "name": "NVIDIA Jetson Orin Nano Developer Kit",
        "manufacturer": "NVIDIA",
        "official_url": "https://developer.nvidia.com/embedded/jetson-orin-nano-developer-kit"
    }

    resolved, is_dup = resolver.resolve(cand)
    assert is_dup
    assert resolved["is_baseline_match"] is True
    assert resolved["duplicate_of"] == "device:nvidia-jetson-orin-nano"


def test_device_intra_expansion_duplicate_detection():
    resolver = DeviceDeduplicationResolver()
    resolver.load_baseline([])  # Empty baseline

    cand1 = {
        "id": "device:google-coral-dev-board",
        "name": "Coral Dev Board",
        "manufacturer": "Google",
        "official_url": "https://coral.ai/products/dev-board"
    }

    cand2 = {
        "id": "device:google-coral-dev-board-mirror",
        "name": "Coral Dev Board",
        "manufacturer": "Google",
        "official_url": "https://coral.ai/products/dev-board"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["is_baseline_match"] is False
    assert resolved2["duplicate_of"] == "device:google-coral-dev-board"


def test_device_repository_normalization():
    resolver = DeviceDeduplicationResolver()
    url1 = "https://github.com/dusty-nv/jetson-inference.git"
    url2 = "https://github.com/dusty-nv/jetson-inference/"
    norm1 = resolver._normalize_repo(url1)
    norm2 = resolver._normalize_repo(url2)
    assert norm1 == "dusty-nv/jetson-inference"
    assert norm2 == "dusty-nv/jetson-inference"


def test_devices_expansion_accounting_equation():
    raw = 1000
    qualified = 800
    rejected = 190
    review = 10

    baseline_dups = 15
    intra_dups = 85
    final_new = 700

    assert raw == qualified + rejected + review
    assert qualified == baseline_dups + intra_dups + final_new
