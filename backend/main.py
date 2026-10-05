"""JSON-backed API for food delivery analytics.

Run the Hive data producer separately with ``python backend.py`` to refresh
dashboard_cache.json. This API process never connects to Hive.
"""

import json
from itertools import islice
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


CACHE_FILE_PATH = Path(__file__).resolve().parent / "dashboard_cache.json"
DASHBOARD_KEYS = (
    "summary",
    "orders_by_city",
    "orders_by_traffic",
    "orders_by_weather",
    "orders_by_vehicle",
    "orders_by_festival",
    "distance_by_city",
    "filters",
)
DATASET_KEYS = DASHBOARD_KEYS + (
    "orders_by_type",
    "orders_by_vehicle_condition",
    "orders_by_multiple_deliveries",
    "orders_by_date",
    "orders",
)
ORDER_FILTER_FIELDS = {
    "city": "city",
    "weather": "weather",
    "traffic": "traffic_density",
    "vehicle": "vehicle_type",
    "festival": "festival",
    "order_type": "order_type",
}

cache_lock = threading.Lock()
json_data: dict[str, Any] = {}
cache_status: dict[str, Any] = {
    "ready": False,
    "is_refreshing": False,
    "last_updated": None,
    "successful_queries": 0,
    "total_queries": len(DATASET_KEYS),
    "orders_ready": False,
    "available_datasets": [],
    "missing_datasets": list(DATASET_KEYS),
    "errors": [],
}
cache_error: str | None = None


def reload_json_cache() -> bool:
    """Load the cache file without making any Hive/database calls."""
    global cache_error
    try:
        with CACHE_FILE_PATH.open("r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
        if not isinstance(data, dict):
            raise ValueError("JSON cache must contain an object")
        missing_keys = [key for key in DASHBOARD_KEYS if key not in data]
        if missing_keys:
            raise ValueError(f"JSON cache is missing dashboard fields: {', '.join(missing_keys)}")
        if not isinstance(data["filters"], dict):
            raise ValueError("JSON cache field 'filters' must contain an object")
        invalid_fields = [
            key for key in DASHBOARD_KEYS[:-1]
            if not isinstance(data[key], list)
        ]
        if invalid_fields:
            raise ValueError(
                f"JSON cache fields must contain arrays: {', '.join(invalid_fields)}"
            )
        if "orders" in data and not isinstance(data["orders"], list):
            raise ValueError("JSON cache field 'orders' must contain an array")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        with cache_lock:
            cache_error = str(error)
            cache_status["ready"] = False
            cache_status["errors"] = [cache_error]
        return False

    with cache_lock:
        json_data.clear()
        json_data.update(data)
        cache_error = None
        cache_status["ready"] = True
        cache_status["is_refreshing"] = False
        cache_status["last_updated"] = data.get("last_updated")
        cache_status["successful_queries"] = sum(key in data for key in DATASET_KEYS)
        cache_status["total_queries"] = len(DATASET_KEYS)
        cache_status["orders_ready"] = isinstance(data.get("orders"), list)
        cache_status["available_datasets"] = [key for key in DATASET_KEYS if key in data]
        cache_status["missing_datasets"] = [
            key for key in DATASET_KEYS if key not in data
        ]
        cache_status["errors"] = (
            [] if cache_status["orders_ready"] else [
                "Filtered delivery records are missing from the JSON cache. "
                "Run backend.py to regenerate it."
            ]
        )
    return True


def require_json_data(key: str | None = None) -> Any:
    """Return loaded JSON data or report that the producer must run first."""
    with cache_lock:
        if not cache_status["ready"]:
            raise HTTPException(
                status_code=503,
                detail=f"JSON cache is unavailable: {cache_error or 'cache has not been loaded'}",
            )
        if key is not None and key not in json_data:
            raise HTTPException(
                status_code=503,
                detail=f"JSON cache does not contain '{key}'. Run backend.py to regenerate it.",
            )
        if key == "orders" and not isinstance(json_data.get(key), list):
            raise HTTPException(
                status_code=503,
                detail="Filtered delivery records are missing from the JSON cache. "
                "Run backend.py to regenerate it.",
            )
        return json_data[key] if key is not None else dict(json_data)


def dashboard_data() -> dict[str, Any]:
    """Return only the original dashboard response fields."""
    data = require_json_data()
    return {key: data[key] for key in DASHBOARD_KEYS}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not reload_json_cache():
        print(f"[JSON] Cache unavailable: {cache_error}")
    yield


app = FastAPI(title="Food Delivery BDA API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Food Delivery BDA API", "status": "running"}


@app.get("/api/health")
def health():
    data = require_json_data("summary")
    return {
        "status": "healthy",
        "data_source": "json",
        "total_orders": data[0]["total_orders"] if data else 0,
    }


@app.get("/api/cache-status")
def get_cache_status():
    with cache_lock:
        return dict(cache_status)


@app.get("/api/dashboard")
def get_dashboard():
    return dashboard_data()


@app.post("/api/refresh")
def refresh_dashboard():
    """Reload JSON written by backend.py; this endpoint does not run Hive."""
    if not reload_json_cache():
        raise HTTPException(
            status_code=503,
            detail=f"Could not reload JSON cache: {cache_error}",
        )
    return dashboard_data()


@app.get("/api/summary")
def summary():
    return require_json_data("summary")


@app.get("/api/orders-by-city")
def orders_by_city():
    return require_json_data("orders_by_city")


@app.get("/api/orders-by-traffic")
def orders_by_traffic():
    return require_json_data("orders_by_traffic")


@app.get("/api/orders-by-weather")
def orders_by_weather():
    return require_json_data("orders_by_weather")


@app.get("/api/orders-by-vehicle")
def orders_by_vehicle():
    return require_json_data("orders_by_vehicle")


@app.get("/api/orders-by-festival")
def orders_by_festival():
    return require_json_data("orders_by_festival")


@app.get("/api/distance-by-city")
def distance_by_city():
    return require_json_data("distance_by_city")


@app.get("/api/filters")
def filters():
    return require_json_data("filters")


@app.get("/api/orders-by-type")
def orders_by_type():
    return require_json_data("orders_by_type")


@app.get("/api/orders-by-vehicle-condition")
def orders_by_vehicle_condition():
    return require_json_data("orders_by_vehicle_condition")


@app.get("/api/orders-by-multiple-deliveries")
def orders_by_multiple_deliveries():
    return require_json_data("orders_by_multiple_deliveries")


@app.get("/api/orders-by-date")
def orders_by_date():
    return require_json_data("orders_by_date")


@app.get("/api/orders")
def orders(
    city: str | None = Query(default=None),
    weather: str | None = Query(default=None),
    traffic: str | None = Query(default=None),
    vehicle: str | None = Query(default=None),
    festival: str | None = Query(default=None),
    order_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
):
    all_orders = require_json_data("orders")
    selected_filters = {
        "city": city,
        "weather": weather,
        "traffic": traffic,
        "vehicle": vehicle,
        "festival": festival,
        "order_type": order_type,
    }
    matching_orders = (
        order
        for order in all_orders
        if all(
            value is None or str(order.get(ORDER_FILTER_FIELDS[name], "")).strip() == value
            for name, value in selected_filters.items()
        )
    )
    return list(islice(matching_orders, limit))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
