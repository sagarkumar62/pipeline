from typing import Dict, Any
from src.extraction.base import BaseExtractor
from src.models.robot import RobotRecord
from src.models.base import DiscoverySource, EvidenceSource


class RobotExtractor(BaseExtractor):
    """
    Extractor for Robot entities from GitHub Robotics Search and discovery sources.
    Extracts structured Robot metadata fields while preserving provenance.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str = "GitHub Robotics Search") -> Dict[str, Any]:
        owner_info = raw_item.get("owner")
        if isinstance(owner_info, dict):
            owner = owner_info.get("login", "")
        else:
            owner = str(owner_info or "").strip()

        name = (raw_item.get("name") or "").strip()
        html_url = raw_item.get("html_url") or raw_item.get("url") or f"https://github.com/{owner}/{name}"

        license_info = raw_item.get("license")
        license_spdx = None
        if isinstance(license_info, dict):
            license_spdx = license_info.get("spdx_id") or license_info.get("name")
        elif isinstance(license_info, str):
            license_spdx = license_info

        query = raw_item.get("_discovery_query") or "topic:robotics"
        src_name = raw_item.get("_discovery_source") or source_name

        topics = [t.lower() for t in (raw_item.get("topics") or [])]
        desc = (raw_item.get("description") or "").lower()
        name_lower = name.lower()
        combined_text = f"{name_lower} {desc} {' '.join(topics)}"

        # Determine robot type based on explicit evidence
        robot_type = "Physical Robot Platform"
        physical_form = "Robotic System"
        if any(k in combined_text for k in ["humanoid", "bipedal"]):
            robot_type = "Humanoid Robot"
            physical_form = "Bipedal Humanoid"
        elif any(k in combined_text for k in ["quadruped", "dog", "spot", "unitree"]):
            robot_type = "Quadruped Robot"
            physical_form = "Quadrupedal"
        elif any(k in combined_text for k in ["arm", "manipulator", "kuka", "ur5", "ur10"]):
            robot_type = "Industrial Arm"
            physical_form = "Articulated Arm"
        elif any(k in combined_text for k in ["mobile", "amr", "agv", "rover", "wheeled"]):
            robot_type = "Mobile Robot (AMR)"
            physical_form = "Wheeled Mobile"
        elif any(k in combined_text for k in ["drone", "aerial", "uav"]):
            robot_type = "Autonomous Drone"
            physical_form = "Aerial Quadcopter"

        # Capabilities derived strictly from evidence
        capabilities = []
        if any(k in combined_text for k in ["bipedal", "walk", "walking", "gait"]):
            capabilities.append("bipedal_locomotion")
        if any(k in combined_text for k in ["quadruped", "trot"]):
            capabilities.append("quadrupedal_locomotion")
        if any(k in combined_text for k in ["arm", "grasp", "grasping", "manipulation", "gripper"]):
            capabilities.append("manipulation")
        if any(k in combined_text for k in ["nav", "navigation", "slam", "autonomous-navigation"]):
            capabilities.append("autonomous_navigation")

        # ROS support
        ros_supported = any(k in combined_text for k in ["ros", "ros2", "ros-robot"])

        # Open source hardware
        open_hardware = any(k in combined_text for k in ["open-hardware", "cad", "printables", "3d-printed"])

        discovery_src = DiscoverySource(
            name=src_name,
            url=f"https://api.github.com/search/repositories?q={query}",
            source_type="API",
            source_trust_level="HIGH"
        )

        evidence_src = EvidenceSource(
            url=html_url,
            source_type="GITHUB_REPOSITORY",
            trust_level="HIGH",
            evidence_type="CODE_REPOSITORY"
        )

        extracted = {
            "name": name,
            "manufacturer": owner,
            "url": raw_item.get("homepage") or html_url,
            "repository_url": html_url,
            "official_url": raw_item.get("homepage"),
            "description": raw_item.get("description"),
            "categories": ["Robots", "Robotics", "Hardware"],
            "robot_type": robot_type,
            "physical_form": physical_form,
            "capabilities": capabilities,
            "ros_supported": ros_supported,
            "open_source_hardware": open_hardware,
            "commercial_status": "Commercial Product" if raw_item.get("homepage") else "Research Platform",
            "discovery_source": discovery_src,
            "source": discovery_src,
            "evidence_sources": [evidence_src]
        }
        return extracted

    def to_record(self, raw_item: Dict[str, Any], source_name: str = "GitHub Robotics Search") -> RobotRecord:
        extracted = self.extract(raw_item, source_name)
        return RobotRecord.create_canonical(**extracted)
