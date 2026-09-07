import os
import time
import logging
from collections import defaultdict

from fastapi import FastAPI, Request, HTTPException, Header
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

app = FastAPI(title="High Performance API Gateway")

# Services now configurable via environment variables
SERVICES = {
    "users": os.getenv("USERS_SERVICE_URL", "http://localhost:8001"),
    "orders": os.getenv("ORDERS_SERVICE_URL", "http://localhost:8002"),
}

API_KEY = os.getenv("GATEWAY_API_KEY", "dev-secret-key")

# --- simple in-memory rate limiter ---
RATE_LIMIT = 5          # max requests
RATE_WINDOW = 10        # per 10 seconds
request_log = defaultdict(list)

# --- simple in-memory cache for GET requests ---
CACHE_TTL = 5  # seconds
cache = {}


def is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    timestamps = [t for t in request_log[client_ip] if now - t < RATE_WINDOW]
    request_log[client_ip] = timestamps
    if len(timestamps) >= RATE_LIMIT:
        return True
    request_log[client_ip].append(now)
    return False


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(
    service: str,
    path: str,
    request: Request,
    x_api_key: str = Header(default=None),
):
    start_time = time.time()
    client_ip = request.client.host

    # 1. Auth check
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # 2. Rate limiting
    if is_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests")

    # 3. Validate service
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Unknown service")

    # 4. Serve from cache for GET requests
    cache_key = f"{service}/{path}"
    if request.method == "GET" and cache_key in cache:
        cached_response, cached_time = cache[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            logger.info(f"Cache hit for {cache_key}")
            return cached_response

    # 5. Forward request with retry + timeout
    url = f"{SERVICES[service]}/{path}"
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.request(
                    method=request.method,
                    url=url,
                    headers=dict(request.headers),
                    content=await request.body(),
                )
            data = response.json()

            if request.method == "GET":
                cache[cache_key] = (data, time.time())

            duration = round(time.time() - start_time, 3)
            logger.info(f"{request.method} {url} -> {response.status_code} in {duration}s")
            return data

        except httpx.RequestError as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")

    raise HTTPException(status_code=502, detail=f"Upstream service unavailable: {last_error}")
