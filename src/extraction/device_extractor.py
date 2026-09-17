from typing import Dict, Any
from src.extraction.base import BaseExtractor
from src.models.device import DeviceRecord
from src.models.base import DiscoverySource, EvidenceSource


class DeviceExtractor(BaseExtractor):
    """
    Extractor for Device entities from GitHub AI Hardware Search and discovery sources.
    Extracts structured Device metadata fields while preserving provenance.
    """

    def extract(self, raw_item: Dict[str, Any], source_name: str = "GitHub AI Hardware Search") -> Dict[str, Any]:
        owner_info = raw_item.get("owner")
        if isinstance(owner_info, dict):
            owner = owner_info.get("login", "")
        else:
            owner = str(owner_info or "").strip()

        name = (raw_item.get("name") or "").strip()
        html_url = raw_item.get("html_url") or raw_item.get("url") or f"https://github.com/{owner}/{name}"

        query = raw_item.get("_discovery_query") or "topic:ai-hardware"
        src_name = raw_item.get("_discovery_source") or source_name

        topics = [t.lower() for t in (raw_item.get("topics") or [])]
        raw_desc = (raw_item.get("description") or "").strip()
        desc_lower = raw_desc.lower()
        name_lower = name.lower()
        combined_text = f"{name_lower} {desc_lower} {' '.join(topics)}"

        # Determine device type based on explicit evidence
        device_type = "AI Accelerator / Edge Dev Kit"
        physical_form = "Single Board Computer"
        if any(k in combined_text for k in ["camera", "vision-sensor", "smart-cam"]):
            device_type = "AI Camera"
            physical_form = "Smart Camera Appliance"
        elif any(k in combined_text for k in ["wearable", "glasses", "ring", "pin"]):
            device_type = "AI Wearable"
            physical_form = "Smart Wearable"
        elif any(k in combined_text for k in ["workstation", "server", "desktop-ai"]):
            device_type = "AI Workstation"
            physical_form = "Standalone Appliance"
        elif any(k in combined_text for k in ["pcie", "card", "accelerator"]):
            device_type = "AI Accelerator"
            physical_form = "PCIe Card"
        elif any(k in combined_text for k in ["sensor", "interface", "haptic"]):
            device_type = "Physical AI Interface"
            physical_form = "Sensor Node"

        # Hardware capabilities derived strictly from evidence
        capabilities = []
        if any(k in combined_text for k in ["edge", "on-device", "embedded"]):
            capabilities.append("edge_inference")
        if any(k in combined_text for k in ["vision", "camera", "image"]):
            capabilities.append("vision_processing")
        if any(k in combined_text for k in ["train", "fine-tune"]):
            capabilities.append("on_device_training")
        if any(k in combined_text for k in ["sensor", "imu", "fusion"]):
            capabilities.append("sensor_fusion")
        if any(k in combined_text for k in ["realtime", "low-latency", "npu"]):
            capabilities.append("low_latency_compute")

        # Processor / NPU inference
        processor = None
        if "jetson" in combined_text:
            processor = "NVIDIA Jetson System-on-Module"
        elif "hailo" in combined_text:
            processor = "Hailo AI Processor"
        elif "coral" in combined_text:
            processor = "Google Coral Edge TPU"
        elif "raspberry" in combined_text or "rpi" in combined_text:
            processor = "Broadcom ARM NPU / Raspberry Pi"
        elif "npu" in combined_text:
            processor = "Dedicated NPU Chip"

        # Open source hardware / software status
        open_source = any(k in combined_text for k in ["open-hardware", "open-source", "schematics", "pcb", "gerber"])

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
            evidence_type="HARDWARE_REPOSITORY"
        )

        extracted = {
            "name": name,
            "manufacturer": owner,
            "url": raw_item.get("homepage") or html_url,
            "repository_url": html_url,
            "official_url": raw_item.get("homepage"),
            "description": raw_desc if raw_desc else None,
            "categories": ["Devices", "AI Hardware", "Edge AI"],
            "device_type": device_type,
            "physical_form": physical_form,
            "capabilities": capabilities,
            "processor": processor,
            "open_source": open_source,
            "commercial_status": "Commercial Product" if raw_item.get("homepage") else "Developer Kit",
            "discovery_source": discovery_src,
            "source": discovery_src,
            "evidence_sources": [evidence_src]
        }
        return extracted

    def to_record(self, raw_item: Dict[str, Any], source_name: str = "GitHub AI Hardware Search") -> DeviceRecord:
        extracted = self.extract(raw_item, source_name)
        return DeviceRecord.create_canonical(**extracted)
