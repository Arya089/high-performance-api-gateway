
# High Performance API Gateway

A lightweight API gateway built with FastAPI that routes requests to backend microservices.

## Run locally
pip install -r requirements.txt
uvicorn main:app --reload

## Endpoints
- `GET /health` — health check
- `/{service}/{path}` — proxies requests to registered backend services
