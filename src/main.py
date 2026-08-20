"""The ASGI entrypoint; Vercel auto-detects `app` here."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from src.routers import refdata, subscriptions

app = FastAPI(
    title="Air Nomad Society",
    description="Personalized flight deals delivered to your inbox.",
)
app.include_router(subscriptions.router)
app.include_router(refdata.router)


@app.middleware("http")
async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
