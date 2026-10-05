"""Generate the dashboard JSON cache from Hive.

Run this module whenever the source data should be refreshed:
    python backend.py
"""

import csv
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


DATABASE = "food_delivery"
CACHE_FILE_PATH = Path(__file__).resolve().parent / "dashboard_cache.json"

KNOWN_HEADER_NAMES = {
    "city", "weather", "weatherconditions", "traffic_density", "road_traffic_density",
    "vehicle_type", "type_of_vehicle", "festival", "order_type", "type_of_order",
    "multiple_deliveries", "vehicle_condition", "delivery_person_id",
    "delivery_person_ratings", "delivery_person_age", "id", "order_date",
    "time_ordered", "time_order_picked", "average_distance_km", "total_orders",
    "total_delivery_persons", "total_cities", "average_rating", "average_vehicle_condition",
}

QUERY_SUMMARY = """
    SELECT
        COUNT(*) AS total_orders,
        COUNT(DISTINCT delivery_person_id) AS total_delivery_persons,
        COUNT(DISTINCT city) AS total_cities,
        AVG(delivery_person_ratings) AS average_rating,
        AVG(vehicle_condition) AS average_vehicle_condition
    FROM deliveries
    WHERE city IS NOT NULL
    AND LOWER(TRIM(city)) != 'nan'
    AND LOWER(TRIM(city)) != 'city'
"""

QUERY_ORDERS_BY_CITY = """
    SELECT TRIM(city) AS city, COUNT(*) AS total_orders
    FROM deliveries
    WHERE city IS NOT NULL
    AND LOWER(TRIM(city)) != 'nan'
    AND LOWER(TRIM(city)) != 'city'
    GROUP BY TRIM(city)
    ORDER BY total_orders DESC
"""

QUERY_ORDERS_BY_TRAFFIC = """
    SELECT TRIM(road_traffic_density) AS traffic_density, COUNT(*) AS total_orders
    FROM deliveries
    WHERE road_traffic_density IS NOT NULL
    AND LOWER(TRIM(road_traffic_density)) NOT IN ('nan', 'road_traffic_density', 'traffic_density')
    GROUP BY TRIM(road_traffic_density)
    ORDER BY total_orders DESC
"""

QUERY_ORDERS_BY_WEATHER = """
    SELECT TRIM(weatherconditions) AS weather, COUNT(*) AS total_orders
    FROM deliveries
    WHERE weatherconditions IS NOT NULL
    AND LOWER(TRIM(weatherconditions)) NOT IN ('nan', 'weatherconditions', 'weather')
    GROUP BY TRIM(weatherconditions)
    ORDER BY total_orders DESC
"""

QUERY_ORDERS_BY_VEHICLE = """
    SELECT TRIM(type_of_vehicle) AS vehicle_type, COUNT(*) AS total_orders
    FROM deliveries
    WHERE type_of_vehicle IS NOT NULL
    AND LOWER(TRIM(type_of_vehicle)) NOT IN ('nan', 'type_of_vehicle', 'vehicle_type')
    GROUP BY TRIM(type_of_vehicle)
    ORDER BY total_orders DESC
"""

QUERY_ORDERS_BY_FESTIVAL = """
    SELECT TRIM(festival) AS festival, COUNT(*) AS total_orders
    FROM deliveries
    WHERE festival IS NOT NULL
    AND LOWER(TRIM(festival)) NOT IN ('nan', 'festival')
    GROUP BY TRIM(festival)
    ORDER BY total_orders DESC
"""

QUERY_DISTANCE_BY_CITY = """
    SELECT
        TRIM(city) AS city,
        ROUND(
            AVG(
                SQRT(
                    POW((delivery_location_latitude - restaurant_latitude) * 111, 2)
                    + POW((delivery_location_longitude - restaurant_longitude) * 111, 2)
                )
            ),
            2
        ) AS average_distance_km
    FROM deliveries
    WHERE city IS NOT NULL
    AND LOWER(TRIM(city)) NOT IN ('nan', 'city')
    GROUP BY TRIM(city)
    ORDER BY average_distance_km DESC
"""

QUERY_ORDERS_BY_TYPE = """
    SELECT TRIM(type_of_order) AS order_type, COUNT(*) AS total_orders
    FROM deliveries
    WHERE type_of_order IS NOT NULL
    AND LOWER(TRIM(type_of_order)) NOT IN ('nan', 'type_of_order', 'order_type')
    GROUP BY TRIM(type_of_order)
    ORDER BY total_orders DESC
"""

QUERY_ORDERS_BY_VEHICLE_CONDITION = """
    SELECT vehicle_condition, COUNT(*) AS total_orders
    FROM deliveries
    WHERE vehicle_condition IS NOT NULL
    AND LOWER(TRIM(CAST(vehicle_condition AS STRING))) NOT IN ('nan', 'vehicle_condition')
    GROUP BY vehicle_condition
    ORDER BY vehicle_condition
"""

QUERY_ORDERS_BY_MULTIPLE_DELIVERIES = """
    SELECT TRIM(multiple_deliveries) AS multiple_deliveries, COUNT(*) AS total_orders
    FROM deliveries
    WHERE multiple_deliveries IS NOT NULL
    AND LOWER(TRIM(multiple_deliveries)) NOT IN ('nan', 'multiple_deliveries')
    GROUP BY TRIM(multiple_deliveries)
    ORDER BY total_orders DESC
"""

QUERY_ORDERS_BY_DATE = """
    SELECT order_date, COUNT(*) AS total_orders
    FROM deliveries
    WHERE order_date IS NOT NULL
    AND LOWER(TRIM(order_date)) NOT IN ('nan', 'order_date')
    GROUP BY order_date
    ORDER BY order_date
"""

QUERY_ORDERS = """
    SELECT
        id,
        delivery_person_id,
        delivery_person_age,
        delivery_person_ratings,
        restaurant_latitude,
        restaurant_longitude,
        delivery_location_latitude,
        delivery_location_longitude,
        order_date,
        time_ordered,
        time_order_picked,
        TRIM(weatherconditions) AS weather,
        TRIM(road_traffic_density) AS traffic_density,
        vehicle_condition,
        TRIM(type_of_order) AS order_type,
        TRIM(type_of_vehicle) AS vehicle_type,
        TRIM(multiple_deliveries) AS multiple_deliveries,
        TRIM(festival) AS festival,
        TRIM(city) AS city
    FROM deliveries
    WHERE city IS NOT NULL
    AND LOWER(TRIM(city)) != 'nan'
    AND LOWER(TRIM(city)) != 'city'
"""

QUERY_FILTERS = {
    "cities": """
        SELECT DISTINCT TRIM(city) AS city FROM deliveries
        WHERE city IS NOT NULL AND LOWER(TRIM(city)) NOT IN ('nan', 'city')
        ORDER BY city
    """,
    "weather": """
        SELECT DISTINCT TRIM(weatherconditions) AS weather FROM deliveries
        WHERE weatherconditions IS NOT NULL
        AND LOWER(TRIM(weatherconditions)) NOT IN ('nan', 'weatherconditions', 'weather')
        ORDER BY weather
    """,
    "traffic": """
        SELECT DISTINCT TRIM(road_traffic_density) AS traffic_density FROM deliveries
        WHERE road_traffic_density IS NOT NULL
        AND LOWER(TRIM(road_traffic_density)) NOT IN ('nan', 'road_traffic_density', 'traffic_density')
        ORDER BY traffic_density
    """,
    "vehicles": """
        SELECT DISTINCT TRIM(type_of_vehicle) AS vehicle_type FROM deliveries
        WHERE type_of_vehicle IS NOT NULL
        AND LOWER(TRIM(type_of_vehicle)) NOT IN ('nan', 'type_of_vehicle', 'vehicle_type')
        ORDER BY vehicle_type
    """,
    "festivals": """
        SELECT DISTINCT TRIM(festival) AS festival FROM deliveries
        WHERE festival IS NOT NULL AND LOWER(TRIM(festival)) NOT IN ('nan', 'festival')
        ORDER BY festival
    """,
    "order_types": """
        SELECT DISTINCT TRIM(type_of_order) AS order_type FROM deliveries
        WHERE type_of_order IS NOT NULL
        AND LOWER(TRIM(type_of_order)) NOT IN ('nan', 'type_of_order', 'order_type')
        ORDER BY order_type
    """,
}


def is_hive_log_line(line: str) -> bool:
    """Return whether a Beeline output line is logging noise rather than CSV."""
    stripped = line.strip()
    if not stripped or re.match(r"^\d{4}-\d{2}-\d{2}[T ]", stripped):
        return True

    log_keywords = (
        "WARN", "INFO", "ERROR", "DEBUG", "TRACE", "SLF4J", "log4j",
        "org.apache", "jar:file:", "beeline", "Please remove the", "See https://",
        "See http://", "Starting configuration", "Start watching", "Configuration org",
        "Stopping configuration", "Connecting to", "Connected to", "Driver:",
        "Transaction isolation", "Beeline version", "Closing:", "jdbc:hive2",
        "Output format", "Executing command",
    )
    if any(keyword.lower() in stripped.lower() for keyword in log_keywords):
        return True
    return stripped.startswith(("+", "|", "0:", "1:", "2:", "3:", "4:", "5:"))


def run_hive_query(query: str) -> list[dict[str, Any]]:
    """Execute a Hive query through Beeline and parse its CSV output."""
    command = [
        "beeline",
        "-u",
        "jdbc:hive2://localhost:10000/default",
        "--silent=true",
        "--showHeader=true",
        "--outputformat=csv2",
        "-e",
        f"USE {DATABASE}; {query}",
    ]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Hive query timed out after 180 seconds") from error
    except FileNotFoundError as error:
        raise RuntimeError("Hive query failed: Beeline executable was not found") from error

    if result.returncode != 0:
        error_message = result.stderr.strip() or "Beeline returned a non-zero exit code"
        raise RuntimeError(f"Hive query failed: {error_message}")

    clean_lines = [line.strip() for line in result.stdout.splitlines() if not is_hive_log_line(line)]
    if not clean_lines:
        return []

    rows = list(csv.reader(clean_lines))
    if len(rows) < 2:
        return []

    headers = [header.strip().split(".")[-1].lower() for header in rows[0]]
    result_rows: list[dict[str, Any]] = []
    for row in rows[1:]:
        if len(row) != len(headers):
            continue
        if all(
            value.strip().lower() in KNOWN_HEADER_NAMES
            or value.strip().lower() == header
            for header, value in zip(headers, row)
        ):
            continue

        item: dict[str, Any] = {}
        for header, value in zip(headers, row):
            value = value.strip()
            if value == "" or value.lower() in ("nan", "null", "none"):
                item[header] = None
            elif re.fullmatch(r"-?\d+", value):
                item[header] = int(value)
            elif re.fullmatch(r"-?\d+\.\d+", value):
                item[header] = float(value)
            else:
                item[header] = value
        result_rows.append(item)
    return result_rows


def build_json_data() -> dict[str, Any]:
    """Run the Hive queries needed by every API endpoint."""
    queries = {
        "summary": QUERY_SUMMARY,
        "orders_by_city": QUERY_ORDERS_BY_CITY,
        "orders_by_traffic": QUERY_ORDERS_BY_TRAFFIC,
        "orders_by_weather": QUERY_ORDERS_BY_WEATHER,
        "orders_by_vehicle": QUERY_ORDERS_BY_VEHICLE,
        "orders_by_festival": QUERY_ORDERS_BY_FESTIVAL,
        "distance_by_city": QUERY_DISTANCE_BY_CITY,
        "orders_by_type": QUERY_ORDERS_BY_TYPE,
        "orders_by_vehicle_condition": QUERY_ORDERS_BY_VEHICLE_CONDITION,
        "orders_by_multiple_deliveries": QUERY_ORDERS_BY_MULTIPLE_DELIVERIES,
        "orders_by_date": QUERY_ORDERS_BY_DATE,
        "orders": QUERY_ORDERS,
    }
    data: dict[str, Any] = {}

    for name, query in queries.items():
        print(f"[HIVE] Creating {name} JSON data...")
        data[name] = run_hive_query(query)

    data["filters"] = {
        name: run_hive_query(query)
        for name, query in QUERY_FILTERS.items()
    }
    return data


def write_json_cache(data: dict[str, Any]) -> None:
    """Write generated data to the JSON cache atomically."""
    payload = {
        "last_updated": datetime.now().isoformat(),
        **data,
    }
    temp_file = CACHE_FILE_PATH.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as cache_file:
        json.dump(payload, cache_file, indent=2)
    temp_file.replace(CACHE_FILE_PATH)


def main() -> None:
    try:
        data = build_json_data()
        write_json_cache(data)
    except (OSError, RuntimeError) as error:
        raise SystemExit(f"[HIVE] JSON generation failed: {error}") from error
    print(f"[HIVE] JSON cache created at {CACHE_FILE_PATH}")


if __name__ == "__main__":
    main()
