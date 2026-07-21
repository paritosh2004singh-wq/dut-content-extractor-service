from pydantic import BaseModel, ConfigDict, Field
from typing import List
from app.modules.ingestion.domain.value_objects.enums import ScriptType

class OCRProviderCapability(BaseModel):
    """
    Defines the strengths and costs of a specific provider.
    """
    model_config = ConfigDict(frozen=True)
    provider_id: str
    supported_scripts: List[ScriptType]
    supports_handwriting: bool = False
    supports_tables: bool = False
    supports_equations: bool = False
    cost_tier: int = Field(default=1, description="1 is cheap/local CPU, 5 is expensive remote API")
    latency_profile: str = "medium"
    cpu_required: bool = False

class CapabilityRequirements(BaseModel):
    """
    Defines what a region NEEDS from a provider, rather than dictating the exact provider.
    """
    model_config = ConfigDict(frozen=True)
    required_scripts: List[ScriptType] = Field(default_factory=list)
    requires_handwriting: bool = False
    requires_equations: bool = False
    requires_tables: bool = False
    max_cost_tier: int = 5
