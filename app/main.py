# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import math
import pytz
import traceback

from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

app = FastAPI(
    title="Where I Shine – Planet Lines API (V1)",
    version="1.0.4",
    description="FastAPI service for natal planet positions and (scaffolded) astrocartography outputs. Compatible with flatlib==0.2.3. Uses modern planets by default."
)

class BirthData(BaseModel):
    birthdate_iso: str = Field(..., example="1983-07-04")
    birthtime_24: str = Field(..., example="12:10")
    latitude: float = Field(..., example=48.3069)
    longitude: float = Field(..., example=14.2858)
    timezone_name: Optional[str] = Field(None, example="Europe/Vienna")
    birthplace_text: Optional[str] = Field(None, example="Linz, Austria")

PLANETS = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]

def format_utcoffset(offset_hours: float) -> str:
    sign = "+" if offset_hours >= 0 else "-"
    ah = abs(offset_hours)
    h = int(math.floor(ah))
    m = int(round((ah - h) * 60))
    return f"{sign}{h:02d}:{m:02d}"

def dec_to_dm_str(value: float, is_lat: bool) -> str:
    deg = int(abs(value))
    minutes = int(round((abs(value) - deg) * 60))
    if minutes == 60:
        deg += 1
        minutes = 0
    hemi = ('n' if value >= 0 else 's') if is_lat else ('e' if value >= 0 else 'w')
    return f"{deg}{hemi}{minutes:02d}"

def to_dt(data: BirthData) -> Datetime:
    tzname = data.timezone_name or "UTC"
    try:
        tz = pytz.timezone(tzname)
    except Exception:
        tz = pytz.UTC

    try:
        dt_naive = datetime.fromisoformat(f"{data.birthdate_iso}T{data.birthtime_24}:00")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid date/time: {e}")

    if dt_naive.tzinfo is None:
        dt_aware = tz.localize(dt_naive)
    else:
        dt_aware = dt_naive.astimezone(tz)

    offset = dt_aware.utcoffset() or timedelta(0)
    offset_hours = offset.total_seconds() / 3600.0
    offset_str = format_utcoffset(offset_hours)

    date_str = f"{dt_aware.year:04d}/{dt_aware.month:02d}/{dt_aware.day:02d}"
    time_str = f"{dt_aware.hour:02d}:{dt_aware.minute:02d}"

    return Datetime(date_str, time_str, offset_str)

@app.get("/health")
def health():
    return {"ok": True, "service": "planet-lines-api", "version": "1.0.4"}

def safe_house(chart: Chart, body_obj) -> Optional[int]:
    try:
        h = chart.houses.getObjectHouse(body_obj)  # type: ignore[attr-defined]
        return int(getattr(h, "num", h))
    except Exception:
        pass
    try:
        return int(chart.houseOf(body_obj))  # type: ignore[attr-defined]
    except Exception:
        return None

@app.post("/astro_eval")
def astro_eval(data: BirthData):
    try:
        fdt = to_dt(data)
        lat_str = dec_to_dm_str(data.latitude, is_lat=True)
        lon_str = dec_to_dm_str(data.longitude, is_lat=False)
        pos = GeoPos(lat_str, lon_str)

        chart = Chart(fdt, pos, IDs=PLANETS)

        planets = []
        for p in PLANETS:
            body = chart.get(p)
            planets.append({
                "planet": p,
                "lon_ecl": round(body.lon, 4),
                "lat_ecl": round(body.lat, 4),
                "sign": body.sign,
                "house": safe_house(chart, body),
                "ra": round(getattr(body, "ra", 0.0), 4),
                "decl": round(getattr(body, "decl", 0.0), 4)
            })

        sun = chart.get("Sun")
        moon = chart.get("Moon")
        summary = f"Sonne in {sun.sign}, Mond in {moon.sign}. Fokus auf {sun.sign} (Selbstausdruck) & {moon.sign} (Gefühle)."

        lines = [{"planet": p["planet"], "type": t, "polyline_geojson": None}
                 for p in planets for t in ["AC","DC","MC","IC"]]

        return {
            "astro_eval_summary": summary,
            "natal_planets": planets,
            "astro_lines": lines,
            "birthplace_text": data.birthplace_text,
            "latitude": data.latitude,
            "longitude": data.longitude
        }
    except Exception as e:
        tb = traceback.format_exc(limit=4)
        raise HTTPException(status_code=400, detail={"error": str(e), "trace": tb})

@app.post("/debug")
def debug(data: BirthData) -> Dict[str, Any]:
    fdt = to_dt(data)
    lat_str = dec_to_dm_str(data.latitude, is_lat=True)
    lon_str = dec_to_dm_str(data.longitude, is_lat=False)
    return {
        "date": f"{fdt.date}",
        "time": f"{fdt.time}",
        "utcoffset": f"{fdt.utcoffset}",
        "lat_str": lat_str,
        "lon_str": lon_str,
        "timezone_name": data.timezone_name or "UTC",
        "planets_used": PLANETS,
    }
