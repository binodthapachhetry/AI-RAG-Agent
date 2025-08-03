import asyncio


async def flaky_op(mode: str = "ok", sleep_ms: int = 0, fail_times: int = 0, key: str = "global"):
    """
    Demo external operation:
      - mode="ok": returns "ok" after optional sleep
      - mode="slow": sleeps then returns
      - mode="fail": raises
      - mode="fail_then_ok": fails 'fail_times' calls (per key) then succeeds
    """
    await asyncio.sleep(max(sleep_ms, 0) / 1000.0)
    if mode == "ok" or mode == "slow":
        return {"status": "ok"}
    if mode == "fail":
        raise RuntimeError("simulated failure")
    if mode == "fail_then_ok":
        # naive per-process counter (for tests)
        COUNTERS[key] = COUNTERS.get(key, 0) + 1
        if COUNTERS[key] <= fail_times:
            raise RuntimeError(f"fail {COUNTERS[key]}/{fail_times}")
        return {"status": "ok-after-fail"}
    raise ValueError("unknown mode")


COUNTERS: dict[str, int] = {}
