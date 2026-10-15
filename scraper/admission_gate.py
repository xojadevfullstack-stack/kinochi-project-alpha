"""
Scraper proxy for admission_gate.
Yagona admission_gate modulini scraper doirasida to'g'ridan-to'g'ri qayta ishlatish uchun import qiladi.
"""
import sys
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.admission_gate import (
    REQUIRED_FIELDS,
    normalize_title,
    check_url_reachable,
    pre_check,
    final_check,
    record_rejection,
    resolve_rejection,
    is_blacklisted_or_rejected,
    promote_to_published,
)

__all__ = [
    "REQUIRED_FIELDS",
    "normalize_title",
    "check_url_reachable",
    "pre_check",
    "final_check",
    "record_rejection",
    "resolve_rejection",
    "is_blacklisted_or_rejected",
    "promote_to_published",
]
