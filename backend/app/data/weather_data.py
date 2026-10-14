"""
Regional and seasonal weather data for Indian agricultural zones.

DATA SOURCE: NASA POWER Climatology API v2.6
  URL: https://power.larc.nasa.gov/api/temporal/climatology/point
  Community: AG (Agroclimatology)
  Parameters: T2M (2m temperature), PRECTOTCORR (corrected precipitation), RH2M (relative humidity)
  Fetched: 2025-10 (multi-year climatological average, 1981–2022 baseline)
  License: CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
  Citation: Stackhouse, P.W. et al. (2023). NASA POWER Project.

Seasonal definitions (Indian crop calendar):
  Rabi   — Nov–Mar (cool dry season, winter crops: wheat, chickpea, mustard)
  Kharif — Jun–Sep (monsoon season, summer crops: soybean, cotton, rice)
  Zaid   — Apr–May (hot dry inter-season: watermelon, vegetables)

Rainfall unit: mm (monthly PRECTOTCORR values in mm/day × 30.4 × n_months)
Temperature unit: °C
Humidity unit: %

NOTE: These are long-term climatological means — actual seasonal values will
vary year-to-year. Do not treat as real-time forecasts.
"""

from typing import Dict, Any

# ─── NASA POWER-calibrated regional climatology ───────────────────────────────
# Coordinates used for API queries:
#   Nashik:     lat=20.0,  lon=73.8  (Nashik district, Maharashtra)
#   Ludhiana:   lat=30.9,  lon=75.85 (Ludhiana district, Punjab)
#   Pune:       lat=18.52, lon=73.86 (Pune district, Maharashtra/Deccan)
#   Thanjavur:  lat=10.78, lon=79.14 (Thanjavur, Cauvery Delta, Tamil Nadu)

REGION_WEATHER: Dict[str, Dict[str, Any]] = {
    "Nashik / Maharashtra": {
        # Annual: T2M=24.4°C, RH2M=61.2%, Total rain≈1628mm (monsoon-dominant)
        "temperature_c": 24.4,
        "humidity_percent": 61.2,
        "rainfall_mm": 1628.0,
        "source": "NASA POWER Climatology (1981–2022), coords: 20.0°N, 73.8°E",
        "season_defaults": {
            "Rabi": {
                # Nov–Mar: cool, dry post-monsoon period
                "temperature_c": 22.7,
                "humidity_percent": 43.4,
                "rainfall_mm": 31.0,
            },
            "Kharif": {
                # Jun–Sep: south-west monsoon, high humidity
                "temperature_c": 24.5,
                "humidity_percent": 87.0,
                "rainfall_mm": 1510.0,
            },
            "Zaid": {
                # Apr–May: pre-monsoon heat, low humidity
                "temperature_c": 29.4,
                "humidity_percent": 45.4,
                "rainfall_mm": 16.0,
            },
        },
    },
    "Ludhiana / Punjab": {
        # Annual: T2M=25.3°C, RH2M=43.4%, Total rain≈657mm (monsoon + winter)
        "temperature_c": 25.3,
        "humidity_percent": 43.4,
        "rainfall_mm": 657.0,
        "source": "NASA POWER Climatology (1981–2022), coords: 30.9°N, 75.85°E",
        "season_defaults": {
            "Rabi": {
                # Nov–Mar: cold winters (Punjab fog belt), moderate rabi rains
                "temperature_c": 16.9,
                "humidity_percent": 42.5,
                "rainfall_mm": 102.0,
            },
            "Kharif": {
                # Jun–Sep: hot, humid monsoon with moderate rainfall
                "temperature_c": 32.6,
                "humidity_percent": 52.8,
                "rainfall_mm": 506.0,
            },
            "Zaid": {
                # Apr–May: very hot, dry
                "temperature_c": 31.7,
                "humidity_percent": 26.6,
                "rainfall_mm": 43.0,
            },
        },
    },
    "Pune / Deccan": {
        # Annual: T2M=23.9°C, RH2M=66.8%, Total rain≈1718mm (monsoon-dominant)
        "temperature_c": 23.9,
        "humidity_percent": 66.8,
        "rainfall_mm": 1718.0,
        "source": "NASA POWER Climatology (1981–2022), coords: 18.52°N, 73.86°E",
        "season_defaults": {
            "Rabi": {
                # Nov–Mar: mild winters, very dry
                "temperature_c": 21.9,
                "humidity_percent": 54.4,
                "rainfall_mm": 33.0,
            },
            "Kharif": {
                # Jun–Sep: monsoon, high humidity
                "temperature_c": 24.1,
                "humidity_percent": 87.4,
                "rainfall_mm": 1551.0,
            },
            "Zaid": {
                # Apr–May: warm pre-monsoon
                "temperature_c": 28.9,
                "humidity_percent": 49.4,
                "rainfall_mm": 30.0,
            },
        },
    },
    "Thanjavur / Cauvery Delta": {
        # Annual: T2M=28.2°C, RH2M=70.7%, Total rain≈1007mm (NE monsoon dominant)
        "temperature_c": 28.2,
        "humidity_percent": 70.7,
        "rainfall_mm": 1007.0,
        "source": "NASA POWER Climatology (1981–2022), coords: 10.78°N, 79.14°E",
        "season_defaults": {
            "Rabi": {
                # Nov–Mar: NE monsoon brings most rain here (reversed pattern vs north India)
                "temperature_c": 25.9,
                "humidity_percent": 77.1,
                "rainfall_mm": 411.0,
            },
            "Kharif": {
                # Jun–Sep: SW monsoon, less rain in this leeward delta zone
                "temperature_c": 29.8,
                "humidity_percent": 64.4,
                "rainfall_mm": 298.0,
            },
            "Zaid": {
                # Apr–May: hot, moderate humidity
                "temperature_c": 31.1,
                "humidity_percent": 63.5,
                "rainfall_mm": 106.0,
            },
        },
    },
}

# ─── Data provenance metadata ─────────────────────────────────────────────────
WEATHER_DATA_PROVENANCE = {
    "source": "NASA POWER Climatology API v2.6",
    "baseline_period": "1981–2022",
    "api_url": "https://power.larc.nasa.gov/api/temporal/climatology/point",
    "parameters_fetched": ["T2M", "PRECTOTCORR", "RH2M"],
    "community": "AG (Agroclimatology)",
    "license": "CC BY 4.0",
    "fetched_date": "2025-10",
    "note": (
        "Values are multi-year climatological averages. Actual seasonal weather will "
        "vary year-to-year. Rainfall is approximated from mm/day × season days. "
        "PRECTOTCORR monthly values multiplied by 30.4 (avg days/month) × n_months."
    ),
    "isric_note": (
        "ISRIC SoilGrids v2.0 queried for soil pH and nitrogen — returned null for "
        "most Indian locations at the requested coordinates due to API data gaps. "
        "Soil defaults (soil_data.py) rely on ICAR/FAO published ranges for Indian "
        "agro-ecological zones. See: Poggio et al. (2021), doi:10.5194/soil-7-217-2021."
    ),
}


def get_weather_profile(district: str = "Nashik / Maharashtra", season: str = "Rabi") -> Dict[str, float]:
    """
    Returns NASA POWER-calibrated seasonal weather defaults for the given district.
    Falls back to Nashik defaults if district is not in the database.
    """
    profile = REGION_WEATHER.get(district, REGION_WEATHER["Nashik / Maharashtra"])
    season_data = profile.get("season_defaults", {}).get(season)
    if season_data:
        return dict(season_data)
    return {
        "temperature_c": profile["temperature_c"],
        "humidity_percent": profile["humidity_percent"],
        "rainfall_mm": profile["rainfall_mm"],
    }


def list_regions() -> list:
    """Returns list of available region names."""
    return list(REGION_WEATHER.keys())
