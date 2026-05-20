from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import json
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("q-vercel-latency.json", "r") as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.options("/api/latency")
async def options_latency():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/latency")
def get_latency_metrics(body: RequestBody):

    result = {}

    for region in body.regions:

        region_data = [
            item for item in telemetry
            if item["region"] == region
        ]

        if not region_data:
            continue

        latencies = [item["latency_ms"] for item in region_data]
        uptimes = [item["uptime_pct"] for item in region_data]

        avg_latency = round(sum(latencies) / len(latencies), 2)
        p95_latency = round(float(np.percentile(latencies, 95)), 2)
        avg_uptime = round(sum(uptimes) / len(uptimes), 3)
        breaches = len([x for x in latencies if x > body.threshold_ms])

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return JSONResponse(content=result, headers={"Access-Control-Allow-Origin": "*"})