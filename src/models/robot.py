from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator
from src.utils.urls import normalize_url, extract_domain
from src.models.base import (
    BaseEntity,
    DiscoverySource,
    SourceMetadata,
    EvidenceSource,
    VerificationEvidence,
    VerificationResult,
    QualityMetrics,
)


class RobotRecord(BaseEntity):
    """
    Canonical Pydantic model for a Robot entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='robot'.
    
    A Robot represents a real physical robotic system, robot platform, humanoid robot,
    industrial robot, service robot, mobile robot, or quadruped. Software-only bots,
    chatbots, AI agents, and simulators are excluded from canonical Robot records.
    """
    entity_type: Literal["robot"] = "robot"

    # Robot Specific Metadata Fields
    manufacturer: Optional[str] = Field(None, description="Manufacturer organization e.g. Boston Dynamics, Unitree, Tesla, Figure")
    country: Optional[str] = Field(None, description="Country of manufacture/origin e.g. USA, China, Japan, Germany")
    release_year: Optional[int] = Field(None, description="Year of public release or reveal e.g. 2023")
    robot_type: Optional[str] = Field(None, description="E.g. Humanoid, Quadruped, Industrial Arm, Mobile Robot (AMR), Service Robot")
    physical_form: Optional[str] = Field(None, description="Form factor e.g. Bipedal Humanoid, Quadrupedal, Articulated Arm, Wheeled Mobile")
    capabilities: List[str] = Field(default_factory=list, description="Physical capabilities e.g. bipedal_locomotion, manipulation, autonomous_navigation, grasping")
    use_cases: List[str] = Field(default_factory=list, description="Target application domains e.g. Logistics, Manufacturing, Inspection, Research")
    autonomy_level: Optional[str] = Field(None, description="Autonomy classification e.g. Fully Autonomous, Semi-Autonomous, Teleoperated")
    sensors: List[str] = Field(default_factory=list, description="Integrated sensor types e.g. LiDAR, Stereo Cameras, IMU, Force Sensors")
    actuators: List[str] = Field(default_factory=list, description="Actuator types e.g. Electric Servo Motors, Hydraulic Actuators")
    hardware_architecture: Optional[str] = Field(None, description="Compute architecture e.g. NVIDIA Jetson, Intel NUC, Custom Compute")
    software_stack: Optional[str] = Field(None, description="Robot software ecosystem e.g. ROS 2, Custom RTOS, NVIDIA Isaac")
    operating_environment: Optional[str] = Field(None, description="Environment suitability e.g. Indoor Industrial, Outdoor Rough Terrain, Universal")
    payload_capacity: Optional[str] = Field(None, description="Maximum payload capacity e.g. 25 kg")
    battery_life: Optional[str] = Field(None, description="Operating runtime per charge e.g. 90 minutes")
    open_source_hardware: bool = Field(False, description="Whether physical hardware schematics/CAD are open source")
    ros_supported: bool = Field(False, description="Whether official ROS / ROS 2 drivers are supported")
    commercial_status: Optional[str] = Field(None, description="Status e.g. Commercial Product, Research Prototype, Concept")
    official_url: Optional[str] = Field(None, description="Official manufacturer landing page or product site")
    repository_url: Optional[str] = Field(None, description="Open source code or driver repository URL")

    @field_validator("official_url", mode="before")
    @classmethod
    def validate_robot_official_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        return norm if norm else None

    @field_validator("repository_url", mode="before")
    @classmethod
    def validate_robot_repo_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        if norm.startswith("http://github.com"):
            norm = "https://github.com" + norm[17:]
        return norm.lower() if "github.com" in norm.lower() else norm

    @classmethod
    def create_canonical(cls, **kwargs) -> "RobotRecord":
        """
        Creates a RobotRecord with stable deterministic ID: robot:<key>
        """
        name = (kwargs.get("name") or "").strip()
        mfg = (kwargs.get("manufacturer") or "").strip().lower()
        repo_url = kwargs.get("repository_url") or ""
        official_url = kwargs.get("official_url") or kwargs.get("url") or ""

        if repo_url:
            repo_url = normalize_url(repo_url)
            kwargs["repository_url"] = repo_url

        if official_url:
            official_url = normalize_url(official_url)
            kwargs["official_url"] = official_url

        if not kwargs.get("canonical_name"):
            kwargs["canonical_name"] = name.lower()

        # Deterministic ID key logic
        if mfg and name:
            clean_m = mfg.replace(" ", "-")
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"robot:{clean_m}/{clean_n}"
        elif repo_url and "github.com/" in repo_url.lower():
            clean = repo_url.lower().replace("https://github.com/", "").replace("http://github.com/", "").rstrip("/")
            kwargs["id"] = f"robot:{clean}"
        else:
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"robot:{clean_n}"

        # Ensure primary URL field is set
        if not kwargs.get("url"):
            if official_url:
                kwargs["url"] = official_url
            elif repo_url:
                kwargs["url"] = repo_url
            else:
                clean_n = name.lower().replace(" ", "-")
                kwargs["url"] = f"https://ai-orbit.org/robots/{clean_n}"

        # Ensure discovery source
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "GitHub Robotics & Robot Discovery"),
                    url=kwargs.get("url", ""),
                    source_type="API",
                    source_trust_level="HIGH"
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        return cls(**kwargs)
