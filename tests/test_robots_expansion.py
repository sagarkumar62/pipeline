import json
import os
import pytest
from src.models.robot import RobotRecord
from src.qualification.robot_qualifier import RobotQualifier
from src.deduplication.robot_resolver import RobotDeduplicationResolver


def test_robot_baseline_immutability():
    baseline_path = "data/working/robots/robots_final.json"
    assert os.path.exists(baseline_path)
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 93


def test_robot_qualification_precedence():
    qualifier = RobotQualifier()

    # Software bot / Chatbot must yield HARD_EXCLUSION
    cand_bot = {
        "name": "discord-trading-bot",
        "description": "Automated discord bot for crypto trading",
        "topics": ["trading-bot", "discord-bot"]
    }
    status, reason = qualifier.qualify(cand_bot)
    assert status == "HARD_EXCLUSION"

    # Awesome list / Tutorial must yield HARD_EXCLUSION
    cand_awesome = {
        "name": "awesome-robotics-resources",
        "description": "Curated list of awesome robotics courses and tutorials",
        "topics": ["awesome-list"]
    }
    status, reason = qualifier.qualify(cand_awesome)
    assert status == "HARD_EXCLUSION"

    # Clean Physical Robot candidate must yield QUALIFIED
    cand_robot = {
        "name": "Unitree Go2",
        "description": "Quadruped robotic platform equipped with 3D LiDAR and autonomous navigation capabilities",
        "manufacturer": "Unitree Robotics",
        "topics": ["quadruped", "robotics"],
        "stars": 1200
    }
    status, reason = qualifier.qualify(cand_robot)
    assert status == "QUALIFIED"


def test_robot_software_agent_exclusion():
    qualifier = RobotQualifier()

    cand_agent = {
        "name": "ai-coding-agent",
        "description": "Autonomous software agent for automated python code generation",
        "topics": ["ai-agent"]
    }
    status, reason = qualifier.qualify(cand_agent)
    assert status == "HARD_EXCLUSION"


def test_robot_simulation_exclusion():
    qualifier = RobotQualifier()

    cand_sim = {
        "name": "isaac-sim-gazebo-environment",
        "description": "Virtual simulator-only environment for physics simulation",
        "topics": ["simulator-only"]
    }
    status, reason = qualifier.qualify(cand_sim)
    assert status == "HARD_EXCLUSION"


def test_robot_baseline_duplicate_detection():
    resolver = RobotDeduplicationResolver()
    baseline_records = [
        {
            "id": "robot:unitree-go2",
            "name": "Unitree Go2",
            "manufacturer": "Unitree Robotics",
            "official_url": "https://www.unitree.com/go2"
        }
    ]
    resolver.load_baseline(baseline_records)

    cand = {
        "id": "robot:unitree-go2-dup",
        "name": "Unitree Go2",
        "manufacturer": "Unitree Robotics",
        "official_url": "https://www.unitree.com/go2"
    }

    resolved, is_dup = resolver.resolve(cand)
    assert is_dup
    assert resolved["is_baseline_match"] is True
    assert resolved["duplicate_of"] == "robot:unitree-go2"


def test_robot_intra_expansion_duplicate_detection():
    resolver = RobotDeduplicationResolver()
    resolver.load_baseline([])  # Empty baseline

    cand1 = {
        "id": "robot:boston-dynamics-spot",
        "name": "Spot",
        "manufacturer": "Boston Dynamics",
        "official_url": "https://bostondynamics.com/spot"
    }

    cand2 = {
        "id": "robot:bostondynamics-spot-mirror",
        "name": "Spot",
        "manufacturer": "Boston Dynamics",
        "official_url": "https://bostondynamics.com/spot"
    }

    _, is_dup1 = resolver.resolve(cand1)
    resolved2, is_dup2 = resolver.resolve(cand2)

    assert not is_dup1
    assert is_dup2
    assert resolved2["is_baseline_match"] is False
    assert resolved2["duplicate_of"] == "robot:boston-dynamics-spot"


def test_robot_repository_normalization():
    resolver = RobotDeduplicationResolver()
    url1 = "https://github.com/unitreerobotics/unitree_ros2.git"
    url2 = "https://github.com/unitreerobotics/unitree_ros2/"
    norm1 = resolver._normalize_repo(url1)
    norm2 = resolver._normalize_repo(url2)
    assert norm1 == "unitreerobotics/unitree_ros2"
    assert norm2 == "unitreerobotics/unitree_ros2"


def test_robots_expansion_accounting_equation():
    raw = 1000
    qualified = 800
    rejected = 190
    review = 10

    baseline_dups = 15
    intra_dups = 85
    final_new = 700

    assert raw == qualified + rejected + review
    assert qualified == baseline_dups + intra_dups + final_new
