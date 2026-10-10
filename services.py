import asyncio
import random
import httpx
from typing import List, Tuple, Dict
from models import QuoteItem, ProviderName, VehicleCategory

class RoutingService:
    @staticmethod
    async def get_coordinates(client: httpx.AsyncClient, address: str) -> Tuple[float, float]:
        """Geocode text address to (latitude, longitude) using Nominatim OpenStreetMap."""
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "FairIQ-Fare-Engine/1.0"}
        params = {"q": address, "format": "json", "limit": 1}
        
        response = await client.get(url, params=params, headers=headers)
        data = response.json()
        if not data:
            raise ValueError(f"Could not find coordinates for location: '{address}'")
        
        return float(data[0]["lat"]), float(data[0]["lon"])

    @classmethod
    async def calculate_route(cls, origin_address: str, dest_address: str) -> Dict[str, float]:
        """Fetch real-world driving distance (km) and travel duration (minutes) using OSRM."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Geocode both locations concurrently
            (lat1, lon1), (lat2, lon2) = await asyncio.gather(
                cls.get_coordinates(client, origin_address),
                cls.get_coordinates(client, dest_address)
            )

            # 2. Query OSRM routing engine (expects format: lon,lat)
            osrm_url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
            res = await client.get(osrm_url)
            route_data = res.json()

            if route_data.get("code") != "Ok" or not route_data.get("routes"):
                raise ValueError("Routing service could not find a drivable path between these locations.")

            distance_meters = route_data["routes"][0]["distance"]
            duration_seconds = route_data["routes"][0]["duration"]

            return {
                "distance_km": round(distance_meters / 1000.0, 2),
                "duration_min": max(1, round(duration_seconds / 60.0))
            }

class FareAggregatorService:
    @staticmethod
    async def fetch_uber(distance_km: float, duration_min: int) -> List[QuoteItem]:
        await asyncio.sleep(0.08)
        surge = round(random.choice([1.0, 1.15, 1.25]), 2)
        return [
            QuoteItem(provider=ProviderName.UBER, vehicle_category=VehicleCategory.BIKE,
                      service_name="Uber Moto", base_fare=25.0, surge_multiplier=surge,
                      total_fare=round((25 + (distance_km * 8.0) + (duration_min * 1.0)) * surge, 2), eta_minutes=4),
            QuoteItem(provider=ProviderName.UBER, vehicle_category=VehicleCategory.AUTO,
                      service_name="Uber Auto", base_fare=35.0, surge_multiplier=surge,
                      total_fare=round((35 + (distance_km * 11.0) + (duration_min * 1.2)) * surge, 2), eta_minutes=5),
            QuoteItem(provider=ProviderName.UBER, vehicle_category=VehicleCategory.CAB_ECONOMY,
                      service_name="UberGo", base_fare=50.0, surge_multiplier=surge,
                      total_fare=round((50 + (distance_km * 14.0) + (duration_min * 1.5)) * surge, 2), eta_minutes=6)
        ]

    @staticmethod
    async def fetch_ola(distance_km: float, duration_min: int) -> List[QuoteItem]:
        await asyncio.sleep(0.1)
        surge = round(random.choice([1.0, 1.05, 1.2]), 2)
        return [
            QuoteItem(provider=ProviderName.OLA, vehicle_category=VehicleCategory.BIKE,
                      service_name="Ola Bike", base_fare=20.0, surge_multiplier=surge,
                      total_fare=round((20 + (distance_km * 8.5) + (duration_min * 0.9)) * surge, 2), eta_minutes=3),
            QuoteItem(provider=ProviderName.OLA, vehicle_category=VehicleCategory.AUTO,
                      service_name="Ola Auto", base_fare=30.0, surge_multiplier=surge,
                      total_fare=round((30 + (distance_km * 11.5) + (duration_min * 1.1)) * surge, 2), eta_minutes=4),
            QuoteItem(provider=ProviderName.OLA, vehicle_category=VehicleCategory.CAB_ECONOMY,
                      service_name="Ola Mini", base_fare=45.0, surge_multiplier=surge,
                      total_fare=round((45 + (distance_km * 14.2) + (duration_min * 1.6)) * surge, 2), eta_minutes=7)
        ]

    @staticmethod
    async def fetch_rapido(distance_km: float, duration_min: int) -> List[QuoteItem]:
        await asyncio.sleep(0.06)
        surge = round(random.choice([1.0, 1.0, 1.1]), 2)
        return [
            QuoteItem(provider=ProviderName.RAPIDO, vehicle_category=VehicleCategory.BIKE,
                      service_name="Rapido Bike", base_fare=15.0, surge_multiplier=surge,
                      total_fare=round((15 + (distance_km * 7.5) + (duration_min * 0.8)) * surge, 2), eta_minutes=2),
            QuoteItem(provider=ProviderName.RAPIDO, vehicle_category=VehicleCategory.AUTO,
                      service_name="Rapido Auto", base_fare=28.0, surge_multiplier=surge,
                      total_fare=round((28 + (distance_km * 10.5) + (duration_min * 1.0)) * surge, 2), eta_minutes=4),
            QuoteItem(provider=ProviderName.RAPIDO, vehicle_category=VehicleCategory.CAB_ECONOMY,
                      service_name="Rapido Cab", base_fare=48.0, surge_multiplier=surge,
                      total_fare=round((48 + (distance_km * 13.8) + (duration_min * 1.4)) * surge, 2), eta_minutes=8)
        ]