# ai-generated: 95% - ChatGPT Codex drafted the bounded-cardinality Prometheus middleware for Lab 3
from time import perf_counter
from typing import Any

from prometheus_client import Histogram, disable_created_metrics


disable_created_metrics()

# This ladder was designed around the measured p99 of 0.1742 seconds.  Ten
# millisecond buckets cover more than the required +/-10% band around p99.
REQUEST_DURATION = Histogram(
    "http_server_request_duration_seconds",
    "Duration of HTTP server requests in seconds.",
    ("http_request_method", "http_route", "http_response_status_code"),
    buckets=(
        0.005,
        0.01,
        0.02,
        0.03,
        0.04,
        0.05,
        0.075,
        0.1,
        0.125,
        0.14,
        0.15,
        0.16,
        0.17,
        0.18,
        0.19,
        0.2,
        0.225,
        0.25,
        0.3,
        0.4,
        0.5,
        0.75,
        1.0,
        2.0,
        5.0,
    ),
)


class RequestMetricsMiddleware:
    """Observe every completed HTTP request once, using route templates as labels."""

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or scope.get("path") == "/metrics":
            await self.app(scope, receive, send)
            return

        started = perf_counter()
        status_code = 500

        async def send_with_status(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        finally:
            route = scope.get("route")
            route_template = getattr(route, "path", None) or "unmatched"
            REQUEST_DURATION.labels(
                http_request_method=str(scope.get("method", "UNKNOWN")),
                http_route=route_template,
                http_response_status_code=str(status_code),
            ).observe(perf_counter() - started)
