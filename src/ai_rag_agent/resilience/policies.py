# src/ai_rag_agent/resilience/policies.py
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import timedelta
from typing import Awaitable, TypeVar

import structlog
from aiobreaker import CircuitBreaker, CircuitBreakerError, CircuitBreakerState
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from ..ext.flaky_service import flaky_op

T = TypeVar("T")
log = structlog.get_logger()


# --- Timeouts (unchanged) ---
class TimeoutError(Exception):
    """Domain-specific timeout (distinct from asyncio.TimeoutError)."""


async def with_timeout(awaitable: Awaitable[T], timeout_s: float) -> T:
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_s)
    except asyncio.TimeoutError as e:
        raise TimeoutError(f"operation exceeded {timeout_s}s") from e


# --- Retries (unchanged) ---
def retryable():
    return retry(
        retry=retry_if_exception_type((TimeoutError, RuntimeError)),
        wait=wait_random_exponential(multiplier=0.1, max=2.0),
        stop=stop_after_attempt(3),
        reraise=True,
        before_sleep=before_sleep_log(log, log_level=logging.WARNING),
    )


breaker = CircuitBreaker(
    fail_max=2,
    timeout_duration=timedelta(seconds=2),
    name="flaky-op",
)


@breaker
async def flaky_through_breaker(*, mode: str, timeout_s: float):
    # Counted as a breaker failure if this raises
    return await with_timeout(flaky_op(mode=mode), timeout_s=timeout_s)


def breaker_is_open() -> bool:
    """Robust check across aiobreaker versions."""
    try:
        st = breaker.state  # enum CircuitBreakerState
        if isinstance(st, CircuitBreakerState):
            return st == CircuitBreakerState.OPEN
        # fallback if state is string-like
        return str(st).upper().endswith("OPEN")
    except Exception:
        return False


@retryable()
async def call_flaky_with_retry(*, mode: str, fail_times: int, key: str, timeout_s: float):
    # If flaky_op raises, tenacity sees it and retries before control returns
    return await with_timeout(
        flaky_op(mode=mode, fail_times=fail_times, key=key), timeout_s=timeout_s
    )


# --- Circuit breaker (FIX HERE) ---
FAIL_MAX = int(os.getenv("CB_FAIL_MAX", "2"))
RESET_TIMEOUT_S = float(os.getenv("CB_RESET_TIMEOUT_S", "2.0"))

# aiobreaker expects "timeout_duration", not "reset_timeout"
breaker = CircuitBreaker(
    fail_max=FAIL_MAX,
    timeout_duration=RESET_TIMEOUT_S,  # <-- changed kwarg
    name="flaky-op",
)


async def resilient_call(coro: Awaitable[T], timeout_s: float) -> T:
    async def _inner():
        return await with_timeout(coro, timeout_s=timeout_s)

    # If the circuit is open, aiobreaker raises CircuitBreakerError immediately.
    return await breaker.call(_inner)


# --- Bulkhead (unchanged) ---
DEFAULT_BULKHEAD = int(os.getenv("BULKHEAD_DEFAULT_MAX", "5"))
DEFAULT_SEMAPHORE = asyncio.Semaphore(DEFAULT_BULKHEAD)


async def with_bulkhead(coro: Awaitable[T], sem: asyncio.Semaphore) -> T:
    async with sem:
        return await coro


# --- Metrics (optional; unchanged except we avoid referencing breaker.state directly) ---
try:
    from ..observability.resilience_metrics import BREAKER_OPEN, ERRORS, LATENCY, TIMEOUTS
except Exception:  # pragma: no cover

    class _Noop:
        def labels(self, **kwargs):
            return self

        def inc(self, *a, **k):
            pass

        def observe(self, *a, **k):
            pass

        def set(self, *a, **k):
            pass

    TIMEOUTS = ERRORS = LATENCY = BREAKER_OPEN = _Noop()  # type: ignore


async def measured_call(target: str, coro: Awaitable[T], timeout_s: float) -> T:
    start = time.perf_counter()
    try:
        return await resilient_call(coro, timeout_s=timeout_s)
    except TimeoutError:
        TIMEOUTS.labels(target=target).inc()
        raise
    except Exception as e:
        ERRORS.labels(target=target, kind=type(e).__name__).inc()
        raise
    finally:
        LATENCY.labels(target=target).observe(time.perf_counter() - start)
        # Try to set breaker-open gauge defensively (works even if attributes differ).
        try:
            # Prefer dedicated API if present:
            is_open = getattr(breaker, "is_open", None)
            if callable(is_open):
                state_open = 1 if breaker.is_open() else 0
            else:
                # Fallback: inspect a "state" property if it exists
                st = getattr(breaker, "state", None)
                name = getattr(st, "name", None) or str(st or "").lower()
                state_open = 1 if (isinstance(name, str) and name.lower() == "open") else 0
        except Exception:
            state_open = 0
        BREAKER_OPEN.labels(target=target).set(state_open)


# Allow at most N concurrent calls to this dependency
FLAKY_SEMAPHORE = asyncio.Semaphore(5)

__all__ = [
    "TimeoutError",
    "with_timeout",
    "retryable",
    "breaker",
    "resilient_call",
    "with_bulkhead",
    "DEFAULT_SEMAPHORE",
    "measured_call",
    "CircuitBreakerError",
]
