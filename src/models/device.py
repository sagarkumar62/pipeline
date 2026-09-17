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


class DeviceRecord(BaseEntity):
    """
    Canonical Pydantic model for a Device entity in the AI Orbit Ecosystem.
    Distinguished by entity_type='device'.
    
    A Device represents a legitimate physical hardware product, system, AI accelerator,
    AI workstation, edge AI dev kit, AI camera, AI wearable, or physical AI interface relevant to the AI ecosystem.
    Software-only entities, APIs, models, repos, datasets, articles, generic companies, chatbots,
    and robot platforms (which belong to Robots) are excluded.
    """
    entity_type: Literal["device"] = "device"

    # Device Specific Metadata Fields
    manufacturer: Optional[str] = Field(None, description="Manufacturer organization e.g. NVIDIA, Hailo, Google, Raspberry Pi, SiMa.ai, Ampere")
    country: Optional[str] = Field(None, description="Country of manufacture/origin e.g. USA, Israel, UK, Taiwan")
    release_year: Optional[int] = Field(None, description="Year of public release or reveal e.g. 2023")
    device_type: Optional[str] = Field(None, description="Device classification e.g. AI Accelerator, Edge Dev Kit, AI Workstation, AI Camera, AI Wearable, Physical AI Interface")
    physical_form: Optional[str] = Field(None, description="Physical form factor e.g. PCIe Card, Single Board Computer, Standalone Appliance, Smart Wearable, Compact Module")
    capabilities: List[str] = Field(default_factory=list, description="Hardware capabilities e.g. edge_inference, vision_processing, on_device_training, sensor_fusion, low_latency_compute")
    use_cases: List[str] = Field(default_factory=list, description="Target application domains e.g. Edge AI, Computer Vision, Industrial Automation, Smart Home, Healthcare")
    processor: Optional[str] = Field(None, description="Processor or NPU/TPU chip e.g. NVIDIA Jetson Orin, Hailo-8, Google Coral TPU, Apple Neural Engine")
    memory_storage: Optional[str] = Field(None, description="Memory and storage specifications e.g. 8GB LPDDR5, 16GB RAM / 128GB NVMe")
    connectivity: Optional[str] = Field(None, description="Connectivity interfaces e.g. Wi-Fi 6E, Bluetooth 5.2, Ethernet, USB 3.2, PCIe 4.0")
    operating_system: Optional[str] = Field(None, description="Supported operating system e.g. Linux / Ubuntu 22.04 LTS, Android, FreeRTOS")
    integrations: List[str] = Field(default_factory=list, description="Supported AI frameworks e.g. PyTorch, TensorFlow Lite, ONNX Runtime, ROS 2")
    api_sdk: Optional[str] = Field(None, description="Official API or SDK e.g. NVIDIA JetPack SDK, HailoRT, Coral Accelerator SDK")
    open_source: bool = Field(False, description="Whether physical hardware schematics/design or software stack are open source")
    commercial_status: Optional[str] = Field(None, description="Commercial status e.g. Commercial Product, Developer Kit, Open Source Hardware, Prototype")
    official_url: Optional[str] = Field(None, description="Official manufacturer landing page or product site")
    repository_url: Optional[str] = Field(None, description="Open source code or hardware design repository URL")
    logo: Optional[str] = Field(None, description="Verified official logo URL")

    @field_validator("official_url", mode="before")
    @classmethod
    def validate_device_official_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        return norm if norm else None

    @field_validator("repository_url", mode="before")
    @classmethod
    def validate_device_repo_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        norm = normalize_url(v)
        if norm.startswith("http://github.com"):
            norm = "https://github.com" + norm[17:]
        return norm.lower() if "github.com" in norm.lower() else norm

    @classmethod
    def create_canonical(cls, **kwargs) -> "DeviceRecord":
        """
        Creates a DeviceRecord with stable deterministic ID: device:<key>
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
            kwargs["id"] = f"device:{clean_m}/{clean_n}"
        elif repo_url and "github.com/" in repo_url.lower():
            clean = repo_url.lower().replace("https://github.com/", "").replace("http://github.com/", "").rstrip("/")
            kwargs["id"] = f"device:{clean}"
        else:
            clean_n = name.lower().replace(" ", "-")
            kwargs["id"] = f"device:{clean_n}"

        # Ensure primary URL field is set
        if not kwargs.get("url"):
            if official_url:
                kwargs["url"] = official_url
            elif repo_url:
                kwargs["url"] = repo_url
            else:
                clean_n = name.lower().replace(" ", "-")
                kwargs["url"] = f"https://ai-orbit.org/devices/{clean_n}"

        # Ensure discovery source
        if "discovery_source" not in kwargs:
            if "source" in kwargs and isinstance(kwargs["source"], DiscoverySource):
                kwargs["discovery_source"] = kwargs["source"]
            else:
                kwargs["discovery_source"] = DiscoverySource(
                    name=kwargs.pop("source_name", "GitHub AI Hardware & Edge Devices Search"),
                    url=kwargs.get("url", ""),
                    source_type="API",
                    source_trust_level="HIGH"
                )
        if "source" not in kwargs:
            kwargs["source"] = kwargs["discovery_source"]

        return cls(**kwargs)
