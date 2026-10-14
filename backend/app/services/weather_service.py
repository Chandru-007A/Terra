"""
Live Weather Service for Agricultural Decision Support.
Integrates with Open-Meteo API (WMO-compliant, no API key required)
with coordinate caching, 1-hour forecast TTL, and agronomic threshold evaluation.
"""

from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Any, Optional, Tuple, List
import requests

logger = logging.getLogger(__name__)

# Pre-mapped coordinates for key Indian agricultural districts
KNOWN_COORDINATES: Dict[str, Tuple[float, float]] = {
    "nashik": (19.9975, 73.7898),
    "pune": (18.5204, 73.8567),
    "baramati": (18.1517, 74.5771),
    "nagpur": (21.1458, 79.0882),
    "aurangabad": (19.8762, 75.3433),
    "chhatrapati sambhajinagar": (19.8762, 75.3433),
    "solapur": (17.6599, 75.9064),
    "ahmednagar": (19.0952, 74.7496),
    "kolhapur": (16.7050, 74.2433),
    "ludhiana": (30.9010, 75.8573),
    "karnal": (29.6857, 76.9905),
    "thanjavur": (10.7870, 79.1378),
    "maharashtra": (19.7515, 75.7139),
    "punjab": (31.1471, 75.3412),
    "haryana": (29.0588, 76.0856),
}

# In-memory forecast cache: key -> (forecast_dict, cached_at)
_FORECAST_CACHE: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
CACHE_TTL_HOURS = 1


def resolve_coordinates(location: str) -> Optional[Tuple[float, float]]:
    """Resolves coordinates from dictionary or Open-Meteo geocoding."""
    if not location or not location.strip():
        return None

    clean = location.strip().lower()
    for key, coords in KNOWN_COORDINATES.items():
        if key in clean:
            return coords

    # Try Open-Meteo Geocoding
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(location)}&count=1&language=en&format=json"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                coords = (float(result["latitude"]), float(result["longitude"]))
                KNOWN_COORDINATES[clean] = coords
                return coords
    except Exception as e:
        logger.warning(f"Geocoding lookup failed for '{location}': {e}")

    # Fallback to Maharashtra general center if unrecognized Indian location
    return KNOWN_COORDINATES.get("maharashtra")


def get_live_forecast(location: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Fetches live 7-day daily forecast from Open-Meteo.
    Uses 1-hour cache to avoid excessive requests.
    """
    coords = resolve_coordinates(location)
    if not coords:
        return {
            "success": False,
            "provider": "Open-Meteo Weather Forecast API",
            "error": f"Location '{location}' could not be resolved to coordinates.",
            "last_updated": None,
        }

    cache_key = f"{coords[0]:.4f},{coords[1]:.4f}"
    now = datetime.now(timezone.utc)

    if not force_refresh and cache_key in _FORECAST_CACHE:
        cached_data, cached_at = _FORECAST_CACHE[cache_key]
        if (now - cached_at) < timedelta(hours=CACHE_TTL_HOURS):
            return cached_data

    lat, lon = coords
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&"
        f"timezone=auto"
    )

    try:
        resp = requests.get(url, timeout=6)
        if resp.status_code != 200:
            return {
                "success": False,
                "provider": "Open-Meteo Weather Forecast API",
                "error": f"Weather API returned status code {resp.status_code}",
                "last_updated": None,
            }

        api_json = resp.json()
        daily = api_json.get("daily", {})
        result = {
            "success": True,
            "provider": "Open-Meteo Weather Forecast API (WMO compliant)",
            "latitude": lat,
            "longitude": lon,
            "location": location,
            "daily": daily,
            "last_updated": now.isoformat(),
        }
        _FORECAST_CACHE[cache_key] = (result, now)
        return result

    except Exception as e:
        logger.warning(f"Failed to fetch live weather forecast from Open-Meteo: {e}")
        return {
            "success": False,
            "provider": "Open-Meteo Weather Forecast API",
            "error": f"Network error connecting to weather provider: {str(e)}",
            "last_updated": None,
        }


def evaluate_weather_alerts_for_field(
    field_id: str,
    field_name: str,
    location: str,
    crops: List[Dict[str, Any]],
    heavy_rain_threshold: float = 35.0,
    extreme_heat_threshold: float = 36.0,
    dry_spell_days: int = 5,
    custom_forecast: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluates forecast against agronomic thresholds and returns actionable alert payloads.
    Never fabricates alerts if live data is unavailable.
    """
    forecast = custom_forecast or get_live_forecast(location)
    if not forecast.get("success"):
        return []

    daily = forecast.get("daily", {})
    times = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precips = daily.get("precipitation_sum", [])
    winds = daily.get("wind_speed_10m_max", [])

    alerts: List[Dict[str, Any]] = []
    crop_labels = ", ".join(c.get("name", "Crops") for c in crops) if crops else "Field crops"
    last_updated = forecast.get("last_updated")

    # 1. Heavy Rainfall Check
    for i, t in enumerate(times[:5]):
        p = precips[i] if i < len(precips) and precips[i] is not None else 0.0
        if p >= heavy_rain_threshold:
            alerts.append({
                "type": "weather_alert",
                "severity": "critical" if p >= 50.0 else "warning",
                "title": f"🌧️ Heavy Rainfall Alert: {p:.1f}mm in {location}",
                "message": (
                    f"Forecast predicts {p:.1f} mm of rainfall on {t} in {location}. "
                    f"Action for {field_name} ({crop_labels}): Ensure field drainage channels are cleared "
                    f"to prevent root waterlogging, collar rot, and fungal outbreaks."
                ),
                "field_id": field_id,
                "field_name": field_name,
                "crop_name": crop_labels,
                "link_url": "/dashboard/resources",
                "dedup_key": f"weather_alert:{field_id}:heavy_rain:{t}",
                "metadata": {
                    "forecast_date": t,
                    "rainfall_mm": p,
                    "condition": "Heavy Rain",
                    "provider": forecast.get("provider"),
                    "last_updated": last_updated,
                },
            })
            break  # One alert for next event in window

    # 2. Extreme Heat Check
    for i, t in enumerate(times[:5]):
        t_max = max_temps[i] if i < len(max_temps) and max_temps[i] is not None else 0.0
        if t_max >= extreme_heat_threshold:
            alerts.append({
                "type": "weather_alert",
                "severity": "warning",
                "title": f"☀️ High Heat Spike: {t_max:.1f}°C in {location}",
                "message": (
                    f"Max temperature of {t_max:.1f}°C forecasted on {t}. "
                    f"Action for {field_name} ({crop_labels}): Schedule early morning micro-irrigation "
                    f"or apply protective organic mulch to preserve soil moisture and prevent flower drop."
                ),
                "field_id": field_id,
                "field_name": field_name,
                "crop_name": crop_labels,
                "link_url": "/dashboard/resources",
                "dedup_key": f"weather_alert:{field_id}:extreme_heat:{t}",
                "metadata": {
                    "forecast_date": t,
                    "temperature_max_c": t_max,
                    "condition": "Extreme Heat",
                    "provider": forecast.get("provider"),
                    "last_updated": last_updated,
                },
            })
            break

    # 3. Extended Dry Spell Check
    consecutive_dry = 0
    dry_start = ""
    for i, t in enumerate(times[:7]):
        p = precips[i] if i < len(precips) and precips[i] is not None else 0.0
        if p < 1.0:
            if consecutive_dry == 0:
                dry_start = t
            consecutive_dry += 1
        else:
            consecutive_dry = 0

    if consecutive_dry >= dry_spell_days:
        alerts.append({
            "type": "weather_alert",
            "severity": "info",
            "title": f"💧 Dry Spell Forecast ({consecutive_dry} Days)",
            "message": (
                f"{consecutive_dry} consecutive rain-free days forecast from {dry_start} in {location}. "
                f"Action for {field_name}: Verify irrigation reservoir levels and schedule crop maintenance watering."
            ),
            "field_id": field_id,
            "field_name": field_name,
            "crop_name": crop_labels,
            "link_url": "/dashboard/resources",
            "dedup_key": f"weather_alert:{field_id}:dry_spell:{dry_start}",
            "metadata": {
                "dry_days": consecutive_dry,
                "condition": "Dry Spell",
                "provider": forecast.get("provider"),
                "last_updated": last_updated,
            },
        })

    # 4. High Wind Gusts (Lodging risk)
    for i, t in enumerate(times[:4]):
        w = winds[i] if i < len(winds) and winds[i] is not None else 0.0
        if w >= 40.0:
            alerts.append({
                "type": "weather_alert",
                "severity": "warning",
                "title": f"💨 High Wind Alert: {w:.1f} km/h in {location}",
                "message": (
                    f"Wind speeds reaching {w:.1f} km/h forecast on {t}. "
                    f"Action for {field_name}: Avoid foliar pesticide spraying and provide staking or earthing up for tall crops."
                ),
                "field_id": field_id,
                "field_name": field_name,
                "crop_name": crop_labels,
                "link_url": "/dashboard/calendar",
                "dedup_key": f"weather_alert:{field_id}:high_wind:{t}",
                "metadata": {
                    "wind_speed_kmh": w,
                    "condition": "High Wind",
                    "provider": forecast.get("provider"),
                    "last_updated": last_updated,
                },
            })
            break

    return alerts
