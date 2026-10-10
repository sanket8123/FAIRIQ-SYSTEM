import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# --- ADD THESE TWO LINES ---
from models import RouteRequest, ComparisonResponse, BestQuoteResult
from services import RoutingService, FareAggregatorService
# ---------------------------

app = FastAPI(title="FairIQ Web Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_home():
    return FileResponse("static/index.html")

@app.post("/api/compare", response_model=ComparisonResponse)
async def compare_fares(payload: RouteRequest):
    # 1. Automatic Distance & Duration using OpenStreetMap & OSRM
    try:
        route_info = await RoutingService.calculate_route(payload.origin, payload.destination)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    distance_km = route_info["distance_km"]
    duration_mins = route_info["duration_min"]

    # 2. Parallel calculations for Uber, Ola, and Rapido
    try:
        results = await asyncio.gather(
            FareAggregatorService.fetch_uber(distance_km, duration_mins),
            FareAggregatorService.fetch_ola(distance_km, duration_mins),
            FareAggregatorService.fetch_rapido(distance_km, duration_mins),
        )
        flat_quotes = [q for provider_list in results for q in provider_list]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Calculate category winners
    best_map = {}
    for q in flat_quotes:
        cat = q.vehicle_category
        if cat not in best_map or (q.total_fare, q.eta_minutes) < (best_map[cat].lowest_fare, best_map[cat].eta_minutes):
            best_map[cat] = BestQuoteResult(
                vehicle_category=q.vehicle_category,
                cheapest_provider=q.provider,
                service_name=q.service_name,
                lowest_fare=q.total_fare,
                eta_minutes=q.eta_minutes,
                surge_multiplier=q.surge_multiplier
            )

    best_list = list(best_map.values())
    cheapest = min(best_list, key=lambda x: x.lowest_fare)

    hrs = duration_mins // 60
    mins = duration_mins % 60
    duration_str = f"{hrs} hr {mins} min" if hrs > 0 else f"{mins} min"

    return ComparisonResponse(
        origin=payload.origin,
        destination=payload.destination,
        distance_km=distance_km,
        duration_display=duration_str,
        total_duration_minutes=duration_mins,
        all_quotes=flat_quotes,             # Returns all 9 quotes (3 apps x 3 categories)
        best_by_category=best_list,
        absolute_cheapest=cheapest
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, access_log=True)