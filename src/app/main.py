"""The ASGI entrypoint; pinned for Vercel via [tool.vercel] in pyproject."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.app.config import get_settings
from src.app.routers import refdata, subscriptions

app = FastAPI(
    title="Air Nomad Society",
    description="Personalized flight deals delivered to your inbox.",
)
app.include_router(subscriptions.router)
app.include_router(refdata.router)

# The frontend is a prebuilt static site calling this API from the browser;
# PUBLIC_BASE_URL is its origin, also allow Vercel preview deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().public_base_url],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
