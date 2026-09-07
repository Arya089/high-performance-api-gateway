from fastapi import FastAPI, Request
import httpx

app = FastAPI(title="High Performance API Gateway")

# Example backend services this gateway routes to
SERVICES = {
    "users": "http://localhost:8001",
    "orders": "http://localhost:8002",
}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        return {"error": "Unknown service"}, 404

    url = f"{SERVICES[service]}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body(),
        )
    return response.json()
