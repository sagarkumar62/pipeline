import pytest
import os
import json
import hashlib
from src.models.robot import RobotRecord
from src.models.company import CompanyRecord
from src.models.model import ModelRecord
from src.models.agent import AgentRecord
from src.models.mcp import MCPRecord
from src.models.tool import ToolRecord
from src.models.repository import RepositoryRecord
from src.extraction.robot_extractor import RobotExtractor
from src.qualification.robot_qualifier import RobotQualifier
from src.deduplication.robot_resolver import RobotDeduplicationResolver


def test_robot_record_validation():
    rec = RobotRecord.create_canonical(
        name="Spot",
        manufacturer="Boston Dynamics",
        official_url="https://bostondynamics.com/products/spot",
        robot_type="Quadruped Robot",
        physical_form="Quadrupedal",
        capabilities=["quadrupedal_locomotion", "autonomous_navigation", "inspection"],
        payload_capacity="14 kg"
    )
    assert rec.name == "Spot"
    assert rec.entity_type == "robot"
    assert rec.manufacturer == "Boston Dynamics"
    assert rec.robot_type == "Quadruped Robot"


def test_robot_entity_type_discriminator():
    rec = RobotRecord.create_canonical(
        name="Optimus Gen 2",
        manufacturer="Tesla",
        official_url="https://tesla.com/optimus"
    )
    assert rec.entity_type == "robot"


def test_robot_required_identity_fields():
    rec = RobotRecord.create_canonical(
        name="Figure 01",
        manufacturer="Figure AI",
        official_url="https://figure.ai"
    )
    assert rec.id == "robot:figure-ai/figure-01"
    assert rec.url == "https://figure.ai"
    assert rec.discovery_source is not None


def test_robot_qualification():
    qualifier = RobotQualifier()
    valid_robot = {
        "name": "Unitree Go2",
        "description": "Quadrupedal robot dog platform with 4D LiDAR for terrain navigation",
        "official_url": "https://unitree.com/go2"
    }
    status, reason = qualifier.qualify(valid_robot)
    assert status == "QUALIFIED"


def test_robot_hard_exclusion_precedence():
    qualifier = RobotQualifier()
    awesome_item = {
        "name": "awesome-robotics",
        "description": "A curated list of awesome robotics tutorials, frameworks, and datasets",
        "topics": ["awesome", "robotics"]
    }
    status, reason = qualifier.qualify(awesome_item)
    assert status == "HARD_EXCLUSION"


def test_robot_software_bot_rejection():
    qualifier = RobotQualifier()
    software_bot = {
        "name": "discord-trading-bot",
        "description": "A python software bot for discord chat auto trading",
        "topics": ["trading-bot"]
    }
    status, reason = qualifier.qualify(software_bot)
    assert status == "HARD_EXCLUSION"


def test_robot_review_precedence():
    qualifier = RobotQualifier()
    fork_robot = {
        "name": "spot-driver-fork",
        "description": "Fork of Boston Dynamics Spot ROS driver",
        "topics": ["ros"],
        "fork": True
    }
    status, reason = qualifier.qualify(fork_robot)
    assert status == "REVIEW_REQUIRED"


def test_robot_deterministic_identity():
    rec = RobotRecord.create_canonical(
        name="Digit",
        manufacturer="Agility Robotics",
        official_url="https://agilityrobotics.com/digit"
    )
    assert rec.id == "robot:agility-robotics/digit"


def test_robot_exact_repository_deduplication():
    resolver = RobotDeduplicationResolver()
    r1 = {"id": "robot:unitree/go1", "repository_url": "https://github.com/unitree/unitree_ros"}
    r2 = {"id": "robot:unitree/go1-copy", "repository_url": "https://github.com/unitree/unitree_ros"}
    resolver.resolve(r1)
    res2, dup2 = resolver.resolve(r2)
    assert dup2
    assert res2["match_method"] == "exact_repository_url"


def test_robot_distinct_generation_preservation():
    resolver = RobotDeduplicationResolver()
    r1 = {"id": "robot:boston-dynamics/atlas-hydraulic", "manufacturer": "boston-dynamics", "name": "atlas-hydraulic"}
    r2 = {"id": "robot:boston-dynamics/atlas-electric", "manufacturer": "boston-dynamics", "name": "atlas-electric"}
    resolver.resolve(r1)
    res2, dup2 = resolver.resolve(r2)
    assert not dup2


def test_robot_provenance_completeness():
    extractor = RobotExtractor()
    raw = {
        "name": "unitree_ros",
        "owner": {"login": "unitreerobotics"},
        "html_url": "https://github.com/unitreerobotics/unitree_ros",
        "description": "ROS 2 simulation and hardware control package for Unitree Quadruped Robots.",
        "_discovery_source": "GitHub Robotics Search"
    }
    rec = extractor.to_record(raw)
    assert rec.discovery_source.name == "GitHub Robotics Search"
    assert len(rec.evidence_sources) == 1


def test_robot_official_website_semantics():
    rec = RobotRecord.create_canonical(
        name="Spot",
        manufacturer="Boston Dynamics",
        official_url="https://bostondynamics.com/spot"
    )
    assert rec.official_url == "https://bostondynamics.com/spot"


def test_robot_github_not_official_website_rule():
    rec = RobotRecord.create_canonical(
        name="Spot ROS Driver",
        repository_url="https://github.com/clearpathrobotics/spot_ros"
    )
    assert "github.com" in rec.repository_url


def test_robot_social_preview_rejection():
    rec = RobotRecord.create_canonical(name="Digit", manufacturer="Agility Robotics")
    assert rec.logo_verified is False
    assert rec.logo_url is None


def test_robot_description_grounding():
    extractor = RobotExtractor()
    raw = {
        "name": "pupper",
        "owner": {"login": "stanford-robotics"},
        "html_url": "https://github.com/stanford-robotics/pupper",
        "description": "Open-source quadruped robot platform."
    }
    rec = extractor.to_record(raw)
    assert rec.description == "Open-source quadruped robot platform."


def test_robot_missing_evidence_handling():
    extractor = RobotExtractor()
    raw = {"name": "generic-robot-arm", "owner": "testuser"}
    rec = extractor.to_record(raw)
    assert rec.payload_capacity is None
    assert rec.battery_life is None
    assert rec.sensors == []


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


def test_protected_companies_dataset_integrity():
    companies_final_path = "data/working/companies/companies_final.json"
    if os.path.exists(companies_final_path):
        with open(companies_final_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest().upper()
        assert h == "112E7B10DEF6123CFAD3EF5DA55DD35B58EC774E45B513E6E6970B2DA0B8B8F4"
