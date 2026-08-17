"""
Middleware de seguranca do KAIRUS.
Rate limiting e sanitizacao de input.
"""

import time
import re
from collections import defaultdict
from fastapi import Request, HTTPException


# =========================
# RATE LIMITER SIMPLES
# =========================

class RateLimiter:
    """
    Rate limiter em memoria.
    Para producao, usar Redis ou similar.
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        self.requests[key] = [
            t for t in self.requests[key] if t > window_start
        ]

        if len(self.requests[key]) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        recent = [t for t in self.requests[key] if t > window_start]
        return max(0, self.max_requests - len(recent))


rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


# =========================
# SANITIZACAO DE INPUT
# =========================

def sanitize_input(text: str) -> str:
    """
    Sanitiza o input do usuario.
    Remove caracteres perigosos e limita tamanho.
    """
    if not text:
        return ""

    text = text[:4000]

    text = text.replace("\x00", "")

    text = re.sub(r'<[^>]+>', '', text)

    text = re.sub(r'(?i)javascript:', '', text)
    text = re.sub(r'(?i)on\w+\s*=', '', text)

    return text.strip()


# =========================
# MIDDLEWARE FASTAPI
# =========================

async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting."""
    path = request.url.path

    if path in ("/api/health", "/api/status", "/"):
        return await call_next(request)

    if not path.startswith("/api/"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Muitas requisicoes. Aguarde um momento antes de tentar novamente."
        )

    response = await call_next(request)

    remaining = rate_limiter.get_remaining(client_ip)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)

    return response