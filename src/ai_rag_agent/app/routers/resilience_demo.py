import structlog
from aiobreaker import CircuitBreakerError
from fastapi import APIRouter, HTTPException, status

from ...ext.flaky_service import flaky_op
from ...resilience.policies import (
    FLAKY_SEMAPHORE,
    TimeoutError,
    call_flaky_with_retry,
    flaky_through_breaker,
    resilient_call,
    with_bulkhead,
    with_timeout,
)

router = APIRouter(prefix="/v1", tags=["resilience-demo"])
log = structlog.get_logger()


@router.get("/demo-timeout")
async def demo_timeout(mode: str = "slow", sleep_ms: int = 1500, timeout_ms: int = 500):
    try:
        result = await with_timeout(
            flaky_op(mode=mode, sleep_ms=sleep_ms), timeout_s=timeout_ms / 1000
        )
        return {"ok": True, "result": result}
    except TimeoutError as e:
        log.warning("timeout", mode=mode, sleep_ms=sleep_ms, timeout_ms=timeout_ms)
        raise HTTPException(status_code=504, detail=str(e)) from e


@router.get("/demo-retry")
async def demo_retry(
    mode: str = "fail_then_ok", fail_times: int = 1, timeout_ms: int = 500, key: str = "retry-key"
):
    try:
        result = await call_flaky_with_retry(
            mode=mode, fail_times=fail_times, key=key, timeout_s=timeout_ms / 1000
        )
        return {"ok": True, "result": result}
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"upstream error: {e}") from e


@router.get("/demo-breaker")
async def demo_breaker(mode: str = "fail", timeout_ms: int = 300):
    try:
        result = await flaky_through_breaker(mode=mode, timeout_s=timeout_ms / 1000)
        return {"ok": True, "result": result}
    except CircuitBreakerError as e:
        # Immediate short-circuit
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="circuit open"
        ) from e
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e)) from e
    except RuntimeError as e:
        # Counted failure; may lead to open circuit on subsequent calls
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/demo-bulkhead")
async def demo_bulkhead(concurrency: int = 10, sleep_ms: int = 1000):
    """
    Spawns N concurrent calls to a slow op; semaphore limits in-flight to 5.
    Returns total time; with bulkhead, time ≈ ceil(N/5) * sleep_ms.
    """
    import asyncio
    import time

    start = time.perf_counter()

    async def one():
        return await with_bulkhead(flaky_op(mode="slow", sleep_ms=sleep_ms), FLAKY_SEMAPHORE)

    await asyncio.gather(*[one() for _ in range(concurrency)])
    elapsed_ms = (time.perf_counter() - start) * 1000
    return {"concurrency": concurrency, "elapsed_ms": round(elapsed_ms)}


@router.get("/demo-fallback")
async def demo_fallback(mode: str = "fail", timeout_ms: int = 200):
    try:
        result = await resilient_call(
            flaky_op(mode=mode, sleep_ms=500), timeout_s=timeout_ms / 1000
        )
        return {"ok": True, "result": result}
    except Exception:
        # Replace with cached value / static tip in a real app
        return {
            "ok": False,
            "fallback": "Service is busy—try a 1–2 minute walk as a low-effort action.",
        }
