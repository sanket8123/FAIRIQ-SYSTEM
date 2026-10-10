from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class VehicleCategory(str, Enum):
    BIKE = "BIKE"
    AUTO = "AUTO"
    CAB_ECONOMY = "CAB_ECONOMY"

class ProviderName(str, Enum):
    UBER = "UBER"
    OLA = "OLA"
    RAPIDO = "RAPIDO"

# Only origin and destination are required from the user
class RouteRequest(BaseModel):
    origin: str = Field(..., description="Starting pickup location")
    destination: str = Field(..., description="Drop-off destination")

class QuoteItem(BaseModel):
    provider: ProviderName
    vehicle_category: VehicleCategory
    service_name: str
    base_fare: float
    surge_multiplier: float
    total_fare: float
    eta_minutes: int

class BestQuoteResult(BaseModel):
    vehicle_category: VehicleCategory
    cheapest_provider: ProviderName
    service_name: str
    lowest_fare: float
    eta_minutes: int
    surge_multiplier: float

class ComparisonResponse(BaseModel):
    origin: str
    destination: str
    distance_km: float
    duration_display: str
    total_duration_minutes: int
    all_quotes: List[QuoteItem]
    best_by_category: List[BestQuoteResult]
    absolute_cheapest: BestQuoteResult