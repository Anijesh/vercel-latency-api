# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import statistics
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

@app.options("/api/latency")
async def options_latency():
    return JSONResponse(content={}, headers=CORS_HEADERS)

# Telemetry data — embedded so no filesystem reads needed on Vercel
TELEMETRY = [
  {"region":"apac","service":"recommendations","latency_ms":170.13,"uptime_pct":99.288,"timestamp":20250301},
  {"region":"apac","service":"recommendations","latency_ms":148.4,"uptime_pct":99.233,"timestamp":20250302},
  {"region":"apac","service":"checkout","latency_ms":191.85,"uptime_pct":97.417,"timestamp":20250303},
  {"region":"apac","service":"catalog","latency_ms":170.62,"uptime_pct":97.518,"timestamp":20250304},
  {"region":"apac","service":"checkout","latency_ms":187.45,"uptime_pct":97.425,"timestamp":20250305},
  {"region":"apac","service":"catalog","latency_ms":194.27,"uptime_pct":98.958,"timestamp":20250306},
  {"region":"apac","service":"support","latency_ms":188.72,"uptime_pct":99.373,"timestamp":20250307},
  {"region":"apac","service":"payments","latency_ms":175.31,"uptime_pct":98.99,"timestamp":20250308},
  {"region":"apac","service":"recommendations","latency_ms":117.2,"uptime_pct":98.497,"timestamp":20250309},
  {"region":"apac","service":"checkout","latency_ms":161.61,"uptime_pct":97.669,"timestamp":20250310},
  {"region":"apac","service":"payments","latency_ms":199.66,"uptime_pct":99.328,"timestamp":20250311},
  {"region":"apac","service":"catalog","latency_ms":130.85,"uptime_pct":97.923,"timestamp":20250312},
  {"region":"emea","service":"analytics","latency_ms":177.06,"uptime_pct":97.388,"timestamp":20250301},
  {"region":"emea","service":"recommendations","latency_ms":232.68,"uptime_pct":99.044,"timestamp":20250302},
  {"region":"emea","service":"support","latency_ms":168.66,"uptime_pct":97.442,"timestamp":20250303},
  {"region":"emea","service":"catalog","latency_ms":168.15,"uptime_pct":97.773,"timestamp":20250304},
  {"region":"emea","service":"recommendations","latency_ms":196.01,"uptime_pct":97.492,"timestamp":20250305},
  {"region":"emea","service":"analytics","latency_ms":179.54,"uptime_pct":97.855,"timestamp":20250306},
  {"region":"emea","service":"catalog","latency_ms":150.92,"uptime_pct":98.16,"timestamp":20250307},
  {"region":"emea","service":"payments","latency_ms":147.34,"uptime_pct":97.786,"timestamp":20250308},
  {"region":"emea","service":"checkout","latency_ms":106.94,"uptime_pct":97.514,"timestamp":20250309},
  {"region":"emea","service":"recommendations","latency_ms":227.36,"uptime_pct":98.819,"timestamp":20250310},
  {"region":"emea","service":"catalog","latency_ms":179.75,"uptime_pct":98.262,"timestamp":20250311},
  {"region":"emea","service":"payments","latency_ms":198.05,"uptime_pct":97.165,"timestamp":20250312},
  {"region":"amer","service":"recommendations","latency_ms":214.58,"uptime_pct":97.57,"timestamp":20250301},
  {"region":"amer","service":"support","latency_ms":179.41,"uptime_pct":97.354,"timestamp":20250302},
  {"region":"amer","service":"analytics","latency_ms":190.54,"uptime_pct":98.673,"timestamp":20250303},
  {"region":"amer","service":"payments","latency_ms":202.39,"uptime_pct":97.812,"timestamp":20250304},
  {"region":"amer","service":"catalog","latency_ms":137.13,"uptime_pct":98.601,"timestamp":20250305},
  {"region":"amer","service":"catalog","latency_ms":157.49,"uptime_pct":98.026,"timestamp":20250306},
  {"region":"amer","service":"payments","latency_ms":216.17,"uptime_pct":99.31,"timestamp":20250307},
  {"region":"amer","service":"checkout","latency_ms":184.68,"uptime_pct":97.193,"timestamp":20250308},
  {"region":"amer","service":"catalog","latency_ms":189.24,"uptime_pct":99.367,"timestamp":20250309},
  {"region":"amer","service":"recommendations","latency_ms":142.7,"uptime_pct":99.467,"timestamp":20250310},
  {"region":"amer","service":"analytics","latency_ms":231.94,"uptime_pct":97.499,"timestamp":20250311},
  {"region":"amer","service":"recommendations","latency_ms":175.92,"uptime_pct":98.181,"timestamp":20250312},
]

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

def p95(values: List[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(0.95 * len(sorted_vals))
    # clamp to last element
    idx = min(idx, len(sorted_vals) - 1)
    return round(sorted_vals[idx], 3)

@app.post("/api/latency")
def latency_metrics(req: LatencyRequest):
    result = {}
    for region in req.regions:
        records = [r for r in TELEMETRY if r["region"] == region]
        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": round(statistics.mean(latencies), 3),
            "p95_latency": p95(latencies),
            "avg_uptime": round(statistics.mean(uptimes), 3),
            "breaches": sum(1 for l in latencies if l > req.threshold_ms),
        }

    return result