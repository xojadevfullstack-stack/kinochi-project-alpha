from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address.
    If TRUST_PROXY is enabled, extract real client IP from rightmost hop of X-Forwarded-For
    to prevent client header spoofing. Otherwise fallback to get_remote_address (direct connection).
    """
    if getattr(settings, "TRUST_PROXY", False):
        xff = request.headers.get("x-forwarded-for")
        if xff:
            hops = [ip.strip() for ip in xff.split(",") if ip.strip()]
            hops_count = max(1, getattr(settings, "TRUSTED_PROXIES_COUNT", 1))
            if hops:
                idx = -min(hops_count, len(hops))
                return hops[idx]
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)
